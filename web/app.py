"""
Web-käyttöliittymä äänenlaatu-analysaattorille
"""

# Eventlet monkey-patch MUST be first
import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import os
import sys
import json
import subprocess
import re
import time
from pathlib import Path
from datetime import datetime
import glob

app = Flask(__name__)
app.config['SECRET_KEY'] = 'audio-quality-analyzer-secret-2026'
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max upload
CORS(app)

# SocketIO with eventlet async mode for background tasks
socketio = SocketIO(
    app, 
    cors_allowed_origins="*",
    async_mode='eventlet',
    logger=True,
    engineio_logger=False
)

# Global state
analysis_status = {
    'running': False,
    'current_file': None,
    'progress': 0,
    'total_files': 0,
    'results': []
}


def emit_progress(message, progress=None):
    """Emit progress update via WebSocket"""
    if progress is not None:
        analysis_status['progress'] = progress
    
    data = {
        'message': message,
        'progress': analysis_status['progress'],
        'total': analysis_status['total_files'],
        'current_file': analysis_status['current_file']
    }
    
    # Emit from background thread - broadcasts to all clients by default
    try:
        socketio.emit('progress', data, namespace='/')
        print(f"📊 Progress emitted: {message} ({progress}/{analysis_status['total_files']})")
    except Exception as e:
        print(f"❌ Error emitting progress: {e}")
    
    # Small delay to ensure message is sent (eventlet sleep)
    eventlet.sleep(0.1)


def parse_analyzer_output(line):
    """Parse analyzer output and extract progress information"""
    # Look for analysis phase indicators
    if "Analyzing:" in line:
        # Extract filename from "Analyzing: filename.wav"
        match = re.search(r'Analyzing:\s+(.+)$', line)
        if match:
            return {'type': 'file_start', 'filename': match.group(1).strip()}
    
    elif "DSP Analysis" in line:
        return {'type': 'phase', 'phase': 'DSP Analysis'}
    
    elif "GPU Feature Extraction" in line:
        return {'type': 'phase', 'phase': 'GPU Feature Extraction'}
    
    elif "AI Quality Assessment" in line:
        return {'type': 'phase', 'phase': 'AI Quality Assessment'}
    
    elif "Generating recommendations" in line:
        return {'type': 'phase', 'phase': 'Recommendations'}
    
    elif "Generating LLM explanation" in line:
        return {'type': 'phase', 'phase': 'LLM Explanation'}
    
    elif "Generating Excel report" in line:
        return {'type': 'phase', 'phase': 'Excel Report'}
    
    elif "Generating HTML summary" in line:
        return {'type': 'phase', 'phase': 'HTML Summary'}
    
    elif "✓" in line and "exported" in line.lower():
        return {'type': 'complete'}
    
    return None


def analyze_files_async(filepaths):
    """Run analysis in analyzer container via docker exec"""
    global analysis_status
    
    try:
        analysis_status['running'] = True
        analysis_status['total_files'] = len(filepaths)
        analysis_status['progress'] = 0
        analysis_status['results'] = []
        
        emit_progress(f"Aloitetaan {len(filepaths)} tiedoston analyysi...", 0)
        
        # Build command for analyzer container
        # Use absolute paths within container (/app/input_folder/file.wav)
        files_args = []
        for filepath in filepaths:
            # Ensure path starts with /app
            if not filepath.startswith('/app/'):
                filepath = f'/app/{filepath}' if not filepath.startswith('/') else filepath
            files_args.extend(['--input', filepath])
        
        cmd = [
            'docker', 'exec', 
            'audio-quality-analyzer-gpu',
            'python3', 'src/main.py'
        ] + files_args
        
        print(f"🚀 Executing: {' '.join(cmd)}")
        
        # Run analysis in analyzer container
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        current_file_idx = 0
        current_phase = None
        
        # Stream output and parse progress
        for line in process.stdout:
            line = line.strip()
            if not line:
                continue
            
            print(f"[Analyzer] {line}")
            
            parsed = parse_analyzer_output(line)
            if parsed:
                if parsed['type'] == 'file_start':
                    current_file_idx += 1
                    filename = parsed['filename']
                    analysis_status['current_file'] = filename
                    emit_progress(f"Analysoidaan: {filename}", current_file_idx - 1)
                
                elif parsed['type'] == 'phase':
                    current_phase = parsed['phase']
                    if analysis_status['current_file']:
                        emit_progress(
                            f"{analysis_status['current_file']}: {current_phase}", 
                            current_file_idx - 0.5
                        )
                
                elif parsed['type'] == 'complete':
                    emit_progress(f"✓ Valmis: {analysis_status['current_file']}", current_file_idx)
        
        process.wait()
        
        if process.returncode == 0:
            emit_progress("✓ Analyysi valmis!", len(filepaths))
        else:
            emit_progress(f"✗ Virhe: Analyysi epäonnistui (exit code {process.returncode})", len(filepaths))
        
    except Exception as e:
        print(f"❌ Error in analyze_files_async: {e}")
        import traceback
        traceback.print_exc()
        emit_progress(f"✗ Virhe: {str(e)}", 0)
    
    finally:
        analysis_status['running'] = False
        analysis_status['current_file'] = None


