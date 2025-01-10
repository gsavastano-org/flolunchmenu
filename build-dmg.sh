#!/bin/bash

# --- Configuration ---
APP_NAME="WeeklyMealOrder"
VOLUME_NAME="Weekly Meal Order"
ICON_FILE="app/assets/icon.icns"
PROJECT_ROOT=$(git rev-parse --show-toplevel)

# --- Build the Application with PyInstaller ---
echo "Building application with PyInstaller..."
pyinstaller --onefile --windowed \
  --add-data "app/assets:app/assets" \
  --add-data "app/core/credentials.json:app/core" \
  --add-data ".env:." \
  --name "$APP_NAME" \
  --icon="$ICON_FILE" \
  "$PROJECT_ROOT/ui.py"

if [ $? -ne 0 ]; then
  echo "Error: PyInstaller build failed."
  exit 1
fi

# --- Create DMG with hdiutil ---
echo "Creating DMG file with hdiutil..."
hdiutil create -volname "$VOLUME_NAME" -srcfolder dist -ov -format UDZO "$APP_NAME.dmg"

if [ $? -ne 0 ]; then
  echo "Error: DMG creation failed."
  exit 1
fi

echo "Build completed successfully. Created $APP_NAME.dmg"