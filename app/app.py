from flask import Flask, send_from_directory, request, jsonify, render_template
import os
import subprocess
import re

app = Flask(__name__)
BASE_DIR = os.environ.get('BASE_DIR', '/home21/wildfirebill')
STATIC_DIR = os.path.join(os.path.dirname(__file__), 'static')

def safe_path(path):
    full = os.path.abspath(os.path.join(BASE_DIR, path.lstrip('/')))
    if not full.startswith(os.path.abspath(BASE_DIR)):
        return None
    return full

def parse_bdinfo_report(text):
    """Parse a BDInfo report text file and extract key information."""
    data = {
        'disc_label': None,
        'disc_size': None,
        'protection': None,
        'bd_info_version': None,
        'playlist': None,
        'video': [],
        'audio': [],
        'subtitles': [],
        'chapters': [],
        'quick_summary': None,
        'raw': text
    }
    
    lines = text.split('\n')
    
    # Extract disc label
    for line in lines:
        m = re.search(r'Disc Label:\s*(.+)', line, re.IGNORECASE)
        if m:
            data['disc_label'] = m.group(1).strip()
            break
    
    # Extract disc size
    for line in lines:
        m = re.search(r'Disc Size:\s*([\d.]+)\s*(GB|Bytes)', line, re.IGNORECASE)
        if m:
            data['disc_size'] = m.group(0).strip()
            break
    
    # Extract protection
    for line in lines:
        m = re.search(r'Protection:\s*(.+)', line, re.IGNORECASE)
        if m:
            data['protection'] = m.group(1).strip()
            break
    
    # Extract BDInfo version
    for line in lines:
        m = re.search(r'BDInfo\s*([\d.]+)', line, re.IGNORECASE)
        if m:
            data['bd_info_version'] = m.group(1).strip()
            break
    
    # Extract playlist
    for line in lines:
        m = re.search(r'Playlist:\s*(\d+)\s*\(([\d.]+)\s*GB\)', line, re.IGNORECASE)
        if m:
            data['playlist'] = {'number': m.group(1), 'size': m.group(2) + ' GB'}
            break
    
    # Extract Quick Summary block
    in_quick = False
    quick_lines = []
    for line in lines:
        if 'Quick Summary' in line or 'QUICK SUMMARY' in line:
            in_quick = True
            continue
        if in_quick:
            if line.strip() == '' or '---' in line:
                if quick_lines:
                    break
                continue
            quick_lines.append(line.rstrip())
    if quick_lines:
        data['quick_summary'] = '\n'.join(quick_lines)
    
    # Parse video streams
    in_video = False
    for line in lines:
        if re.search(r'Video:', line, re.IGNORECASE) and not in_video:
            in_video = True
            continue
        if in_video:
            if line.strip() == '':
                in_video = False
                continue
            m = re.match(r'\s*(\d+)\s+(.+)', line)
            if m:
                data['video'].append({'stream': m.group(1), 'info': m.group(2).strip()})
    
    # Parse audio streams
    in_audio = False
    for line in lines:
        if re.search(r'Audio:', line, re.IGNORECASE) and not in_audio:
            in_audio = True
            continue
        if in_audio:
            if line.strip() == '':
                in_audio = False
                continue
            m = re.match(r'\s*(\d+)\s+(.+)', line)
            if m:
                data['audio'].append({'stream': m.group(1), 'info': m.group(2).strip()})
    
    # Parse subtitle streams
    in_subs = False
    for line in lines:
        if re.search(r'Subtitle|Subtitles:', line, re.IGNORECASE) and not in_subs:
            in_subs = True
            continue
        if in_subs:
            if line.strip() == '':
                in_subs = False
                continue
            m = re.match(r'\s*(\d+)\s+(.+)', line)
            if m:
                data['subtitles'].append({'stream': m.group(1), 'info': m.group(2).strip()})
    
    # Parse chapters
    in_chapters = False
    for line in lines:
        if re.search(r'Chapter|Chapters:', line, re.IGNORECASE) and not in_chapters:
            in_chapters = True
            continue
        if in_chapters:
            if line.strip() == '':
                in_chapters = False
                continue
            m = re.match(r'\s*(\d+)\s+(.+)', line)
            if m:
                data['chapters'].append({'chapter': m.group(1), 'info': m.group(2).strip()})
    
    return data

