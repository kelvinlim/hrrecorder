#!/bin/bash
# create_dmg.sh
# Creates a macOS DMG installer for HR Recorder

set -e

APP_NAME="hrrecorder"
APP_BUNDLE="dist/${APP_NAME}.app"
DMG_NAME="hrrecorder.dmg"
DMG_PATH="dist/${DMG_NAME}"
VOLUME_NAME="HR Recorder"
TEMP_DMG="dist/temp.dmg"

echo "Creating DMG for ${APP_NAME}..."

# Check if app bundle exists
if [ ! -d "$APP_BUNDLE" ]; then
    echo "Error: Application bundle not found at $APP_BUNDLE"
    exit 1
fi

# Remove old DMG if exists
if [ -f "$DMG_PATH" ]; then
    echo "Removing old DMG..."
    rm -f "$DMG_PATH"
fi

# Remove temp DMG if exists
if [ -f "$TEMP_DMG" ]; then
    rm -f "$TEMP_DMG"
fi

# Create temporary DMG
echo "Creating temporary DMG..."
hdiutil create -size 200m -fs HFS+ -volname "$VOLUME_NAME" "$TEMP_DMG"

# Mount the temporary DMG
echo "Mounting temporary DMG..."
MOUNT_OUTPUT=$(hdiutil attach "$TEMP_DMG" -readwrite -noverify -noautoopen)
echo "Mount output: $MOUNT_OUTPUT"
MOUNT_DIR=$(echo "$MOUNT_OUTPUT" | grep "/Volumes/" | sed 's/.*\(\/Volumes\/.*\)/\1/' | tail -1)

if [ -z "$MOUNT_DIR" ]; then
    echo "Error: Failed to mount temporary DMG"
    echo "Trying alternative mount path..."
    MOUNT_DIR="/Volumes/${VOLUME_NAME}"
fi

echo "Mounted at: $MOUNT_DIR"

# Verify mount point exists and is writable
if [ ! -d "$MOUNT_DIR" ]; then
    echo "Error: Mount directory does not exist: $MOUNT_DIR"
    exit 1
fi

# Copy application bundle to DMG using ditto (preserves permissions and attributes)
echo "Copying application to DMG..."
if ! ditto "$APP_BUNDLE" "$MOUNT_DIR/$(basename "$APP_BUNDLE")"; then
    echo "Error: Failed to copy app bundle"
    echo "Trying with sudo..."
    sudo ditto "$APP_BUNDLE" "$MOUNT_DIR/$(basename "$APP_BUNDLE")"
fi

# Create Applications symlink
echo "Creating Applications symlink..."
ln -s /Applications "$MOUNT_DIR/Applications"

# Optional: Add background image or custom view settings
# mkdir "$MOUNT_DIR/.background"
# cp background.png "$MOUNT_DIR/.background/"

# Set DMG window properties (optional - requires AppleScript)
# echo '
#    tell application "Finder"
#      tell disk "'$VOLUME_NAME'"
#        open
#        set current view of container window to icon view
#        set toolbar visible of container window to false
#        set the bounds of container window to {400, 100, 900, 500}
#        set viewOptions to the icon view options of container window
#        set arrangement of viewOptions to not arranged
#        set icon size of viewOptions to 128
#        set position of item "'$APP_NAME'.app" of container window to {150, 150}
#        set position of item "Applications" of container window to {350, 150}
#        update without registering applications
#        delay 2
#        close
#      end tell
#    end tell
# ' | osascript

# Unmount the temporary DMG
echo "Unmounting temporary DMG..."
hdiutil detach "$MOUNT_DIR"

# Convert to compressed read-only DMG
echo "Converting to final DMG..."
hdiutil convert "$TEMP_DMG" -format UDZO -o "$DMG_PATH"

# Remove temporary DMG
rm -f "$TEMP_DMG"

echo "DMG created successfully: $DMG_PATH"

# Get DMG size
DMG_SIZE=$(du -h "$DMG_PATH" | cut -f1)
echo "DMG size: $DMG_SIZE"
