#!/bin/bash

# This script provides centralized logging functions for all other scripts.
# Features:
# - Multiple log levels handling (INFO, ERROR, WARN, DEBUG)
# - Consistent timestamp formatting
# - Visual separators for better readability
# - Specific secret logging with emojis
# - Log file management in different locations

LOG_DIR="/var/log/vault"
AUDIT_LOG="${LOG_DIR}/audit.log"
ERROR_LOG="${LOG_DIR}/error.log"
SYSTEM_LOG="${LOG_DIR}/system.log"
OPERATION_LOG="${LOG_DIR}/operation.log"

# Export log files for external use
export AUDIT_LOG="${LOG_DIR}/audit.log"
export ERROR_LOG="${LOG_DIR}/error.log"
export SYSTEM_LOG="${LOG_DIR}/system.log"
export OPERATION_LOG="${LOG_DIR}/operation.log"

log() {
    local level=$1
    local message=$2
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "$timestamp [$level] $message"
}

show_section() {
    echo -e "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  $1"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "${OPERATION_LOG}"
}

log_secret() {
    local path=$1
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "📦 ${timestamp} [SECRET] Secret stored: $path"
    echo "   └─ Status: ✅ Successfully saved"
}
