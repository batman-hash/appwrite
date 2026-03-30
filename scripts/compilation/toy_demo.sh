#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)/compilation_cpp"
SOCKET_PATH="${SOCKET_PATH:-/tmp/toy_process_server.sock}"
SERVER_BIN="${ROOT_DIR}/build/linux/toy_server"
CLIENT_BIN="${ROOT_DIR}/build/linux/toy_client"

print_usage() {
  cat <<'EOF'
Usage:
  ./toy_demo.sh build
  ./toy_demo.sh server
  ./toy_demo.sh client status
  ./toy_demo.sh interactive
  ./toy_demo.sh demo
  ./toy_demo.sh retry-demo

Commands:
  build        Compile the local Linux toy server and client.
  server       Run the local Unix-socket server.
  client ...   Send a one-shot command to the server.
  interactive  Open the interactive local client.
  demo         Build everything, start the server, run a few sample commands, and stop it.
  retry-demo   Show the client retrying a dropped response and replaying the cached reply.

Notes:
  - This script is local-only and uses a Unix domain socket.
  - Override the socket path with SOCKET_PATH=/tmp/custom.sock.
  - The client also supports --target=/tmp/custom.sock.
EOF
}

ensure_built() {
  make -C "${ROOT_DIR}" linux-ipc
}

wait_for_socket() {
  local attempts=50
  local delay=0.1

  for _ in $(seq 1 "${attempts}"); do
    if [[ -S "${SOCKET_PATH}" ]]; then
      return 0
    fi
    sleep "${delay}"
  done

  echo "Timed out waiting for server socket at ${SOCKET_PATH}" >&2
  return 1
}

run_server() {
  exec "${SERVER_BIN}"
}

run_client() {
  exec "${CLIENT_BIN}" "--target=${SOCKET_PATH}" "$@"
}

run_demo() {
  local server_pid=""

  "${SERVER_BIN}" &
  server_pid=$!

  cleanup() {
    if [[ -n "${server_pid}" ]] && kill -0 "${server_pid}" >/dev/null 2>&1; then
      "${CLIENT_BIN}" "--socket=${SOCKET_PATH}" quit >/dev/null 2>&1 || true
      wait "${server_pid}" >/dev/null 2>&1 || true
    fi
  }

  trap cleanup EXIT INT TERM

  wait_for_socket

  echo "== status =="
  "${CLIENT_BIN}" "--socket=${SOCKET_PATH}" status

  echo "== ping =="
  "${CLIENT_BIN}" "--socket=${SOCKET_PATH}" ping

  echo "== echo =="
  "${CLIENT_BIN}" "--socket=${SOCKET_PATH}" "hello from toy_demo.sh"

  echo "== quit =="
  "${CLIENT_BIN}" "--socket=${SOCKET_PATH}" quit
  wait "${server_pid}"
  server_pid=""
  trap - EXIT INT TERM
}

run_retry_demo() {
  local server_pid=""

  "${SERVER_BIN}" &
  server_pid=$!

  cleanup() {
    if [[ -n "${server_pid}" ]] && kill -0 "${server_pid}" >/dev/null 2>&1; then
      "${CLIENT_BIN}" "--socket=${SOCKET_PATH}" quit >/dev/null 2>&1 || true
      wait "${server_pid}" >/dev/null 2>&1 || true
    fi
  }

  trap cleanup EXIT INT TERM

  wait_for_socket

  echo "== arm dropped response =="
  "${CLIENT_BIN}" "--socket=${SOCKET_PATH}" drop-next-response

  echo "== ping with retry =="
  "${CLIENT_BIN}" "--socket=${SOCKET_PATH}" ping

  echo "== stats =="
  "${CLIENT_BIN}" "--socket=${SOCKET_PATH}" stats

  echo "== quit =="
  "${CLIENT_BIN}" "--socket=${SOCKET_PATH}" quit
  wait "${server_pid}"
  server_pid=""
  trap - EXIT INT TERM
}

main() {
  local command="${1:-demo}"

  case "${command}" in
    build)
      ensure_built
      ;;
    server)
      ensure_built
      run_server
      ;;
    client)
      shift || true
      ensure_built
      if [[ $# -eq 0 ]]; then
        echo "Please provide a command for the client." >&2
        exit 1
      fi
      run_client "$@"
      ;;
    interactive)
      ensure_built
      exec "${CLIENT_BIN}" "--target=${SOCKET_PATH}" --interactive
      ;;
    demo)
      ensure_built
      run_demo
      ;;
    retry-demo)
      ensure_built
      run_retry_demo
      ;;
    help|-h|--help)
      print_usage
      ;;
    *)
      echo "Unknown command: ${command}" >&2
      print_usage
      exit 1
      ;;
  esac
}

main "$@"
