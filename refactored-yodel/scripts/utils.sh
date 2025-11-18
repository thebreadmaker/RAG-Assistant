#!/bin/bash

################################################################################
# Shared Utilities - Color functions, logging, health checks
################################################################################

# Color Definitions
readonly COLOR_RESET='\033[0m'
readonly COLOR_RED='\033[0;31m'
readonly COLOR_GREEN='\033[0;32m'
readonly COLOR_YELLOW='\033[1;33m'
readonly COLOR_BLUE='\033[0;34m'
readonly COLOR_CYAN='\033[0;36m'
readonly COLOR_BOLD='\033[1m'
readonly COLOR_DIM='\033[2m'

# Symbols
readonly SYMBOL_CHECK='✅'
readonly SYMBOL_CROSS='❌'
readonly SYMBOL_WARN='⚠️ '
readonly SYMBOL_INFO='ℹ️ '
readonly SYMBOL_ARROW='→'
readonly SYMBOL_CLOCK='⏱️ '

# Configuration
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
readonly LOGS_DIR="${PROJECT_ROOT}/logs"
readonly BACKEND_DIR="${PROJECT_ROOT}/backend"
readonly DOCKER_COMPOSE="${PROJECT_ROOT}/docker-compose.yml"

# Service ports
readonly REDIS_PORT=6379
readonly OLLAMA_PORT=11434
readonly BACKEND_PORT=8000
readonly BACKEND_HEALTH_ENDPOINT="http://localhost:${BACKEND_PORT}/health"

# Timeouts (in seconds)
readonly SERVICE_STARTUP_TIMEOUT=60
readonly HEALTH_CHECK_INTERVAL=2
readonly HEALTH_CHECK_RETRIES=30

# Log files
readonly BOOT_LOG="${LOGS_DIR}/boot.log"
readonly MONITOR_LOG="${LOGS_DIR}/monitor.log"

################################################################################
# Logging Functions
################################################################################

# Initialize logs directory
init_logs() {
    mkdir -p "${LOGS_DIR}" 2>/dev/null || true
}

# Log function with timestamp
log_info() {
    local message="$1"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${COLOR_BLUE}[${timestamp}]${COLOR_RESET} ${COLOR_GREEN}INFO${COLOR_RESET} - ${message}"
}

log_error() {
    local message="$1"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${COLOR_BLUE}[${timestamp}]${COLOR_RESET} ${COLOR_RED}ERROR${COLOR_RESET} - ${message}"
}

log_warn() {
    local message="$1"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${COLOR_BLUE}[${timestamp}]${COLOR_RESET} ${COLOR_YELLOW}WARN${COLOR_RESET} - ${message}"
}

log_success() {
    local message="$1"
    echo -e "${COLOR_GREEN}${SYMBOL_CHECK} ${message}${COLOR_RESET}"
}

log_failure() {
    local message="$1"
    echo -e "${COLOR_RED}${SYMBOL_CROSS} ${message}${COLOR_RESET}"
}

log_section() {
    local title="$1"
    echo ""
    echo -e "${COLOR_BOLD}${COLOR_CYAN}═══════════════════════════════════════════════════════════${COLOR_RESET}"
    echo -e "${COLOR_BOLD}${COLOR_CYAN}  ${title}${COLOR_RESET}"
    echo -e "${COLOR_BOLD}${COLOR_CYAN}═══════════════════════════════════════════════════════════${COLOR_RESET}"
}

log_file() {
    local message="$1"
    local logfile="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[${timestamp}] ${message}" >> "${logfile}"
}

################################################################################
# Color Output Functions
################################################################################

print_header() {
    local text="$1"
    echo -e "\n${COLOR_BOLD}${COLOR_CYAN}┌─ ${text}${COLOR_RESET}"
}

print_subheader() {
    local text="$1"
    echo -e "${COLOR_CYAN}│ ${text}${COLOR_RESET}"
}

print_status_running() {
    local service="$1"
    echo -e "${COLOR_GREEN}${SYMBOL_CHECK} ${service}:${COLOR_RESET}    ${COLOR_GREEN}Running${COLOR_RESET}"
}

print_status_stopped() {
    local service="$1"
    echo -e "${COLOR_RED}${SYMBOL_CROSS} ${service}:${COLOR_RESET}    ${COLOR_RED}Stopped${COLOR_RESET}"
}

