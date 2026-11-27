# Seedbox Filebrowser

A secure, self-hosted filebrowser for seedboxes with:
- 📺 Video screenshot generation
- 📊 MediaInfo extraction to text files
- 🖥️ Web-based GUI
- 🔒 Security features

## Quick Start

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
Returns JSON with raw mediainfo text and parsed media data.

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

### Security

1. **Path traversal protection** - All file access validated against base directory
2. **Authentication** - Built-in FileBrowser user management
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