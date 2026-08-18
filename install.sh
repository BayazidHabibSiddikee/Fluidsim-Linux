#!/bin/bash
# FluidSim Linux - System installer
# Usage: sudo ./install.sh   (or ./install.sh --user for current user only)
set -e

APP_NAME="fluidsim"
APP_DIR="/usr/local/share/fluidsim"
DESKTOP_FILE="${APP_NAME}.desktop"
ICON_FILE="fluidsim.png"

USER_MODE=""
if [[ "${1}" == "--user" ]]; then
    USER_MODE="--user"
    APP_DIR="$HOME/.local/share/fluidsim"
fi

echo "=== FluidSim Linux Installer ==="
echo ""

# Detect install prefix
if [ -z "$USER_MODE" ]; then
    echo "[sudo] Password may be requested..."
    sudo mkdir -p "$APP_DIR" /usr/local/bin ~/.local/share/applications ~/.local/share/icons/hicolor/256x256/apps
    sudo cp -r src bin icons assets requirements.txt launcher.py main.py run.sh docs "$APP_DIR/"
    [ -f LICENSE ] && sudo cp LICENSE "$APP_DIR/" || true
    sudo ln -sf "$APP_DIR/bin/fl_sim" /usr/local/bin/fl_sim
    sudo cp ~/.local/share/applications/$DESKTOP_FILE 2>/dev/null || true
    sudo install -Dm644 icons/$ICON_FILE "/usr/share/icons/hicolor/256x256/apps/$ICON_FILE"
    DESKTOP_SRC="/usr/local/share/applications/$DESKTOP_FILE"
    ICON_PATH="fluidsim"
else
    mkdir -p "$APP_DIR" "$HOME/.local/bin" "$HOME/.local/share/applications" "$HOME/.local/share/icons/hicolor/256x256/apps"
    cp -r src bin icons assets requirements.txt launcher.py main.py run.sh docs "$APP_DIR/"
    [ -f LICENSE ] && cp LICENSE "$APP_DIR/" || true
    ln -sf "$APP_DIR/bin/fl_sim" "$HOME/.local/bin/fl_sim"
    cp "$HOME/.local/share/applications/$DESKTOP_FILE" 2>/dev/null || true
    install -Dm644 icons/$ICON_FILE "$HOME/.local/share/icons/hicolor/256x256/apps/$ICON_FILE"
    DESKTOP_SRC="$HOME/.local/share/applications/$DESKTOP_FILE"
    ICON_PATH="fluidsim"
fi

# Rewrite desktop file with correct paths
cat > "$DESKTOP_SRC" << DEOF
[Desktop Entry]
Name=FluidSim Linux
Comment=Hydraulic & Pneumatic Circuit Simulator
Exec=$APP_DIR/bin/fl_sim
Icon=$ICON_PATH
Type=Application
Categories=Education;Engineering;
Terminal=false
StartupNotify=true
Keywords=hydraulic;pneumatic;simulator;engineering;fluid;
GenericName=Circuit Simulator
StartupWMClass=fl_sim
DEOF

# Install dependencies if missing
python3 -c "import PySide6" 2>/dev/null || {
    echo ""
    echo "Installing Python dependencies..."
    pip3 $USER_MODE install -r "$APP_DIR/requirements.txt"
}

echo ""
echo "✅ Installed to: $APP_DIR"
echo "✅ Desktop entry: $DESKTOP_SRC"
echo "✅ Icon installed"
echo ""
echo "Launch with: fl_sim  (or search 'FluidSim' in your app menu)"
gtk-update-icon-cache -f "$HOME/.local/share/icons/hicolor/256x256/apps/" 2>/dev/null || true
update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
