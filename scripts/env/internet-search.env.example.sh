#!/bin/sh
# Copy this file to internet-search.env.sh and source it before running
# internet-search wrappers.
#
# Example:
#   cp scripts/env/internet-search.env.example.sh scripts/env/internet-search.env.sh
#   source ./scripts/env/internet-search.env.sh

export HUNTER_API_KEY=your_hunter_key
export APOLLO_API_KEY=your_apollo_key

# Optional provider/network settings:
export EXTRACT_PROXY_URL=
export INTERNET_SEARCH_STORE=0
export INTERNET_SEARCH_DB_PATH=./database/internet_search.db
export INTERNET_SEARCH_EXPORT_PATH=./exports/internet_search_results.csv
export AUTO_SYSTEM_THRESHOLD_GUARD=1
export SEARCH_THRESHOLD_WARN_ONLY=0
export SEARCH_MAX_CPU_PERCENT=85
export SEARCH_MAX_MEMORY_PERCENT=80
export SEARCH_MAX_DISK_PERCENT=90
export SEARCH_MAX_PROCESS_COUNT=600
export SEARCH_MAX_LISTENING_PORTS=256
export SEARCH_MAX_SINGLE_PROCESS_CPU_PERCENT=25
export SEARCH_MAX_SINGLE_PROCESS_MEMORY_PERCENT=25
export SEARCH_MAX_SINGLE_PROCESS_IO_MBPS=25
export SEARCH_WARN_ONLY_PROCESS_NAMES=code,gnome-shell