def find_bdinfo_report(dir_path):
    """Find and parse a BDInfo report in a directory."""
    if not os.path.isdir(dir_path):
        return None
    bdinfo_patterns = ['bdinfo', 'bd_info', 'BDINFO', 'BD Info', 'bd-info']
    for item in os.listdir(dir_path):
        item_lower = item.lower()
        if item_lower.endswith('.txt'):
            # Check if filename looks like a BDInfo report
            if any(p.lower() in item_lower for p in bdinfo_patterns):
                item_path = os.path.join(dir_path, item)
                try:
                    with open(item_path, 'r', encoding='utf-8', errors='ignore') as f:
                        text = f.read()
                    parsed = parse_bdinfo_report(text)
                    if parsed.get('disc_label') or parsed.get('playlist') or parsed.get('video'):
                        return {'filename': item, 'parsed': parsed}
                except:
                    pass
    return None

@app.route('/')
def index():
    return send_from_directory(STATIC_DIR, 'index.html')

@app.route('/api/list')
def list_files():
    path = request.args.get('path', '/')
    full_path = safe_path(path)
    if not full_path or not os.path.isdir(full_path):
        return jsonify({'error': 'Directory not found'}), 404
    
    files = []
    try:
        for item in os.listdir(full_path):
            item_path = os.path.join(full_path, item)
            is_dir = os.path.isdir(item_path)
            is_video = item.lower().endswith(('.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m2ts', '.ts'))
            files.append({
                'name': item,
                'path': os.path.join(path, item).replace('\\', '/'),
                'isDir': is_dir,
                'isVideo': is_video,
                'size': os.path.getsize(item_path) if not is_dir else 0
            })
    except PermissionError:
        return jsonify({'error': 'Permission denied'}), 403
    
    files.sort(key=lambda x: (not x['isDir'], x['name'].lower()))
    
    # Auto-detect BDInfo report in this directory
    bdinfo = find_bdinfo_report(full_path)
    
    return jsonify({'files': files, 'bdinfo': bdinfo})

@app.route('/api/mi')
def mediainfo():
    filepath = request.args.get('file', '')
    full_path = safe_path(filepath)
    if not full_path or not os.path.isfile(full_path):
        return jsonify({'error': 'File not found'}), 404
    
    result = subprocess.run(['mediainfo', full_path], capture_output=True, text=True)
    raw_text = result.stdout
    
    # Save mediainfo to txt file using filename
    video_dir = os.path.dirname(full_path)
    video_name = os.path.basename(full_path)
    txt_name = video_name + ".mediainfo.txt"
    txt_path = os.path.join(video_dir, txt_name)
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(raw_text)
    
    return jsonify({'raw_text': raw_text, 'txt_file': txt_name, 'txt_path': txt_path})

@app.route('/api/bdinfo')
def bdinfo():
    filepath = request.args.get('file', '')
    full_path = safe_path(filepath)
    if not full_path or not os.path.isfile(full_path):
        return jsonify({'error': 'File not found'}), 404
    
    try:
        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
            raw_text = f.read()
    except Exception as e:
        return jsonify({'error': f'Cannot read file: {str(e)}'}), 500
    
    parsed = parse_bdinfo_report(raw_text)
    
    # Save parsed bdinfo to txt file
    video_dir = os.path.dirname(full_path)
    bd_name = os.path.basename(full_path)
    txt_name = bd_name + ".bdinfo.txt"
    txt_path = os.path.join(video_dir, txt_name)
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(raw_text)
    
    return jsonify({
        'parsed': parsed,
        'txt_file': txt_name,
        'txt_path': txt_path
    })

if __name__ == '__main__':
    from waitress import serve
    serve(app, host='127.0.0.1', port=13030)