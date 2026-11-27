#!/bin/bash
# Seedbox Filebrowser Startup Script

set -e

BASE_DIR="${BASE_DIR:-/srv}"
MI_PORT="${MI_PORT:-18082}"
SS_PORT="${SS_PORT:-18083}"
FB_PORT="${FB_PORT:-18081}"

echo "Starting Seedbox Filebrowser..."
echo "Base directory: $BASE_DIR"
echo "MediaInfo API: port $MI_PORT"
echo "Screenshot API: port $SS_PORT"
echo "FileBrowser: port $FB_PORT"

# Start MediaInfo API
echo "Starting MediaInfo API..."
python3 /opt/seedbox-fb/asp-mediainfo.py "$BASE_DIR" $MI_PORT &

# Start Screenshot API
echo "Starting Screenshot API..."
python3 /opt/seedbox-fb/asp-screenshot.py "$BASE_DIR" $SS_PORT &

# Start Flask app
echo "Starting Flask app..."
python3 /opt/seedbox-fb/app.py &

# Start FileBrowser
echo "Starting FileBrowser..."
docker run -d --name filebrowser --restart unless-stopped \
  -v "$BASE_DIR:/srv" \
  -v /opt/seedbox-fb/data:/database \
  -p 127.0.0.1:$FB_PORT:80 \
  filebrowser/filebrowser:latest -d /database/filebrowser.db

echo "All services started!"
echo "Access: http://localhost:$FB_PORT"
echo "MediaInfo: http://localhost:$MI_PORT/api/mi?file=FILE"
echo "Screenshots: http://localhost:$SS_PORT/api/ss?file=FILE"