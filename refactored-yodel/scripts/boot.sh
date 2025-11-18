#!/bin/bash

################################################################################
# Refactored YodeL Assistant - Boot Script
# Automated system startup with service orchestration and document ingestion
################################################################################

set -o pipefail

# Source utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/utils.sh"

# Global state
RUNNING=true
SERVICES_PIDS=()

################################################################################
# Signal Handlers
################################################################################

handle_interrupt() {
    log_warn "Received interrupt signal"
    shutdown_services
    exit 0
}

handle_error() {
    local line_number=$1
    log_error "Error occurred at line ${line_number}"
    shutdown_services
    exit 1
}

trap handle_interrupt SIGINT SIGTERM
trap 'handle_error ${LINENO}' ERR

################################################################################
# Prerequisites Check
################################################################################

check_prerequisites() {
    log_section "CHECKING PREREQUISITES"
    
    local all_ok=true
    
    # Check Docker
    print_header "Docker"
    if command -v docker &> /dev/null; then
        if is_docker_running; then
            log_success "Docker is running"
        else
            log_failure "Docker is not running"
            all_ok=false
        fi
    else
        log_failure "Docker is not installed"
        all_ok=false
    fi
    
    # Check Docker Compose
    print_header "Docker Compose"
    if command -v docker-compose &> /dev/null; then
        log_success "Docker Compose is installed"
    else
        log_failure "Docker Compose is not installed"
        all_ok=false
    fi
    
    # Check Python
    print_header "Python"
    if command -v python3 &> /dev/null; then
        local py_version=$(python3 --version | awk '{print $2}')
        log_success "Python ${py_version} is installed"
    else
        log_failure "Python 3 is not installed"
        all_ok=false
    fi
    
    # Check required files
    print_header "Project Files"
    if [ -f "${DOCKER_COMPOSE}" ]; then
        log_success "docker-compose.yml found"
    else
        log_failure "docker-compose.yml not found"
        all_ok=false
    fi
    
    if [ -f "${BACKEND_DIR}/requirements.txt" ]; then
        log_success "requirements.txt found"
    else
        log_failure "requirements.txt not found"
        all_ok=false
    fi
    
    if [ -f "${BACKEND_DIR}/api/main.py" ]; then
        log_success "main.py found"
    else
        log_failure "main.py not found"
        all_ok=false
    fi
    
    echo ""
    if [ "$all_ok" = true ]; then
        log_success "All prerequisites met"
        return 0
    else
        log_failure "Some prerequisites are missing"
        return 1
    fi
}

################################################################################
# Startup Functions
################################################################################

cleanup_old_processes() {
    log_section "CLEANUP OLD PROCESSES"
    cleanup_stale
    log_file "Cleanup completed" "${BOOT_LOG}"
}

start_docker_services() {
    log_section "STARTING DOCKER SERVICES"
    
    print_header "Docker Compose"
    log_info "Starting services from docker-compose.yml..."
    
    cd "${PROJECT_ROOT}" || exit 1
    docker-compose up -d >> "${BOOT_LOG}" 2>&1
    
    log_success "Docker Compose started"
    log_file "Docker Compose started" "${BOOT_LOG}"
    
    # Wait for Redis
    print_header "Redis Service"
    if wait_for_service "Redis" "check_redis_health"; then
        log_file "Redis healthy" "${BOOT_LOG}"
    else
        log_failure "Redis failed to start"
        log_file "Redis failed to start" "${BOOT_LOG}"
        return 1
    fi
    
    # Wait for Ollama
    print_header "Ollama Service"
    if wait_for_service "Ollama" "check_ollama_health"; then
        log_file "Ollama healthy" "${BOOT_LOG}"
    else
        log_failure "Ollama failed to start"
        log_file "Ollama failed to start" "${BOOT_LOG}"
        return 1
    fi
    
    echo ""
    return 0
}

pull_models() {
    log_section "PULLING LLM MODELS"
    
    print_header "Model Check"
    
    local model_name="llama3.2:3b"
    log_info "Checking for model: ${model_name}"
    
    # Check if model exists
    if docker exec refactored-yodel-ollama ollama list 2>/dev/null | grep -q "llama3.2:3b"; then
        log_success "Model already exists"
        log_file "Model llama3.2:3b already exists" "${BOOT_LOG}"
    else
        log_info "Pulling model (this may take several minutes)..."
        docker exec refactored-yodel-ollama ollama pull llama3.2:3b >> "${BOOT_LOG}" 2>&1 &
        local pull_pid=$!
        
        # Show progress
        while kill -0 $pull_pid 2>/dev/null; do
            printf "."
            sleep 2
        done
        
        if docker exec refactored-yodel-ollama ollama list 2>/dev/null | grep -q "llama3.2:3b"; then
            echo ""
            log_success "Model pulled successfully"
            log_file "Model llama3.2:3b pulled successfully" "${BOOT_LOG}"
        else
            echo ""
            log_failure "Model pull failed"
            log_file "Model pull failed" "${BOOT_LOG}"
            return 1
        fi
    fi
    
    echo ""
    return 0
}

