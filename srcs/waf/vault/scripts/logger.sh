#!/bin/bash

LOG_DIR="/var/log/vault"

# Solo mantenemos las funciones que realmente usamos
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
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log_secret() {
    local path=$1
    echo "📦 [SECRET] Secret stored: $path"
}
