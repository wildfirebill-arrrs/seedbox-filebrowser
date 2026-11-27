import http.server, socketserver, urllib.parse, subprocess, json, os, sys, time, shutil, uuid, zipfile

PORT = int(sys.argv[2])
BASE_DIR = sys.argv[1]
OUT_ROOT = "/tmp/asp_screens"

def safe_join(base, rel):
    rel = rel.lstrip('/')
    full = os.path.abspath(os.path.join(base, rel))
    if not full.startswith(os.path.abspath(base)):
        return None
    return full

def ffprobe_meta(path):
    try:
        res = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', path], capture_output=True, text=True)
        dur = float(res.stdout.strip())
        return {'duration': dur, 'width': 1920, 'height': 1080}
    except:
        return {'duration': None, 'width': 1920, 'height': 1080}

def make_timestamps(duration, n, head, tail):
    if duration:
        start = head
        end = duration - tail
        step = (end - start) / (n - 1) if n > 1 else 0
        return [start + i * step for i in range(n)]
    return [i * 10 for i in range(n)]

def cleanup_old():
    try:
        now = time.time()
        for d in os.listdir(OUT_ROOT):
            p = os.path.join(OUT_ROOT, d)
            if os.path.isdir(p) and now - os.path.getmtime(p) > 3600:
                shutil.rmtree(p, ignore_errors=True)
    except:
        pass

class Handler(http.server.BaseHTTPRequestHandler):
    def _send(self, code, payload):
        b = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path != "/api/ss":
            self._send(404, {"error": "not found"})
            return

        qs = urllib.parse.parse_qs(parsed.query)
        rel = qs.get("file", [""])[0]
        n = int(qs.get("n", ["6"])[0] or 6)
        width = int(qs.get("width", ["1280"])[0] or 1280)
        head = int(qs.get("head", ["5"])[0] or 5)
        tail = int(qs.get("tail", ["5"])[0] or 5)
        fmt = (qs.get("fmt", ["jpg"])[0] or "jpg").lower()

        full = safe_join(BASE_DIR, rel)
        if not full or not os.path.isfile(full):
            self._send(400, {"error": "File not found"})
            return

        os.makedirs(OUT_ROOT, exist_ok=True)
        cleanup_old()

        token = uuid.uuid4().hex
        out_dir = os.path.join(OUT_ROOT, token)
        os.makedirs(out_dir, exist_ok=True)

        # Save screenshots in video's directory too
        video_dir = os.path.dirname(full)
        video_name = os.path.splitext(os.path.basename(full))[0]
        save_dir = os.path.join(video_dir, video_name + "_screenshots")
        os.makedirs(save_dir, exist_ok=True)

        # Parent folder name for prefix
        parent_folder = os.path.basename(video_dir) if video_dir else video_name

        meta = ffprobe_meta(full)
        dur = meta.get("duration")
        ts = make_timestamps(dur, n, head, tail)

        files = []
        for i, t in enumerate(ts, start=1):
            out_name = f"{parent_folder}-{i:02d}.{fmt}"
            out_path = os.path.join(out_dir, out_name)
            save_path = os.path.join(save_dir, out_name)
            vf = f"scale={width}:-2"
            cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error",
                   "-ss", f"{t:.3f}", "-i", full,
                   "-frames:v", "1", "-an",
                   "-vf", vf]
            if fmt in ("jpg", "jpeg"):
                cmd += ["-q:v", "2"]
            cmd += ["-y", out_path]
            try:
                subprocess.run(cmd, timeout=35, check=True)
                if os.path.isfile(out_path) and os.path.getsize(out_path) > 0:
                    files.append(out_name)
                    shutil.copy2(out_path, save_path)
            except Exception:
                pass

        if not files:
            shutil.rmtree(out_dir, ignore_errors=True)
            self._send(500, {"error": "Screenshot failed"})
            return

        # Create ZIP file
        zip_name = f"{parent_folder}-screenshots.zip"
        zip_path = os.path.join(out_dir, zip_name)
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for f in files:
                zf.write(os.path.join(out_dir, f), f)

        self._send(200, {
            "base": f"/__asp_ss__/{token}/",
            "files": files,
            "zip": zip_name,
            "save_dir": save_dir,
            "parent_folder": parent_folder,
            "params": {"n": n, "width": width, "head": head, "tail": tail, "fmt": fmt},
            "meta": meta
        })

socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(("127.0.0.1", PORT), Handler) as httpd:
    httpd.serve_forever()