#!/bin/bash
# Post-build script: copies backend resources into all bundle locations
# Run after tauri build finishes to populate AppImage, deb, and other bundles with backend files

BUNDLE_DIR="src-tauri/target/release/bundle"
BACKEND_SRC="src-tauri/resources/backend"

# Exit silently if no bundles were created (e.g., during dev)
if [ ! -d "$BUNDLE_DIR" ]; then
    exit 0
fi

echo "[Post-Bundle] Copying backend resources into bundle outputs..."

# Copy to AppImage
if [ -d "$BUNDLE_DIR/appimage" ]; then
    APPIMAGE_USR="$BUNDLE_DIR/appimage/proteinscout.AppDir/usr"
    if [ -d "$APPIMAGE_USR" ]; then
        echo "[Post-Bundle] Copying backend to AppImage..."
        rm -rf "$APPIMAGE_USR/backend"
        cp -r "$BACKEND_SRC" "$APPIMAGE_USR/backend"
        chmod +x "$APPIMAGE_USR/backend/backend" 2>/dev/null || true
        echo "[Post-Bundle] ✓ AppImage backend copied"
    fi
fi

# Copy to deb (if applicable)
if [ -d "$BUNDLE_DIR/deb" ]; then
    echo "[Post-Bundle] Copying backend to deb..."
    for deb_dir in "$BUNDLE_DIR/deb"/*; do
        if [ -d "$deb_dir/usr" ]; then
            rm -rf "$deb_dir/usr/backend"
            cp -r "$BACKEND_SRC" "$deb_dir/usr/backend"
            chmod +x "$deb_dir/usr/backend/backend" 2>/dev/null || true
        fi
    done
    echo "[Post-Bundle] ✓ deb backend copied"
fi

# Copy to dmg (macOS)
if [ -d "$BUNDLE_DIR/macos" ]; then
    echo "[Post-Bundle] Copying backend to macOS bundle..."
    for app_bundle in "$BUNDLE_DIR/macos"/*.app; do
        if [ -d "$app_bundle/Contents/Resources" ]; then
            rm -rf "$app_bundle/Contents/Resources/backend"
            cp -r "$BACKEND_SRC" "$app_bundle/Contents/Resources/backend"
            chmod +x "$app_bundle/Contents/Resources/backend/backend" 2>/dev/null || true
        fi
    done
    echo "[Post-Bundle] ✓ macOS backend copied"
fi

echo "[Post-Bundle] Done!"
