#!/bin/sh
set -eu

REPO_ROOT="/opt/devnavigator"

if [ "$#" -eq 0 ]; then
    exec python3 "$REPO_ROOT/devnavigator.py" --help
fi

case "$1" in
    monitor|toy-server|toy-client)
        exec python3 "$REPO_ROOT/compilation_cpp/scripts/network_stability_monitor.py" "$@"
        ;;
    *)
        exec python3 "$REPO_ROOT/devnavigator.py" "$@"
        ;;
esac
