#!/bin/bash
# Build and run script for DevNavigator

set -e

BUILD_DIR="cpp_crawler/build"
BIN_NAME="devnavigator"
PROJECT_ROOT="$(pwd)"

echo "🔨 Building C++ crawler..."

# Create build directory
mkdir -p "$BUILD_DIR"
cd "$BUILD_DIR"

# Run CMake and build
cmake ..
cmake --build .

echo "✅ Build complete!"
echo "📍 Binary location: $PROJECT_ROOT/$BUILD_DIR/$BIN_NAME"
echo ""
echo "To run email sender:"
echo "  $PROJECT_ROOT/$BUILD_DIR/$BIN_NAME"
echo ""
echo "Optional custom database path:"
echo "  $PROJECT_ROOT/$BUILD_DIR/$BIN_NAME /path/to/devnav.db"
