#!/bin/bash

################################################################################
# Safina RAG Assistant - Monitor Script
# Real-time system dashboard with logs, metrics, and service health
################################################################################

set -o pipefail

# Source utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/utils.sh"

# Global state
RUNNING=true
SESSION_NAME="safina-monitor"
MONITORING_PID=$$
START_TIME=$(date +%s)
FILTER_TERM=""

################################################################################
# Signal Handlers
################################################################################

handle_interrupt() {
    log_warn "Monitoring interrupted"
    cleanup_monitor
    exit 0
}

handle_error() {
    local line_number=$1
    log_error "Error occurred at line ${line_number}"
    cleanup_monitor
    exit 1
}

trap handle_interrupt SIGINT SIGTERM
trap 'handle_error ${LINENO}' ERR

################################################################################
# Monitoring Setup
################################################################################

setup_monitoring() {
    init_logs
    
    log_file "================================" "${MONITOR_LOG}"
    log_file "Monitor script started at $(date)" "${MONITOR_LOG}"
    log_file "================================" "${MONITOR_LOG}"
    
    # Create tmux session for monitoring
    if tmux has-session -t "${SESSION_NAME}" 2>/dev/null; then
        tmux kill-session -t "${SESSION_NAME}" 2>/dev/null || true
    fi
    
    tmux new-session -d -s "${SESSION_NAME}" -x 200 -y 50 2>/dev/null || {
        log_error "Failed to create tmux session"
        return 1
    }
    
    log_file "Tmux session created" "${MONITOR_LOG}"
    return 0
}

cleanup_monitor() {
    log_info "Cleaning up monitoring resources..."
    tmux kill-session -t "${SESSION_NAME}" 2>/dev/null || true
    log_file "Monitoring stopped at $(date)" "${MONITOR_LOG}"
}

################################################################################
# Service Status Functions
################################################################################

get_redis_status() {
    if container_exists "safina-redis"; then
        if [ "$(docker inspect -f '{{.State.Running}}' safina-redis 2>/dev/null)" = "true" ]; then
            if check_redis_health; then
                echo "✅ Running (6379)"
                return 0
            else
                echo "🔴 Unhealthy"
                return 1
            fi
        else
            echo "🔴 Stopped"
            return 1
        fi
    else
        echo "⊘ Not found"
        return 1
    fi
}

get_ollama_status() {
    if container_exists "safina-ollama"; then
        if [ "$(docker inspect -f '{{.State.Running}}' safina-ollama 2>/dev/null)" = "true" ]; then
            if check_ollama_health; then
                echo "✅ Running (11434)"
                return 0
            else
                echo "🔴 Unhealthy"
                return 1
            fi
        else
            echo "🔴 Stopped"
            return 1
        fi
    else
        echo "⊘ Not found"
        return 1
    fi
}

get_backend_status() {
    if [ -f "${PROJECT_ROOT}/.safina_backend.pid" ]; then
        local backend_pid=$(cat "${PROJECT_ROOT}/.safina_backend.pid")
        if is_process_running "$backend_pid"; then
            if check_backend_health; then
                echo "✅ Running (8000)"
                return 0
            else
                echo "🟡 Starting"
                return 1
            fi
        else
            echo "🔴 Stopped"
            return 1
        fi
    else
        echo "⊘ Not found"
        return 1
    fi
}

################################################################################
# System Metrics Functions
################################################################################

get_cpu_usage() {
    top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1}'
}

get_memory_info() {
    free -h | awk 'NR==2{printf "%s / %s (%.1f%%)", $3, $2, $3*100/$2}'
}

get_disk_info() {
    df -h "${PROJECT_ROOT}" | awk 'NR==2{printf "%s / %s (%.0f%%)", $3, $2, $5}'
}

get_uptime() {
    local current_time=$(date +%s)
    local elapsed=$((current_time - START_TIME))
    local hours=$((elapsed / 3600))
    local minutes=$(((elapsed % 3600) / 60))
    local seconds=$((elapsed % 60))
    printf "%dh %dm %ds" $hours $minutes $seconds
}

