#!/bin/bash
# Script de instalacion para GSC Dashboard en macOS
# Ejecutar con: bash install.sh

set -e

echo "========================================"
echo "  GSC Dashboard - Instalacion"
echo "========================================"
echo ""

# Detectar el directorio del script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PYTHON_PATH=$(which python3)
PLIST_NAME="com.gsc.dashboard"
PLIST_PATH="$HOME/Library/LaunchAgents/${PLIST_NAME}.plist"

echo "[1/4] Verificando Python..."
if [ -z "$PYTHON_PATH" ]; then
    echo "Error: Python3 no encontrado. Instala Python primero."
    exit 1
fi
echo "  Python encontrado: $PYTHON_PATH"

echo ""
echo "[2/4] Instalando dependencias..."
pip3 install -q google-auth google-auth-oauthlib google-api-python-client flask
echo "  Dependencias instaladas"

echo ""
echo "[3/4] Creando servicio de arranque automatico..."

# Crear el Launch Agent
cat > "$PLIST_PATH" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${PLIST_NAME}</string>
    <key>ProgramArguments</key>
    <array>
        <string>${PYTHON_PATH}</string>
        <string>${SCRIPT_DIR}/app.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>${HOME}/.config/gsc/dashboard.log</string>
    <key>StandardErrorPath</key>
    <string>${HOME}/.config/gsc/dashboard.error.log</string>
    <key>WorkingDirectory</key>
    <string>${SCRIPT_DIR}</string>
</dict>
</plist>
EOF

echo "  Launch Agent creado en: $PLIST_PATH"

echo ""
echo "[4/4] Iniciando servicio..."
launchctl unload "$PLIST_PATH" 2>/dev/null || true
launchctl load "$PLIST_PATH"

echo ""
echo "========================================"
echo "  Instalacion completada!"
echo "========================================"
echo ""
echo "El dashboard esta disponible en:"
echo "  http://127.0.0.1:5000"
echo ""
echo "El servicio se iniciara automaticamente al arrancar tu Mac."
echo ""
echo "Comandos utiles:"
echo "  Detener:   launchctl unload ~/Library/LaunchAgents/${PLIST_NAME}.plist"
echo "  Iniciar:   launchctl load ~/Library/LaunchAgents/${PLIST_NAME}.plist"
echo "  Ver logs:  tail -f ~/.config/gsc/dashboard.log"
echo ""