@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')


@app.route('/api/status')
def get_status():
    """Get current analysis status"""
    return jsonify(analysis_status)


@app.route('/api/files')
def list_files():
    """List audio files in input folder"""
    input_folder = '/app/input_folder'
    audio_extensions = ['.mp3', '.wav', '.flac', '.m4a', '.ogg', '.aac']
    
    files = []
    for ext in audio_extensions:
        for filepath in Path(input_folder).glob(f'*{ext}'):
            stat = filepath.stat()
            files.append({
                'name': filepath.name,
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
            })
    
    return jsonify({'files': sorted(files, key=lambda x: x['name'])})


@app.route('/api/analyze', methods=['POST'])
def start_analysis():
    """Start analysis for selected files"""
    if analysis_status['running']:
        return jsonify({'error': 'Analysis already running'}), 400
    
    data = request.json
    selected_files = data.get('files', [])
    
    if not selected_files:
        return jsonify({'error': 'No files selected'}), 400
    
    # Build full paths
    filepaths = [os.path.join('/app/input_folder', f) for f in selected_files]
    
    # Start analysis in background thread using socketio.start_background_task
    socketio.start_background_task(analyze_files_async, filepaths)
    
    return jsonify({'message': 'Analysis started', 'files': len(selected_files)})


@app.route('/api/reports')
def list_reports():
    """List available reports"""
    output_folder = '/app/output'
    
    reports = {
        'html': [],
        'excel': [],
        'text': []
    }
    
    # HTML reports
    for filepath in Path(output_folder).glob('audio_quality_summary_*.html'):
        stat = filepath.stat()
        reports['html'].append({
            'name': filepath.name,
            'size': stat.st_size,
            'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
            'path': f'/api/report/html/{filepath.name}'
        })
    
    # Excel reports
    for filepath in Path(output_folder).glob('audio_quality_report_*.xlsx'):
        stat = filepath.stat()
        reports['excel'].append({
            'name': filepath.name,
            'size': stat.st_size,
            'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
            'path': f'/api/report/excel/{filepath.name}'
        })
    
    # Text reports
    reports_dir = Path(output_folder) / 'reports'
    if reports_dir.exists():
        for filepath in reports_dir.glob('*.txt'):
            stat = filepath.stat()
            reports['text'].append({
                'name': filepath.name,
                'size': stat.st_size,
                'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'path': f'/api/report/text/{filepath.name}'
            })
    
    # Sort by creation time (newest first)
    for key in reports:
        reports[key] = sorted(reports[key], key=lambda x: x['created'], reverse=True)
    
    return jsonify(reports)


@app.route('/api/report/html/<filename>')
def download_html_report(filename):
    """Download HTML report"""
    filepath = os.path.join('/app/output', filename)
    if not os.path.exists(filepath):
        return jsonify({'error': 'Report not found'}), 404
    return send_file(filepath, mimetype='text/html')


@app.route('/api/report/excel/<filename>')
def download_excel_report(filename):
    """Download Excel report"""
    filepath = os.path.join('/app/output', filename)
    if not os.path.exists(filepath):
        return jsonify({'error': 'Report not found'}), 404
    return send_file(filepath, as_attachment=True)


@app.route('/api/report/text/<filename>')
def download_text_report(filename):
    """Download text report"""
    filepath = os.path.join('/app/output/reports', filename)
    if not os.path.exists(filepath):
        return jsonify({'error': 'Report not found'}), 404
    return send_file(filepath, mimetype='text/plain')


@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection"""
    emit('connected', {'message': 'Connected to analyzer'})


@socketio.on('request_status')
def handle_status_request():
    """Handle status request"""
    emit('status', analysis_status)


if __name__ == '__main__':
    print("🚀 Starting Audio Quality Analyzer Web Interface...")
    print("📡 Server: http://localhost:5000")
    print("🎙️ Ready to analyze audio files!")
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)
