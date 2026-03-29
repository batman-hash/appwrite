#!/bin/bash
# Build and run script for DevNavigator

set -e

BUILD_DIR="cpp_crawler/build"
BIN_NAME="devnavigator"

echo "🔨 Building C++ crawler..."

# Create build directory
mkdir -p "$BUILD_DIR"
cd "$BUILD_DIR"

# Run CMake and build
cmake ..
make

echo "✅ Build complete!"
echo "📍 Binary location: $BUILD_DIR/$BIN_NAME"
echo ""
echo "To run email sender:"
echo "  ./$BIN_NAME"
