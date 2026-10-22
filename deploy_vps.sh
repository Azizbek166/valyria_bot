#!/bin/bash
# Valyria RPG Bot - Ubuntu / Debian Avtomatik O'rnatish Skripti

set -e

echo "=== Valyria RPG Bot Server O'rnatish Boshlandi ==="

sudo apt update && sudo apt install -y python3 python3-pip python3-venv git

INSTALL_DIR="/opt/valyria_bot"

if [ ! -d "$INSTALL_DIR" ]; then
    sudo mkdir -p "$INSTALL_DIR"
    sudo chown -R "$USER:$USER" "$INSTALL_DIR"
fi

cd "$INSTALL_DIR"

if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

SERVICE_FILE="/etc/systemd/system/valyria_bot.service"

sudo bash -c "cat > $SERVICE_FILE" <<EOF
[Unit]
Description=Valyria RPG Telegram Bot
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/venv/bin/python $INSTALL_DIR/bot.py
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable valyria_bot
sudo systemctl restart valyria_bot

echo "=== Valyria Bot Muvaffaqiyatli Ishga Tushirildi! ==="
echo "Holatni ko'rish: sudo systemctl status valyria_bot"
echo "Loglarni kuzatish: sudo journalctl -u valyria_bot -f"