get_error_count() {
    if [ -f "${LOGS_DIR}/errors_$(date +%Y%m%d)_*.log" ]; then
        wc -l < "${LOGS_DIR}/errors_$(date +%Y%m%d)_"*.log 2>/dev/null | awk '{s+=$1} END {print s}'
    else
        echo "0"
    fi
}

################################################################################
# Dashboard Display
################################################################################

display_dashboard() {
    while [ "$RUNNING" = true ]; do
        clear
        
        # Header
        echo -e "${COLOR_BOLD}${COLOR_CYAN}"
        echo "╔════════════════════════════════════════════════════════════════════════════════════════════════════════════╗"
        echo "║                     SAFINA RAG ASSISTANT - MONITORING DASHBOARD                                           ║"
        echo "╚════════════════════════════════════════════════════════════════════════════════════════════════════════════╝"
        echo -e "${COLOR_RESET}"
        
        # Service Status Panel
        echo -e "${COLOR_BOLD}${COLOR_CYAN}┌─ SERVICE STATUS ${COLOR_RESET}"
        echo -e "${COLOR_CYAN}│${COLOR_RESET}"
        echo -e "${COLOR_CYAN}│ Redis:         $(get_redis_status)${COLOR_RESET}"
        echo -e "${COLOR_CYAN}│ Ollama:        $(get_ollama_status)${COLOR_RESET}"
        echo -e "${COLOR_CYAN}│ Backend:       $(get_backend_status)${COLOR_RESET}"
        echo -e "${COLOR_CYAN}│${COLOR_RESET}"
        echo -e "${COLOR_CYAN}│ Uptime:        $(get_uptime)${COLOR_RESET}"
        echo -e "${COLOR_CYAN}│ Last Updated:  $(date '+%Y-%m-%d %H:%M:%S')${COLOR_RESET}"
        echo -e "${COLOR_CYAN}└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────${COLOR_RESET}"
        
        # System Metrics Panel
        echo ""
        echo -e "${COLOR_BOLD}${COLOR_CYAN}┌─ SYSTEM METRICS ${COLOR_RESET}"
        echo -e "${COLOR_CYAN}│${COLOR_RESET}"
        
        # CPU
        local cpu=$(get_cpu_usage)
        echo -n -e "${COLOR_CYAN}│ CPU:    "
        if (( $(echo "$cpu > 80" | bc -l) )); then
            echo -e "${COLOR_RED}${cpu}%${COLOR_RESET}${COLOR_CYAN}  "
        elif (( $(echo "$cpu > 50" | bc -l) )); then
            echo -e "${COLOR_YELLOW}${cpu}%${COLOR_RESET}${COLOR_CYAN}  "
        else
            echo -e "${COLOR_GREEN}${cpu}%${COLOR_RESET}${COLOR_CYAN}  "
        fi
        echo -e "│${COLOR_RESET}"
        
        # Memory
        echo -e "${COLOR_CYAN}│ Memory: $(get_memory_info)${COLOR_RESET}"
        echo -e "${COLOR_CYAN}│${COLOR_RESET}"
        
        # Disk
        echo -e "${COLOR_CYAN}│ Disk:   $(get_disk_info)${COLOR_RESET}"
        echo -e "${COLOR_CYAN}│${COLOR_RESET}"
        
        # Errors
        local error_count=$(get_error_count)
        echo -n -e "${COLOR_CYAN}│ Errors (24h): "
        if [ "$error_count" -gt 10 ]; then
            echo -e "${COLOR_RED}${error_count}${COLOR_RESET}${COLOR_CYAN}${COLOR_RESET}"
        elif [ "$error_count" -gt 0 ]; then
            echo -e "${COLOR_YELLOW}${error_count}${COLOR_RESET}${COLOR_CYAN}${COLOR_RESET}"
        else
            echo -e "${COLOR_GREEN}${error_count}${COLOR_RESET}${COLOR_CYAN}${COLOR_RESET}"
        fi
        echo -e "${COLOR_CYAN}│${COLOR_RESET}"
        echo -e "${COLOR_CYAN}└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────${COLOR_RESET}"
        
        # Logs Panel
        echo ""
        echo -e "${COLOR_BOLD}${COLOR_CYAN}┌─ ACTIVITY LOGS (Latest 20 entries) ${COLOR_RESET}"
        echo -e "${COLOR_CYAN}│${COLOR_RESET}"
        
        # Get latest log file
        local latest_log=$(ls -t "${LOGS_DIR}"/all_*.log 2>/dev/null | head -1)
        if [ -f "$latest_log" ]; then
            if [ -n "$FILTER_TERM" ]; then
                grep -i "$FILTER_TERM" "$latest_log" 2>/dev/null | tail -15 | while read line; do
                    # Color code by log level
                    if echo "$line" | grep -qi "error\|❌"; then
                        echo -e "${COLOR_CYAN}│${COLOR_RESET} ${COLOR_RED}${line}${COLOR_RESET}"
                    elif echo "$line" | grep -qi "warning\|⚠️"; then
                        echo -e "${COLOR_CYAN}│${COLOR_RESET} ${COLOR_YELLOW}${line}${COLOR_RESET}"
                    elif echo "$line" | grep -qi "success\|✅"; then
                        echo -e "${COLOR_CYAN}│${COLOR_RESET} ${COLOR_GREEN}${line}${COLOR_RESET}"
                    else
                        echo -e "${COLOR_CYAN}│${COLOR_RESET} ${line}"
                    fi
                done
            else
                tail -15 "$latest_log" 2>/dev/null | while read line; do
                    # Color code by log level
                    if echo "$line" | grep -qi "error\|❌"; then
                        echo -e "${COLOR_CYAN}│${COLOR_RESET} ${COLOR_RED}${line}${COLOR_RESET}"
                    elif echo "$line" | grep -qi "warning\|⚠️"; then
                        echo -e "${COLOR_CYAN}│${COLOR_RESET} ${COLOR_YELLOW}${line}${COLOR_RESET}"
                    elif echo "$line" | grep -qi "success\|✅"; then
                        echo -e "${COLOR_CYAN}│${COLOR_RESET} ${COLOR_GREEN}${line}${COLOR_RESET}"
                    else
                        echo -e "${COLOR_CYAN}│${COLOR_RESET} ${line}"
                    fi
                done
            fi
        else
            echo -e "${COLOR_CYAN}│${COLOR_RESET} No logs found"
        fi
        
        echo -e "${COLOR_CYAN}│${COLOR_RESET}"
        echo -e "${COLOR_CYAN}└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────${COLOR_RESET}"
        
        # Command input section
        echo ""
        echo -e "${COLOR_BOLD}${COLOR_YELLOW}Commands: --stop (shutdown) | --restart (reload) | filter <term> | clear | status | or ENTER to refresh${COLOR_RESET}"
        
        # Show filter status if active
        if [ -n "$FILTER_TERM" ]; then
            echo -e "${COLOR_YELLOW}Filtering: '${FILTER_TERM}'${COLOR_RESET}"
        fi
        
        # Refresh every 3 seconds
        sleep 3
    done
}

