import http.server, socketserver, urllib.parse, subprocess, json, os, sys

PORT = int(sys.argv[2])
BASE_DIR = sys.argv[1]

def safe_join(base, rel):
    rel = rel.lstrip('/')
    full = os.path.abspath(os.path.join(base, rel))
    if not full.startswith(os.path.abspath(base)):
        return None
    return full

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path != '/api/mi':
            self.send_response(404)
            self.end_headers()
            return
        
        query = urllib.parse.parse_qs(parsed.query)
        file_path = query.get('file', [''])[0]
        full_path = safe_join(BASE_DIR, file_path)
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        
        if not full_path or not os.path.isfile(full_path):
            self.wfile.write(json.dumps({"error": "File not found"}).encode('utf-8'))
            return
        
        try:
            res_text = subprocess.run(['mediainfo', full_path], capture_output=True, text=True)
            raw_text = res_text.stdout
            
            # Save mediainfo to txt file using filename
            video_dir = os.path.dirname(full_path)
            video_name = os.path.basename(full_path)
            txt_name = video_name + ".mediainfo.txt"
            txt_path = os.path.join(video_dir, txt_name)
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(raw_text)
            
            res_json = subprocess.run(['mediainfo', '--Output=JSON', full_path], capture_output=True, text=True)
            media = None
            try:
                media = json.loads(res_json.stdout)
            except:
                pass
            
            if media is None:
                lines = raw_text.split('\n')
                tracks = []
                current_track = {}
                for line in lines:
                    line = line.strip()
                    if not line:
                        if current_track:
                            tracks.append(current_track)
                            current_track = {}
                        continue
                    if ':' not in line and '@type' not in current_track:
                        current_track['@type'] = line
                    elif ':' in line:
                        k, v = line.split(':', 1)
                        current_track[k.strip()] = v.strip()
                if current_track:
                    tracks.append(current_track)
                media = {"media": {"track": tracks}}
            
            payload = {"raw_text": raw_text, "txt_file": txt_name, "txt_path": txt_path, **media}
            self.wfile.write(json.dumps(payload).encode('utf-8'))
        except Exception as e:
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))

socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(("127.0.0.1", PORT), Handler) as httpd:
    httpd.serve_forever()