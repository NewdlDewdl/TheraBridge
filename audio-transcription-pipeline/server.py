#!/usr/bin/env python3
"""
Audio Transcription Pipeline - Bridge Server
============================================

This server provides a REST API for the browser UI to interact with
the audio transcription pipeline.

API Endpoints:
- POST /api/upload - Upload audio file and start processing
- GET /api/status/{job_id} - Get processing status
- GET /api/results/{job_id} - Get processing results
- POST /api/cancel/{job_id} - Cancel processing

Usage:
    python server.py

Server will run on http://localhost:5000
"""

import os
import uuid
import time
import json
import threading
from pathlib import Path
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

# Import pipeline components
# NOTE: Uncomment and modify these imports based on actual pipeline structure
# from src.pipeline import TranscriptionPipeline
# from src.config import PipelineConfig

# ============================================
# Configuration
# ============================================

app = Flask(__name__)
CORS(app)  # Enable CORS for browser access

# Upload configuration
UPLOAD_FOLDER = Path('uploads')
UPLOAD_FOLDER.mkdir(exist_ok=True)
RESULTS_FOLDER = Path('results')
RESULTS_FOLDER.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {'mp3', 'wav', 'm4a', 'aac', 'ogg', 'flac', 'wma', 'aiff'}
MAX_FILE_SIZE = 200 * 1024 * 1024  # 200 MB

# Job storage (in-memory)
# NOTE: Replace with Redis or database for production
jobs = {}
jobs_lock = threading.Lock()


# ============================================
# Helper Functions
# ============================================

def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def update_job_status(job_id, status=None, step=None, progress=None, message=None, error=None):
    """Update job status in thread-safe manner."""
    with jobs_lock:
        if job_id in jobs:
            if status:
                jobs[job_id]['status'] = status
            if step:
                jobs[job_id]['step'] = step
            if progress is not None:
                jobs[job_id]['progress'] = progress
            if message:
                jobs[job_id]['message'] = message
            if error:
                jobs[job_id]['error'] = error
            jobs[job_id]['updated_at'] = datetime.now().isoformat()


def process_audio_file(job_id, file_path):
    """
    Process audio file through the transcription pipeline.

    This function runs in a background thread.
    """
    try:
        # Step 1: Uploading (already done, but mark as complete)
        update_job_status(job_id, status='processing', step='uploading', progress=10,
                         message='File uploaded successfully')
        time.sleep(0.5)

        # Step 2: Transcribing
        update_job_status(job_id, step='transcribing', progress=25,
                         message='Transcribing audio with Whisper API')

        # TODO: Call actual transcription pipeline
        # pipeline = TranscriptionPipeline()
        # transcript = pipeline.transcribe(file_path)

        # Simulate transcription (remove in production)
        time.sleep(3)
        update_job_status(job_id, progress=50, message='Transcription complete')

        # Step 3: Diarizing
        update_job_status(job_id, step='diarizing', progress=60,
                         message='Analyzing speakers with pyannote')

        # TODO: Call actual diarization
        # diarization = pipeline.diarize(file_path)

        # Simulate diarization (remove in production)
        time.sleep(3)
        update_job_status(job_id, progress=85, message='Diarization complete')

        # Step 4: Aligning
        update_job_status(job_id, step='aligning', progress=90,
                         message='Aligning transcript with speakers')

        # TODO: Call actual alignment
        # aligned = pipeline.align(transcript, diarization)

        # Simulate alignment (remove in production)
        time.sleep(2)

        # Generate mock results (replace with actual results)
        results = generate_mock_results()

        # Save results
        results_file = RESULTS_FOLDER / f"{job_id}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)

        # Mark as complete
        with jobs_lock:
            jobs[job_id]['status'] = 'completed'
            jobs[job_id]['step'] = 'aligning'
            jobs[job_id]['progress'] = 100
            jobs[job_id]['message'] = 'Processing complete'
            jobs[job_id]['results_file'] = str(results_file)
            jobs[job_id]['completed_at'] = datetime.now().isoformat()

        print(f"✅ Job {job_id} completed successfully")

    except Exception as e:
        print(f"❌ Job {job_id} failed: {str(e)}")
        update_job_status(job_id, status='failed', error=str(e),
                         message=f'Processing failed: {str(e)}')


def generate_mock_results():
    """
    Generate mock results for testing.

    TODO: Replace with actual pipeline results
    """
    return {
        "aligned_transcript": [
            {
                "speaker": "SPEAKER_00",
                "text": "Hello, how are you feeling today?",
                "start": 0.5,
                "end": 3.2
            },
            {
                "speaker": "SPEAKER_01",
                "text": "I've been feeling a bit anxious lately. There's a lot going on at work.",
                "start": 3.8,
                "end": 8.5
            },
            {
                "speaker": "SPEAKER_00",
                "text": "I understand. Can you tell me more about what's been happening at work?",
                "start": 9.0,
                "end": 13.4
            },
            {
                "speaker": "SPEAKER_01",
                "text": "Well, we have a big project deadline coming up, and I'm worried I won't be able to finish everything on time.",
                "start": 14.0,
                "end": 20.5
            }
        ],
        "performance": {
            "total_time": 8.5,
            "audio_duration": 21.0,
            "transcription_time": 3.2,
            "diarization_time": 3.5,
            "alignment_time": 1.8,
            "rtf": 0.40,
            "num_segments": 4,
            "num_speakers": 2
        }
    }