################################################################################
# Command Input Handler
################################################################################

listen_for_commands() {
    while [ "$RUNNING" = true ]; do
        echo -n ">>> "
        read -t 5 -r command || continue
        
        case "$command" in
            --stop)
                if confirm "Stop all services?"; then
                    log_info "Shutting down services..."
                    log_file "User initiated shutdown" "${MONITOR_LOG}"
                    shutdown_services
                    RUNNING=false
                    cleanup_monitor
                    log_success "Services stopped"
                    exit 0
                fi
                ;;
            --restart)
                if confirm "Restart all services?"; then
                    log_info "Restarting services..."
                    log_file "User initiated restart" "${MONITOR_LOG}"
                    shutdown_services
                    sleep 2
                    log_info "Services restarting..."
                    if bash "${SCRIPT_DIR}/boot.sh" > /dev/null 2>&1 &
                    then
                        log_success "Restart initiated"
                        sleep 5
                    else
                        log_failure "Restart failed"
                    fi
                fi
                ;;
            filter)
                echo -n "Enter filter term: "
                read -r filter_input
                FILTER_TERM="$filter_input"
                log_info "Filtering logs for: ${FILTER_TERM}"
                log_file "Filter applied: ${FILTER_TERM}" "${MONITOR_LOG}"
                ;;
            clear)
                FILTER_TERM=""
                log_info "Filter cleared"
                log_file "Filter cleared" "${MONITOR_LOG}"
                ;;
            status)
                display_detailed_status
                ;;
            "")
                # Just refresh dashboard
                ;;
            *)
                log_warn "Unknown command: ${command}"
                ;;
        esac
    done
}