print_status_waiting() {
    local service="$1"
    echo -e "${COLOR_YELLOW}⧗ ${service}:${COLOR_RESET}    ${COLOR_YELLOW}Starting...${COLOR_RESET}"
}

################################################################################
# Health Check Functions
################################################################################

# Check if port is open (service running)
is_port_open() {
    local port=$1
    timeout 2 bash -c "</dev/tcp/localhost/${port}" 2>/dev/null
    return $?
}

# Check if Redis is healthy
check_redis_health() {
    docker exec safina-redis redis-cli ping &>/dev/null
    return $?
}

# Check if Ollama is healthy
check_ollama_health() {
    curl -s http://localhost:${OLLAMA_PORT}/api/tags > /dev/null
    return $?
}

# Check if Backend is healthy
check_backend_health() {
    curl -s "${BACKEND_HEALTH_ENDPOINT}" > /dev/null 2>&1
    return $?
}

# Wait for service with retries
wait_for_service() {
    local service_name=$1
    local check_function=$2
    local max_retries=${3:-$HEALTH_CHECK_RETRIES}
    local retry_count=0

    print_status_waiting "${service_name}"

    while [ $retry_count -lt $max_retries ]; do
        if $check_function; then
            print_status_running "${service_name}"
            return 0
        fi
        retry_count=$((retry_count + 1))
        sleep $HEALTH_CHECK_INTERVAL
        printf "."
    done

    echo ""
    print_status_stopped "${service_name}"
    return 1
}

################################################################################
# Docker Functions
################################################################################

# Check if Docker is running
is_docker_running() {
    docker ps > /dev/null 2>&1
    return $?
}

# Get container status
get_container_status() {
    local container_name=$1
    docker ps -a --filter "name=${container_name}" --format '{{.Status}}'
}

# Check if container exists
container_exists() {
    local container_name=$1
    docker ps -a --filter "name=${container_name}" --format '{{.Names}}' | grep -q "^${container_name}$"
    return $?
}

# Get container ID
get_container_id() {
    local container_name=$1
    docker ps -a --filter "name=${container_name}" --format '{{.ID}}'
}

################################################################################
# Process Management Functions
################################################################################

# Get PID of process
get_process_pid() {
    local process_pattern=$1
    pgrep -f "$process_pattern" | head -1
}

