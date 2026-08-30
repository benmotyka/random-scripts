#!/usr/bin/env bash
# Instalator watchdoga P2P. Idempotentny - mozna uruchamiac wielokrotnie,
# istniejaca konfiguracja nie zostanie nadpisana.
set -euo pipefail

PREFIX=/opt/nvr-p2p-watchdog
CONF=/etc/nvr-p2p-watchdog.conf
UNITS=/etc/systemd/system
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ $EUID -ne 0 ]]; then
    echo "Uruchom przez sudo: sudo ./install.sh" >&2
    exit 1
fi

echo "==> Instaluje skrypt do $PREFIX"
install -d -m 755 -o root -g root "$PREFIX"
install -m 755 -o root -g root "$SRC/watchdog.py" "$PREFIX/watchdog.py"

echo "==> Konfiguracja"
if [[ -f "$CONF" ]]; then
    echo "    $CONF juz istnieje - zostawiam bez zmian"
else
    install -m 600 -o root -g root "$SRC/nvr-p2p-watchdog.conf.example" "$CONF"
    echo "    utworzono $CONF - UZUPELNIJ haslo i dane bota"
fi

echo "==> Jednostki systemd"
install -m 644 -o root -g root "$SRC/systemd/nvr-p2p-watchdog.service" "$UNITS/"
install -m 644 -o root -g root "$SRC/systemd/nvr-p2p-watchdog.timer" "$UNITS/"
systemctl daemon-reload
systemctl enable --now nvr-p2p-watchdog.timer

echo
echo "Gotowe. Timer aktywny:"
systemctl list-timers nvr-p2p-watchdog --no-pager | sed -n 2p
echo
echo "Test powiadomien:  sudo $PREFIX/watchdog.py --test-notify"
echo "Podglad logu:      sudo tail -f /var/log/nvr-p2p-watchdog.log"
