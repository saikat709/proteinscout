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
echo "Preparing backend for bundling..."

# Ensure resources backend folder exists and copy backend files for packaging
mkdir -p src-tauri/resources/backend
rm -rf src-tauri/resources/backend/main.py
rm -rf src-tauri/resources/backend/routers
rm -rf src-tauri/resources/backend/core

cp backend/main.py src-tauri/resources/backend/ || true
cp -r backend/routers src-tauri/resources/backend/ || true
cp -r backend/core src-tauri/resources/backend/ || true

echo "Done: Backend prepared for bundling"
echo ""
echo "Run: npm run tauri:build"
