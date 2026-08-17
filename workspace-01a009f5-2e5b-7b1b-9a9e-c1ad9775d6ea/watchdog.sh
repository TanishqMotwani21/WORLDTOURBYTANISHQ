#!/bin/bash
# Watchdog: keep the FastAPI app + Cloudflare tunnel alive for the live demo.
# Restarts the app if it stops answering; restarts the tunnel on 530/dead errors
# (a restarted tunnel gets a new trycloudflare URL, written to PUBLIC_URL.txt).
APP_DIR=/home/user/title-verification/backend
URL_FILE=/home/user/title-verification/PUBLIC_URL.txt
LOG=/home/user/watchdog.log

start_app() {
  cd "$APP_DIR" && nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 >> /home/user/app.log 2>&1 &
  echo "$(date -u +%H:%M:%S) watchdog: app restarted (pid $!)" >> "$LOG"
  sleep 8
}
start_tunnel() {
  pkill -f "cloudflared tunnel" 2>/dev/null; sleep 2
  nohup /home/user/cloudflared tunnel --url http://localhost:8000 --no-autoupdate > /home/user/tunnel.log 2>&1 &
  echo "$(date -u +%H:%M:%S) watchdog: tunnel restarting (pid $!)" >> "$LOG"
  sleep 12
  NEW=$(grep -o "https://[a-z0-9-]*\.trycloudflare\.com" /home/user/tunnel.log | head -1)
  if [ -n "$NEW" ]; then echo "$NEW" > "$URL_FILE"; echo "$(date -u +%H:%M:%S) watchdog: new URL $NEW" >> "$LOG"; fi
}

while true; do
  if ! curl -sf -m 6 http://localhost:8000/api/health > /dev/null 2>&1; then
    if ! curl -sf -m 6 http://localhost:8000/ > /dev/null 2>&1; then start_app; fi
  fi
  PUB=$(head -1 "$URL_FILE" 2>/dev/null)
  if [ -n "$PUB" ]; then
    CODE=$(curl -s -o /dev/null -m 20 -w "%{http_code}" "$PUB/api/health" 2>/dev/null || echo 000)
    if [ "$CODE" = "530" ] || [ "$CODE" = "000" ] || [ "$CODE" = "502" ] || [ "$CODE" = "503" ]; then
      # app alive but tunnel dead → recreate only the tunnel
      if curl -sf -m 6 http://localhost:8000/api/health > /dev/null 2>&1; then start_tunnel; fi
    fi
  fi
  sleep 30
done
