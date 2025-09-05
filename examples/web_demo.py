#!/usr/bin/env python3
"""
Simple web demo interface for Video Processor.

This provides a basic Flask web interface to demonstrate video processing
capabilities in a browser-friendly format.
"""

import asyncio
import os
import tempfile
from pathlib import Path
from typing import Optional

try:
    from flask import Flask, jsonify, render_template_string, request
except ImportError:
    print("Flask not installed. Install with: uv add flask")
    exit(1)

from video_processor import ProcessorConfig, VideoProcessor
from video_processor.tasks import setup_procrastinate
from video_processor.tasks.compat import get_version_info

# Simple HTML template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Video Processor Demo</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .container { max-width: 800px; margin: 0 auto; }
        .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
        .success { background: #d4edda; color: #155724; }
        .error { background: #f8d7da; color: #721c24; }
        .info { background: #d1ecf1; color: #0c5460; }
        pre { background: #f8f9fa; padding: 10px; border-radius: 5px; }
        button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }
        button:hover { background: #0056b3; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎬 Video Processor Demo</h1>
        
        <div class="status info">
            <strong>System Information:</strong><br>
            Version: {{ version_info.version }}<br>
            Procrastinate: {{ version_info.procrastinate_version }}<br>
            Features: {{ version_info.features }}
        </div>
        
        <h2>Test Video Processing</h2>
        <button onclick="processTestVideo()">Create & Process Test Video</button>
        <button onclick="submitAsyncJob()">Submit Async Processing Job</button>
        <button onclick="getSystemInfo()">Refresh System Info</button>
        
        <div id="results"></div>
        
        <h2>Processing Logs</h2>
        <pre id="logs">Ready...</pre>
    </div>
    
    <script>
        function log(message) {
            const logs = document.getElementById('logs');
            logs.textContent += new Date().toLocaleTimeString() + ': ' + message + '\\n';
            logs.scrollTop = logs.scrollHeight;
        }
        
        function showResult(data, isError = false) {
            const results = document.getElementById('results');
            const className = isError ? 'error' : 'success';
            results.innerHTML = '<div class="status ' + className + '"><pre>' + JSON.stringify(data, null, 2) + '</pre></div>';
        }
        
        async function processTestVideo() {
            log('Starting test video processing...');
            try {
                const response = await fetch('/api/process-test', { method: 'POST' });
                const data = await response.json();
                if (response.ok) {
                    log('Test video processing completed successfully');
                    showResult(data);
                } else {
                    log('Test video processing failed: ' + data.error);
                    showResult(data, true);
                }
            } catch (error) {
                log('Request failed: ' + error);
                showResult({error: error.message}, true);
            }
        }
        
        async function submitAsyncJob() {
            log('Submitting async processing job...');
            try {
                const response = await fetch('/api/async-job', { method: 'POST' });
                const data = await response.json();
                if (response.ok) {
                    log('Async job submitted with ID: ' + data.job_id);
                    showResult(data);
                } else {
                    log('Async job submission failed: ' + data.error);
                    showResult(data, true);
                }
            } catch (error) {
                log('Request failed: ' + error);
                showResult({error: error.message}, true);
            }
        }
        
        async function getSystemInfo() {
            log('Refreshing system information...');
            try {
                const response = await fetch('/api/info');
                const data = await response.json();
                showResult(data);
                log('System info refreshed');
            } catch (error) {
                log('Failed to get system info: ' + error);
                showResult({error: error.message}, true);
            }
        }
    </script>
</body>
</html>
"""

app = Flask(__name__)


async def create_test_video(output_dir: Path) -> Path:
    """Create a simple test video for processing."""
    import subprocess
    
    video_file = output_dir / "web_demo_test.mp4"
    
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", "testsrc=duration=5:size=320x240:rate=15",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "30",
        str(video_file)
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg failed: {result.stderr}")
        return video_file
    except FileNotFoundError:
        raise RuntimeError("FFmpeg not found. Please install FFmpeg.")


@app.route('/')
def index():
    """Serve the demo web interface."""
    version_info = get_version_info()
    return render_template_string(HTML_TEMPLATE, version_info=version_info)


@app.route('/api/info')
def api_info():
    """Get system information."""
    return jsonify(get_version_info())


@app.route('/api/process-test', methods=['POST'])
def api_process_test():
    """Process a test video synchronously."""
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test video
            test_video = asyncio.run(create_test_video(temp_path))
            
            # Configure processor for fast processing
            config = ProcessorConfig(
                output_dir=temp_path / "outputs",
                output_formats=["mp4"],
                quality_preset="ultrafast",
                generate_thumbnails=True,
                generate_sprites=False,  # Skip sprites for faster demo
                enable_360_processing=False,  # Skip 360 for faster demo
            )
            
            # Process video
            processor = VideoProcessor(config)
            result = processor.process_video(test_video)
            
            return jsonify({
                "status": "success",
                "video_id": result.video_id,
                "encoded_files": len(result.encoded_files),
                "thumbnails": len(result.thumbnails),
                "processing_time": "< 30s (estimated)",
                "message": "Test video processed successfully!"
            })
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/async-job', methods=['POST'])
def api_async_job():
    """Submit an async processing job."""
    try:
        database_url = os.environ.get(
            'PROCRASTINATE_DATABASE_URL',
            'postgresql://video_user:video_password@postgres:5432/video_processor'
        )
        
        # Set up Procrastinate
        app_context = setup_procrastinate(database_url)
        
        # In a real application, you would:
        # 1. Accept file uploads
        # 2. Store them temporarily
        # 3. Submit processing jobs
        # 4. Return job IDs for status tracking
        
        # For demo, we'll just simulate job submission
        job_id = f"demo-job-{os.urandom(4).hex()}"
        
        return jsonify({
            "status": "submitted",
            "job_id": job_id,
            "queue": "video_processing",
            "message": "Job submitted to background worker",
            "note": "In production, this would submit a real Procrastinate job"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def main():
    """Run the web demo server."""
    port = int(os.environ.get('PORT', 8080))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    print(f"🌐 Starting Video Processor Web Demo on port {port}")
    print(f"📖 Open http://localhost:{port} in your browser")
    
    app.run(host='0.0.0.0', port=port, debug=debug)


if __name__ == '__main__':
    main()