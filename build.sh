#!/bin/bash
# Build script for ProteinScout
# Just builds the frontend - Rust will handle backend spawning

set -e

echo "=== Building ProteinScout ==="
echo ""

# Build frontend
echo "Building React frontend..."
npm run build

echo ""
echo "✓ Frontend built successfully"
echo ""
echo "Run: npm run tauri:build"
