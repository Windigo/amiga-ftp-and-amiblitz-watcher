#!/bin/bash
# ============================================
# AmiBlitz3 Development Environment Starter
# ============================================
# Start de FTP-server en file watcher in 1x.
#
# Gebruik:
#   ./start_dev.sh                    # start alles
#   ./start_dev.sh /pad/naar/project  # met projectpad
#   ./start_dev.sh stop               # stop alles
#   ./start_dev.sh status             # check status
# ============================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

FTP_LOG="/tmp/amiga_ftp_server.log"
WATCH_LOG="/tmp/amiga_watch.log"
PID_FILE="/tmp/amiga_dev.pids"

# Default project directory
PROJECT_DIR="${1:-$SCRIPT_DIR}"
ACTION="$1"

stop_all() {
    echo "Stoppen van alle Amiga dev processen..."
    if [ -f "$PID_FILE" ]; then
        while IFS= read -r pid; do
            if kill -0 "$pid" 2>/dev/null; then
                echo "  Stop PID $pid"
                kill "$pid" 2>/dev/null
            fi
        done < "$PID_FILE"
        rm -f "$PID_FILE"
    fi
    for pid in $(pgrep -f "python3 ftp_server.py" 2>/dev/null); do
        echo "  Stop FTP server PID $pid"
        sudo kill "$pid" 2>/dev/null
    done
    for pid in $(pgrep -f "watch_and_deploy.py" 2>/dev/null); do
        echo "  Stop watcher PID $pid"
        kill "$pid" 2>/dev/null
    done
    echo "Klaar."
    exit 0
}

status_all() {
    echo "=== Amiga Dev Status ==="
    echo ""
    # Check FTP via lsof op poort 21 (werkt ook voor sudo processen)
    FTP_INFO=$(sudo lsof -i :21 -P 2>/dev/null | grep LISTEN | head -1)
    if [ -n "$FTP_INFO" ]; then
        FTP_PID=$(echo "$FTP_INFO" | awk '{print $2}')
        echo "FTP-server:  DRAAIT (PID $FTP_PID, poort 21)"
    else
        echo "FTP-server:  GESTOPT"
    fi
    WATCH_PID=$(pgrep -f "watch_and_deploy.py" 2>/dev/null | head -1)
    if [ -n "$WATCH_PID" ]; then
        WATCH_DIR=$(ps -p "$WATCH_PID" -o args= 2>/dev/null | grep -o '/[^ ]*' | tail -1)
        echo "File watcher: DRAAIT (PID $WATCH_PID, $WATCH_DIR)"
    else
        echo "File watcher: GESTOPT"
    fi
    AMIGA_IP=$(grep '"host"' "$SCRIPT_DIR/watch_config.json" 2>/dev/null | head -1 | grep -o '[0-9.]*')
    if [ -n "$AMIGA_IP" ]; then
        if ping -c 1 -W 1 "$AMIGA_IP" >/dev/null 2>&1; then
            echo "Amiga:       BEREIKBAAR ($AMIGA_IP)"
        else
            echo "Amiga:       NIET BEREIKBAAR ($AMIGA_IP)"
        fi
    fi
    echo ""
    echo "Logbestanden:"
    echo "  FTP:    $FTP_LOG"
    echo "  Watch:  $WATCH_LOG"
    exit 0
}

case "$ACTION" in
    stop)
        stop_all
        ;;
    status)
        status_all
        ;;
    --help|-h)
        echo "Gebruik: $0 [project_pad|stop|status]"
        exit 0
        ;;
esac

# Oude processen opruimen (ook sudo processen)
for pid in $(pgrep -f "python3.*ftp_server" 2>/dev/null; pgrep -f "ftp_server" 2>/dev/null); do
    if [ -n "$pid" ] && [ "$pid" != "$$" ]; then
        echo "Oude FTP-server gestopt (PID $pid)"
        sudo kill -9 "$pid" 2>/dev/null
        sleep 1
    fi
done 2>/dev/null

# Wacht tot poort 21 vrij is
for i in 1 2 3 4 5; do
    if ! lsof -i :21 -P 2>/dev/null | grep -q LISTEN; then
        break
    fi
    echo "Wacht tot poort 21 vrij is... ($i)"
    sleep 1
done

# FTP server starten
echo "FTP-server starten op poort 21..."
sudo python3 "$SCRIPT_DIR/ftp_server.py" > "$FTP_LOG" 2>&1 &
FTP_PID=$!
echo "  PID: $FTP_PID"
echo "$FTP_PID" >> "$PID_FILE"
sleep 2

if kill -0 "$FTP_PID" 2>/dev/null; then
    echo "  OK!"
else
    echo "  FOUT! Check log: $FTP_LOG"
    cat "$FTP_LOG"
    exit 1
fi

# File watcher starten
if pgrep -f "watch_and_deploy.py" >/dev/null 2>&1; then
    echo "File watcher draait al."
else
    echo "File watcher starten voor: $PROJECT_DIR"
    python3 "$SCRIPT_DIR/watch_and_deploy.py" "$PROJECT_DIR" > "$WATCH_LOG" 2>&1 &
    WATCH_PID=$!
    echo "  PID: $WATCH_PID"
    echo "$WATCH_PID" >> "$PID_FILE"
    sleep 1
    if kill -0 "$WATCH_PID" 2>/dev/null; then
        echo "  OK!"
    else
        echo "  FOUT! Check log: $WATCH_LOG"
        cat "$WATCH_LOG"
        exit 1
    fi
fi

echo ""
echo "============================================"
echo "  AmiBlitz3 Dev Environment is ACTIEF!"
echo "============================================"
echo ""
echo "  FTP-server:  http://0.0.0.0:21"
echo "  File watcher: $PROJECT_DIR"
echo "  Amiga:       192.168.68.70"
echo ""
echo "  Logs:"
echo "    FTP:   tail -f $FTP_LOG"
echo "    Watch: tail -f $WATCH_LOG"
echo ""
echo "  Commando's:"
echo "    $0 stop    - stop alles"
echo "    $0 status  - toon status"
echo "============================================"
