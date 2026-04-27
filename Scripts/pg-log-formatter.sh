#!/usr/bin/env bash
# PostgreSQL Log Formatter - Colorize and format PG logs
# ANSI color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
GRAY='\033[0;90m'
RESET='\033[0m'

# Colorize PostgreSQL log output
colorize_log() {
    while IFS= read -r line; do
        # Timestamp
        if [[ "$line" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}[[:space:]] ]]; then
            timestamp="${line:0:25}"
            rest="${line:26}"
            echo -e "${GRAY}${timestamp}${RESET} $(colorize_message "$rest")"
        else
            echo -e "$(colorize_message "$line")"
        fi
    done
}

colorize_message() {
    local msg="$1"
    
    # Error levels
    case "$msg" in
        *FATAL*|*PANIC*)
            echo -e "${RED}${msg}${RESET}"
            return
            ;;
        *ERROR*)
            echo -e "${RED}${msg}${RESET}"
            return
            ;;
        *WARNING*)
            echo -e "${YELLOW}${msg}${RESET}"
            return
            ;;
        *LOG*|*INFO*)
            echo -e "${CYAN}${msg}${RESET}"
            return
            ;;
        *DEBUG*)
            echo -e "${MAGENTA}${msg}${RESET}"
            return
            ;;
        *NOTICE*)
            echo -e "${GREEN}${msg}${RESET}"
            return
            ;;
    esac
    
    # SQL statements
    if [[ "$msg" =~ statement:|duration: ]]; then
        echo -e "${GREEN}${msg}${RESET}"
        return
    fi
    
    # Connection info
    if [[ "$msg" =~ connection|received|authenticated ]]; then
        echo -e "${BLUE}${msg}${RESET}"
        return
    fi
    
    # Checkpoint and system
    if [[ "$msg" =~ checkpoint|archive|autovacuum ]]; then
        echo -e "${WHITE}${msg}${RESET}"
        return
    fi
    
    echo "$msg"
}

# Export for use
export -f colorize_log colorize_message