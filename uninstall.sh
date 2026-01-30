#!/bin/bash
# Script de desinstalacion para GSC Dashboard en macOS

PLIST_NAME="com.gsc.dashboard"
PLIST_PATH="$HOME/Library/LaunchAgents/${PLIST_NAME}.plist"

echo "Deteniendo servicio..."
launchctl unload "$PLIST_PATH" 2>/dev/null || true

echo "Eliminando Launch Agent..."
rm -f "$PLIST_PATH"

echo "Desinstalacion completada."
echo "Los archivos del proyecto no se han eliminado."
