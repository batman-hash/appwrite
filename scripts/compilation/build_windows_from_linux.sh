#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)/compilation_cpp"
BUILD_DIR="${BUILD_DIR:-build/windows}"
MINGW_CXX="${MINGW_CXX:-x86_64-w64-mingw32-g++}"
TARGET="${1:-windows-all}"

run_local_build() {
  echo "Using local MinGW-w64 compiler: ${MINGW_CXX}"
  make -C "${ROOT_DIR}" BUILD_DIR="${BUILD_DIR}" MINGW_CXX="${MINGW_CXX}" "${TARGET}"
}

run_docker_build() {
  echo "Local MinGW-w64 compiler not found. Falling back to Docker."
  docker build -t mem-cross-build "${ROOT_DIR}"
  docker run --rm \
    --user "$(id -u):$(id -g)" \
    -v "${ROOT_DIR}:/workspace" \
    -w /workspace \
    mem-cross-build \
    make BUILD_DIR="${BUILD_DIR}" MINGW_CXX=x86_64-w64-mingw32-g++ "${TARGET}"
}

if command -v "${MINGW_CXX}" >/dev/null 2>&1; then
  run_local_build
else
  run_docker_build
fi