# Check if process is running
is_process_running() {
    local pid=$1
    [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null
    return $?
}

# Kill process gracefully
kill_process() {
    local pid=$1
    if is_process_running "$pid"; then
        kill -TERM "$pid" 2>/dev/null
        sleep 2
        if is_process_running "$pid"; then
            kill -KILL "$pid" 2>/dev/null
        fi
    fi
}

################################################################################
# Confirmation Functions
################################################################################

# Ask for confirmation
confirm() {
    local prompt="$1"
    local response
    read -p "$(echo -e ${COLOR_YELLOW}${prompt}${COLOR_RESET}) (y/n): " -r response
    [[ "$response" =~ ^[Yy]$ ]]
    return $?
}

################################################################################
# Cleanup Functions
################################################################################

# Cleanup old processes and containers
cleanup_stale() {
    log_info "Cleaning up stale processes..."
    
    # Kill old Python processes
    pkill -f "uvicorn.*main:app" 2>/dev/null || true
    pkill -f "python.*setup_rag" 2>/dev/null || true
    
    # Remove old container PIDs
    rm -f "${PROJECT_ROOT}/.safina_backend.pid" 2>/dev/null || true
    rm -f "${PROJECT_ROOT}/.safina_redis.pid" 2>/dev/null || true
    rm -f "${PROJECT_ROOT}/.safina_ollama.pid" 2>/dev/null || true
    
    log_success "Cleanup complete"
}

# Full cleanup on shutdown
cleanup_all() {
    log_info "Performing full cleanup..."
    
    # Kill backend
    if [ -f "${PROJECT_ROOT}/.safina_backend.pid" ]; then
        local backend_pid=$(cat "${PROJECT_ROOT}/.safina_backend.pid")
        kill_process "$backend_pid"
        rm -f "${PROJECT_ROOT}/.safina_backend.pid"
    fi
    
    # Stop containers
    docker-compose -f "${DOCKER_COMPOSE}" down 2>/dev/null || true
    
    # Remove PID files
    rm -f "${PROJECT_ROOT}"/.safina_*.pid 2>/dev/null || true
    
    log_success "Cleanup complete"
}

################################################################################
# Display Functions
################################################################################

# Display spinner
spinner() {
    local pid=$1
    local spinner=( '⠋' '⠙' '⠹' '⠸' '⠼' '⠴' '⠦' '⠧' '⠇' '⠏' )
    local i=0
    
    while kill -0 "$pid" 2>/dev/null; do
        echo -ne "\r${spinner[$((i % ${#spinner[@]}))]} "
        ((i++))
        sleep 0.1
    done
}

# Display progress bar
progress_bar() {
    local current=$1
    local total=$2
    local width=50
    local percentage=$((current * 100 / total))
    local filled=$((width * current / total))
    
    printf "["
    printf "%${filled}s" | tr ' ' '='
    printf "%$((width - filled))s" | tr ' ' '-'
    printf "] %d%%\r" "$percentage"
}

################################################################################
# Summary Display
################################################################################

display_service_summary() {
    log_section "SERVICE STATUS SUMMARY"
    
    echo ""
    print_header "Services"
    
    if container_exists "safina-redis"; then
        if [ "$(docker inspect -f '{{.State.Running}}' safina-redis 2>/dev/null)" = "true" ]; then
            print_status_running "Redis"
        else
            print_status_stopped "Redis"
        fi
    else
        print_status_stopped "Redis"
    fi
    
    if container_exists "safina-ollama"; then
        if [ "$(docker inspect -f '{{.State.Running}}' safina-ollama 2>/dev/null)" = "true" ]; then
            print_status_running "Ollama"
        else
            print_status_stopped "Ollama"
        fi
    else
        print_status_stopped "Ollama"
    fi
    
    local backend_pid=$(get_process_pid "uvicorn.*main:app")
    if is_process_running "$backend_pid"; then
        print_status_running "Backend"
    else
        print_status_stopped "Backend"
    fi
    
    echo ""
}

display_endpoints() {
    print_header "Endpoints"
    echo -e "${COLOR_CYAN}│ Backend API:     ${COLOR_BOLD}http://localhost:${BACKEND_PORT}${COLOR_RESET}"
    echo -e "${COLOR_CYAN}│ API Docs:        ${COLOR_BOLD}http://localhost:${BACKEND_PORT}/docs${COLOR_RESET}"
    echo -e "${COLOR_CYAN}│ Redis:           ${COLOR_BOLD}localhost:${REDIS_PORT}${COLOR_RESET}"
    echo -e "${COLOR_CYAN}│ Ollama:          ${COLOR_BOLD}localhost:${OLLAMA_PORT}${COLOR_RESET}"
    echo ""
}

display_logs_info() {
    print_header "Logs"
    echo -e "${COLOR_CYAN}│ Boot log:        ${COLOR_BOLD}${BOOT_LOG}${COLOR_RESET}"
    echo -e "${COLOR_CYAN}│ Monitor log:     ${COLOR_BOLD}${MONITOR_LOG}${COLOR_RESET}"
    echo -e "${COLOR_CYAN}│ Backend logs:    ${COLOR_BOLD}${LOGS_DIR}/all_*.log${COLOR_RESET}"
    echo ""
}

################################################################################
# Export for use in other scripts
################################################################################

export COLOR_RESET COLOR_RED COLOR_GREEN COLOR_YELLOW COLOR_BLUE COLOR_CYAN COLOR_BOLD COLOR_DIM
export SYMBOL_CHECK SYMBOL_CROSS SYMBOL_WARN SYMBOL_INFO SYMBOL_ARROW SYMBOL_CLOCK
export PROJECT_ROOT LOGS_DIR BACKEND_DIR DOCKER_COMPOSE
export REDIS_PORT OLLAMA_PORT BACKEND_PORT BACKEND_HEALTH_ENDPOINT
export SERVICE_STARTUP_TIMEOUT HEALTH_CHECK_INTERVAL HEALTH_CHECK_RETRIES
export BOOT_LOG MONITOR_LOG
