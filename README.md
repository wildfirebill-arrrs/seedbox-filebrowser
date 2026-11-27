# Seedbox Filebrowser

A secure, self-hosted web-based file browser for seedboxes with video screenshot generation, MediaInfo metadata extraction, and BDInfo report parsing.

<p class="description">Web-based file manager for media directories featuring video screenshot capture, comprehensive media metadata extraction via MediaInfo, and BDInfo Blu-ray report parsing with auto-detection.</p>

<p><strong>Features:</strong></p>
<ul>
  <li>📁 Web-based file manager with responsive GUI</li>
  <li>📸 Video screenshot generation with folder-named files</li>
  <li>📊 MediaInfo extraction to .txt files</li>
  <li>📀 BDInfo report auto-detection and parsing</li>
  <li>🔒 Basic authentication via htpasswd</li>
  <li>🌙 Dark mode support</li>
  <li>🔄 Persistent login (Remember me)</li>
  <li>📊 Auto-detected BDInfo reports in directory views</li>
</ul>

<h2>Quick Start</h2>

### Prerequisites
- Docker
- Python 3.8+
- mediainfo
- ffmpeg

### Installation
```bash
# Install Python dependencies
pip install -r app/requirements.txt

# Start all services
chmod +x app/start.sh
./app/start.sh
```

### Configuration
Set environment variables:
- `BASE_DIR`: Root directory for file browsing (default: /srv)
- `MI_PORT`: MediaInfo API port (default: 18082)
- `SS_PORT`: Screenshot API port (default: 18083)
- `FB_PORT`: FileBrowser port (default: 18081)

### API Endpoints

**MediaInfo**
```
GET /api/mi?file=<path>
```
Returns JSON with raw mediainfo text and saves `.mediainfo.txt` next to the file.

**Screenshots**
```
GET /api/ss?file=<path>&n=6&width=1280&head=5&tail=5&fmt=jpg
```
Parameters:
- `n`: Number of screenshots (1-20)
- `width`: Screenshot width (320-3840)
- `head`: Seconds from start to skip
- `tail`: Seconds from end to skip
- `fmt`: Image format (jpg, png)

**BDInfo**
```
GET /api/bdinfo?file=<path>
```
Auto-detects and parses BDInfo reports from directory contents.

### Security
1. **Path traversal protection** - All file access validated against base directory
2. **Authentication** - Built-in FileBrowser user management with htpasswd
3. **Localhost binding** - All APIs bind to 127.0.0.1 only
4. **HTTPS** - Use reverse proxy for TLS

### Nginx Configuration
```nginx
server {
    listen 443 ssl;
    server_name yourdomain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://127.0.0.1:18081;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /api/mi {
        proxy_pass http://127.0.0.1:18082;
    }
    
    location /api/ss {
        proxy_pass http://127.0.0.1:18083;
    }
    
    location /__asp_ss__/ {
        alias /tmp/asp_screens/;
    }
}
```

<p class="license">License: MIT</p>

### Seedbox Installation

#### Default Installation Path
- Files are installed to `~/.apps/`
- Nginx config: `~/.apps/nginx/`
- FileBrowser data: `~/.apps/filebrowser/`
- Supervisor config: `~/.config/supervisor/`

#### One-Click Installation
1. Upload the `app/` directory contents to `~/seedbox-fb/`
2. Run: `supervisord -c ~/.config/supervisor/supervisord.conf`
3. Access: `https://yourdomain.com/seedbox-fb/`
4. Login with your account credentials

#### Manual Installation Steps
1. **Upload files** to your seedbox home directory
2. **Install Python deps**: `pip3 install flask waitress`
3. **Install supervisord** (if not present): `apt-get install supervisor`
4. **Start services**: `supervisord -c ~/.config/supervisor/supervisord.conf`
5. **Configure nginx**: Copy `seedbox-fb.conf` to `~/.apps/nginx/proxy.d/`
6. **Reload nginx**: `nginx -p ~/.apps/nginx/ -c nginx.conf -s reload`
7. **Access**: `https://yourseedbox.ip/seedbox-fb/`
8. **Login** with your account credentials

### Port Mapping
| Service | Port | Description |
|---------|------|-------------|
| FileBrowser GUI | 18081 | Main web interface |
| MediaInfo API | 18082 | Media metadata extraction |
| Screenshot API | 18083 | Video screenshot generation |

### HTTPS Setup
Use your seedbox's built-in reverse proxy (Nginx/Apache) to forward `https://yourdomain.com/seedbox-fb/` to `http://127.0.0.1:18081`.

### Troubleshooting
- Check logs: `tail -f ~/.seedbox-fb/logs/flask.log` or check your log system
- Service status: `supervisorctl -c ~/.config/supervisor/supervisord.conf status`
- If ports are busy, adjust `FIREBROWSER_PORT`, `MEDIAINFO_PORT`, `SCREENSHOT_PORT` env vars

### Port Mapping
| Service | Port | Description |
|---------|------|-------------|
| FileBrowser GUI | 18081 | Main web interface |
| MediaInfo API | 18082 | Media metadata extraction |
| Screenshot API | 18083 | Video screenshot generation |

### HTTPS Setup
Use your seedbox's built-in reverse proxy (Nginx/Apache) to forward `https://yourdomain.com/seedbox-fb/` to `http://127.0.0.1:18081`.

### Troubleshooting
- Check logs: `tail -f ~/.seedbox-fb/logs/flask.log` or check your log system
- Service status: `supervisorctl -c /home21/wildfirebill/.config/supervisor/supervisord.conf status`
- If ports are busy, adjust `FIREBROWSER_PORT`, `MEDIAINFO_PORT`, `SCREENSHOT_PORT` env vars