start_backend() {
    log_section "STARTING BACKEND SERVICES"
    
    print_header "Backend Setup"
    cd "${BACKEND_DIR}" || exit 1
    
    log_info "Initializing RAG system..."
    if python3 setup_rag.py >> "${BOOT_LOG}" 2>&1; then
        log_success "RAG system initialized"
        log_file "RAG system initialized successfully" "${BOOT_LOG}"
    else
        log_failure "RAG system initialization failed"
        log_file "RAG system initialization failed" "${BOOT_LOG}"
        return 1
    fi
    
    print_header "Starting FastAPI Server"
    log_info "Starting backend server on port ${BACKEND_PORT}..."

    # Backend log file
    local backend_log="${LOGS_DIR}/backend_$(date '+%Y%m%d_%H%M%S').log"

    # Start backend in background, redirect output to backend log
    nohup python3 -m uvicorn api.main:app --host 0.0.0.0 --port ${BACKEND_PORT} > "$backend_log" 2>&1 &
    local backend_pid=$!
    echo $backend_pid > "${PROJECT_ROOT}/.refactored_yodel_backend.pid"
    SERVICES_PIDS+=($backend_pid)

    log_file "Backend started with PID ${backend_pid}" "${BOOT_LOG}"
    log_file "Backend log: $backend_log" "${BOOT_LOG}"

    # Wait for backend health
    if wait_for_service "Backend" "check_backend_health"; then
        log_file "Backend healthy" "${BOOT_LOG}"
    else
        log_failure "Backend failed to start"
        log_file "Backend failed to start" "${BOOT_LOG}"
        # Show last 10 lines of backend log for error context
        log_file "--- Backend error log ---" "${BOOT_LOG}"
        tail -n 10 "$backend_log" | while read -r line; do log_file "$line" "${BOOT_LOG}"; done
        log_file "--- End backend error log ---" "${BOOT_LOG}"
        return 1
    fi

    echo ""
    return 0
}

ingest_documents() {
    log_section "INGESTING DOCUMENTS"
    
    print_header "Document Ingestion"
    log_info "Ingesting documents into vector database..."
    
    # Call ingest endpoint
    local response=$(curl -s -X POST "${BACKEND_HEALTH_ENDPOINT%/health}/ingest" \
        -H "Content-Type: application/json" 2>/dev/null)
    
    if echo "$response" | grep -q '"status":"success"'; then
        local chunk_count=$(echo "$response" | grep -oP '(?<="Total chunks: )\d+')
        log_success "Documents ingested (${chunk_count} chunks)"
        log_file "Documents ingested: ${chunk_count} chunks" "${BOOT_LOG}"
    else
        log_warn "Document ingestion completed (check logs)"
        log_file "Document ingestion completed" "${BOOT_LOG}"
    fi
    
    echo ""
    return 0
}

display_startup_complete() {
    log_section "STARTUP COMPLETE"
    
    echo ""
    display_service_summary
    display_endpoints
    display_logs_info
    
    echo -e "${COLOR_BOLD}${COLOR_GREEN}System is ready!${COLOR_RESET}"
    echo ""
}

################################################################################
# Command Input Handler
################################################################################

listen_for_commands() {
    log_info "Listening for commands..."
    echo -e "${COLOR_YELLOW}Enter command (--stop, --restart, or press ENTER to keep running):${COLOR_RESET}"
    echo ""
    
    while [ "$RUNNING" = true ]; do
        echo -n ">>> "
        read -r command
        
        case "$command" in
            --stop)
                if confirm "Stop all services?"; then
                    log_info "Shutting down services..."
                    shutdown_services
                    RUNNING=false
                    log_success "Services stopped"
                    exit 0
                else
                    echo "Cancelled."
                fi
                ;;
            --restart)
                if confirm "Restart all services?"; then
                    log_info "Restarting services..."
                    shutdown_services
                    sleep 2
                    log_section "RESTARTING SYSTEM"
                    main
                else
                    echo "Cancelled."
                fi
                ;;
            "")
                # Keep running
                ;;
            *)
                log_warn "Unknown command: ${command}"
                ;;
        esac
    done
}

################################################################################
# Shutdown
################################################################################

shutdown_services() {
    log_info "Shutting down services..."
    
    # Kill backend processes
    if [ -f "${PROJECT_ROOT}/.refactored_yodel_backend.pid" ]; then
        local backend_pid=$(cat "${PROJECT_ROOT}/.refactored_yodel_backend.pid")
        if is_process_running "$backend_pid"; then
            log_info "Stopping backend (PID: ${backend_pid})..."
            kill_process "$backend_pid"
        fi
        rm -f "${PROJECT_ROOT}/.refactored_yodel_backend.pid"
    fi
    
    # Stop Docker containers
    log_info "Stopping Docker containers..."
    docker-compose -f "${DOCKER_COMPOSE}" down >> "${BOOT_LOG}" 2>&1 || true
    
    # Clean resources
    rm -f "${PROJECT_ROOT}"/.refactored_yodel_*.pid 2>/dev/null || true
    
    log_file "Services shut down" "${BOOT_LOG}"
    log_success "Services stopped"
}

################################################################################
# Main
################################################################################

main() {
    init_logs
    
    log_file "================================" "${BOOT_LOG}"
    log_file "Boot script started at $(date)" "${BOOT_LOG}"
    log_file "================================" "${BOOT_LOG}"
    
    # Run startup sequence
    check_prerequisites || exit 1
    cleanup_old_processes
    start_docker_services || exit 1
    pull_models || exit 1
    start_backend || exit 1
    ingest_documents
    display_startup_complete
    
    # Listen for commands
    listen_for_commands
}

# Run main if script is executed directly
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    main "$@"
fi
