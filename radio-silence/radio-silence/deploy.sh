#!/usr/bin/env bash
# Radio Silence - one-shot deploy. Run as root on a FRESH Ubuntu server,
# from inside the extracted radio-silence folder.
set -euo pipefail
cd "$(dirname "$0")"

echo "[1/5] Installing Docker + dig (if missing)"
command -v docker >/dev/null || curl -fsSL https://get.docker.com | sh
apt-get install -y -qq dnsutils python3 >/dev/null

echo "[2/5] Generating zone (flag comes from flag_guid.txt)"
mkdir -p zones cache
python3 gen_zone.py

echo "[3/5] Starting BIND"
chmod -R 777 zones cache
docker compose up -d
sleep 6

echo "[4/5] Local self-test"
dig +short @127.0.0.1 -p 5052 comms-check.cofastic.com TXT
dig +short @127.0.0.1 -p 5052 signals.cofastic.com DNSKEY | head -c 60; echo
dig +short @127.0.0.1 -p 5052 relay-000.signals.cofastic.com NSEC
if dig @127.0.0.1 -p 5052 signals.cofastic.com AXFR +tcp | grep -q "Transfer failed"; then
  echo "AXFR correctly refused"; else echo "WARNING: AXFR not refused!"; fi

echo "[5/5] Done. Flag (keep secret): $(cat flag.txt)"
echo "Now test from OUTSIDE: python3 solve.py <server-ip> 5052"