display_detailed_status() {
    clear
    echo ""
    echo -e "${COLOR_BOLD}${COLOR_CYAN}═══════════════════════════════════════════════════════════${COLOR_RESET}"
    echo -e "${COLOR_BOLD}${COLOR_CYAN}  DETAILED SERVICE STATUS${COLOR_RESET}"
    echo -e "${COLOR_BOLD}${COLOR_CYAN}═══════════════════════════════════════════════════════════${COLOR_RESET}"
    echo ""
    
    print_header "Redis"
    local redis_status=$(docker inspect safina-redis 2>/dev/null)
    if [ -n "$redis_status" ]; then
        echo -e "Container Status: $(docker inspect -f '{{.State.Running}}' safina-redis)"
        echo -e "Uptime: $(docker inspect -f '{{.State.StartedAt}}' safina-redis)"
        echo -e "Health: $(check_redis_health && echo 'Healthy' || echo 'Unhealthy')"
    else
        echo "Container not found"
    fi
    
    print_header "Ollama"
    local ollama_status=$(docker inspect safina-ollama 2>/dev/null)
    if [ -n "$ollama_status" ]; then
        echo -e "Container Status: $(docker inspect -f '{{.State.Running}}' safina-ollama)"
        echo -e "Uptime: $(docker inspect -f '{{.State.StartedAt}}' safina-ollama)"
        echo -e "Health: $(check_ollama_health && echo 'Healthy' || echo 'Unhealthy')"
    else
        echo "Container not found"
    fi
    
    print_header "Backend"
    if [ -f "${PROJECT_ROOT}/.safina_backend.pid" ]; then
        local backend_pid=$(cat "${PROJECT_ROOT}/.safina_backend.pid")
        echo -e "Process ID: ${backend_pid}"
        echo -e "Running: $(is_process_running "$backend_pid" && echo 'Yes' || echo 'No')"
        echo -e "Health: $(check_backend_health && echo 'Healthy' || echo 'Unhealthy')"
    else
        echo "Process not found"
    fi
    
    echo ""
    echo -n "Press ENTER to return to dashboard..."
    read -r
}

shutdown_services() {
    log_info "Shutting down all services..."
    
    # Kill backend
    if [ -f "${PROJECT_ROOT}/.safina_backend.pid" ]; then
        local backend_pid=$(cat "${PROJECT_ROOT}/.safina_backend.pid")
        if is_process_running "$backend_pid"; then
            log_info "Stopping backend (PID: ${backend_pid})..."
            kill_process "$backend_pid"
        fi
        rm -f "${PROJECT_ROOT}/.safina_backend.pid"
    fi
    
    # Stop containers
    log_info "Stopping Docker containers..."
    docker-compose -f "${DOCKER_COMPOSE}" down >> "${MONITOR_LOG}" 2>&1 || true
    
    # Cleanup
    rm -f "${PROJECT_ROOT}"/.safina_*.pid 2>/dev/null || true
    
    log_file "Services shut down" "${MONITOR_LOG}"
}

################################################################################
# Main
################################################################################

main() {
    setup_monitoring || exit 1
    
    log_info "Starting monitoring dashboard..."
    log_file "Monitoring started" "${MONITOR_LOG}"
    
    # Run display and input in parallel
    display_dashboard &
    local display_pid=$!
    
    listen_for_commands
    
    wait $display_pid 2>/dev/null || true
}

# Run main if script is executed directly
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    main "$@"
fi