# ============================================
# API Endpoints
# ============================================

@app.route('/api/upload', methods=['POST'])
def upload_audio():
    """
    Upload audio file and start processing.

    Request: multipart/form-data with 'audio' file field
    Response: {"job_id": "uuid", "message": "..."}
    """
    # Validate request
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400

    file = request.files['audio']

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({
            'error': f'Invalid file type. Supported formats: {", ".join(ALLOWED_EXTENSIONS)}'
        }), 400

    # Check file size (approximate)
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)

    if file_size > MAX_FILE_SIZE:
        return jsonify({
            'error': f'File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)} MB'
        }), 413

    # Generate job ID
    job_id = str(uuid.uuid4())

    # Save file
    filename = secure_filename(file.filename)
    file_path = UPLOAD_FOLDER / f"{job_id}_{filename}"
    file.save(str(file_path))

    # Create job record
    with jobs_lock:
        jobs[job_id] = {
            'job_id': job_id,
            'filename': filename,
            'file_path': str(file_path),
            'file_size': file_size,
            'status': 'processing',
            'step': 'uploading',
            'progress': 0,
            'message': 'File uploaded, starting processing',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }

    # Start background processing
    thread = threading.Thread(target=process_audio_file, args=(job_id, file_path))
    thread.daemon = True
    thread.start()

    print(f"📁 Job {job_id} created: {filename} ({file_size / (1024*1024):.2f} MB)")

    return jsonify({
        'job_id': job_id,
        'message': 'File uploaded successfully'
    }), 200


@app.route('/api/status/<job_id>', methods=['GET'])
def get_status(job_id):
    """
    Get processing status for a job.

    Response: {
        "job_id": "uuid",
        "status": "processing|completed|failed",
        "step": "uploading|transcribing|diarizing|aligning",
        "progress": 0-100,
        "message": "...",
        "error": "..." (if failed)
    }
    """
    with jobs_lock:
        if job_id not in jobs:
            return jsonify({'error': 'Job not found'}), 404

        job = jobs[job_id]

        response = {
            'job_id': job['job_id'],
            'status': job['status'],
            'step': job['step'],
            'progress': job['progress'],
            'message': job.get('message', '')
        }

        if job['status'] == 'failed' and 'error' in job:
            response['error'] = job['error']

        return jsonify(response), 200


@app.route('/api/results/<job_id>', methods=['GET'])
def get_results(job_id):
    """
    Get processing results for a completed job.

    Response: {
        "job_id": "uuid",
        "aligned_transcript": [...],
        "performance": {...}
    }
    """
    with jobs_lock:
        if job_id not in jobs:
            return jsonify({'error': 'Job not found'}), 404

        job = jobs[job_id]

        if job['status'] != 'completed':
            return jsonify({
                'error': f'Job not completed. Current status: {job["status"]}'
            }), 400

        # Load results from file
        results_file = job.get('results_file')
        if not results_file or not os.path.exists(results_file):
            return jsonify({'error': 'Results file not found'}), 404

        with open(results_file, 'r') as f:
            results = json.load(f)

        # Add job ID to results
        results['job_id'] = job_id

        return jsonify(results), 200


@app.route('/api/cancel/<job_id>', methods=['POST'])
def cancel_job(job_id):
    """
    Cancel a processing job.

    Response: {"message": "...", "job_id": "uuid"}
    """
    with jobs_lock:
        if job_id not in jobs:
            return jsonify({'error': 'Job not found'}), 404

        job = jobs[job_id]

        if job['status'] == 'completed':
            return jsonify({'error': 'Job already completed'}), 400

        if job['status'] == 'failed':
            return jsonify({'error': 'Job already failed'}), 400

        # Mark as cancelled (graceful cancellation)
        job['status'] = 'cancelled'
        job['message'] = 'Processing cancelled by user'
        job['cancelled_at'] = datetime.now().isoformat()

        # TODO: Actually stop the processing thread
        # This requires more sophisticated thread management

        print(f"🛑 Job {job_id} cancelled")

        return jsonify({
            'message': 'Job cancelled successfully',
            'job_id': job_id
        }), 200


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    }), 200


@app.route('/')
def index():
    """Serve API documentation."""
    return jsonify({
        'name': 'Audio Transcription Pipeline API',
        'version': '1.0.0',
        'endpoints': {
            'POST /api/upload': 'Upload audio file',
            'GET /api/status/{job_id}': 'Get processing status',
            'GET /api/results/{job_id}': 'Get results',
            'POST /api/cancel/{job_id}': 'Cancel processing',
            'GET /api/health': 'Health check'
        }
    }), 200


# ============================================
# Main
# ============================================

if __name__ == '__main__':
    print("""
    ╔════════════════════════════════════════════════════════╗
    ║  Audio Transcription Pipeline - Bridge Server         ║
    ║                                                        ║
    ║  Server running on: http://localhost:5000             ║
    ║  UI should connect to this address                    ║
    ║                                                        ║
    ║  Endpoints:                                           ║
    ║    POST /api/upload      - Upload audio file          ║
    ║    GET  /api/status/{id} - Get processing status      ║
    ║    GET  /api/results/{id} - Get results               ║
    ║    POST /api/cancel/{id} - Cancel processing          ║
    ║    GET  /api/health      - Health check               ║
    ║                                                        ║
    ║  Press Ctrl+C to stop                                 ║
    ╚════════════════════════════════════════════════════════╝
    """)

    # Run server
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        threaded=True
    )
