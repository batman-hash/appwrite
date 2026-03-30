#!/bin/bash
# Clear DevNavigator runtime search state.
#
# Safe default:
# - removes internet-search runtime state files only when no search process is holding the lock
# - does not touch your contact database
#
# Optional:
#   CLEAR_GEO_CACHE=1  -> also clear cached IP geolocation rows from the database

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

RUNTIME_DIRS=(
  "${INTERNET_SEARCH_RUNTIME_DIR:-./runtime/internet-search}"
  "${INTERNET_SEARCH_RUNTIME_DIR_DOCKER:-./runtime/internet-search-docker}"
)

clear_runtime_dir() {
  local runtime_dir="$1"
  local lock_file="${runtime_dir}/search.lock"
  local pid_file="${runtime_dir}/search.pid"
  local state_file="${runtime_dir}/search.state"
  local last_command_file="${runtime_dir}/last-command.txt"

  if [ ! -d "$runtime_dir" ]; then
    return 0
  fi

  mkdir -p "$runtime_dir"
  exec 9>"$lock_file"
  if flock -n 9; then
    rm -f "$pid_file" "$state_file" "$last_command_file"
    echo "✓ Cleared runtime search state: $runtime_dir"
  else
    echo "ℹ️  Skipped active runtime directory: $runtime_dir"
  fi
  exec 9>&-
}

for runtime_dir in "${RUNTIME_DIRS[@]}"; do
  clear_runtime_dir "$runtime_dir"
done

if [ "${CLEAR_GEO_CACHE:-0}" = "1" ]; then
  python3 - <<'PY'
import os
import sqlite3

db_path = os.getenv("DATABASE_PATH", "./database/devnav.db")
conn = sqlite3.connect(db_path)
cur = conn.cursor()
cur.execute("DELETE FROM ip_tracking")
deleted = cur.rowcount
conn.commit()
conn.close()
print(f"✓ Cleared geo cache rows: {deleted} from {db_path}")
PY
fi
