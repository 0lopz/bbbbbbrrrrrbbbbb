import os
import sys
import tempfile
import logging
from pathlib import Path
from flask import Flask, request, jsonify, render_template # type: ignore
from werkzeug.utils import secure_filename # type: ignore
from flask_cors import CORS  # type: ignore

# Set up project root path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configuration
app.config.update(
    UPLOAD_FOLDER=tempfile.mkdtemp(prefix='ratters_uploads_'),
    MAX_CONTENT_LENGTH=100 * 1024 * 1024,  # 100MB limit
    SECRET_KEY=os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-123'),
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
ALLOWED_EXTENSIONS = {'exe', 'pyc', 'jar', 'dll'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    logger.info("Received file upload request")
    
    # Check if file exists in request
    if 'file' not in request.files:
        logger.error("No file part in request")
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    
    # Check if file was selected
    if file.filename == '':
        logger.error("No file selected")
        return jsonify({'error': 'No selected file'}), 400
    
    # Check file extension
    if not allowed_file(file.filename):
        logger.error(f"Invalid file type: {file.filename}")
        return jsonify({'error': 'File type not allowed'}), 400
    
    try:
        # Secure filename and save temporarily
        filename = secure_filename(file.filename)
        upload_dir = app.config['UPLOAD_FOLDER']
        filepath = os.path.join(upload_dir, filename)
        file.save(filepath)
        logger.info(f"File saved temporarily to: {filepath}")
        
        # Simulate analysis (replace with actual analysis code)
        results = simulate_analysis(filepath)
        
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500
        
    finally:
        # Clean up temporary file
        if 'filepath' in locals() and os.path.exists(filepath):
            try:
                os.remove(filepath)
                logger.info(f"Removed temporary file: {filepath}")
            except Exception as e:
                logger.error(f"Error removing temp file: {str(e)}")

def simulate_analysis(filepath):
    """Simulate analysis results for demonstration"""
    return {
        'type': 'Windows Executable',
        'webhook': 'https://discord.com/api/webhooks/1234567890/abcdefghijklmnopqrstuvwxyz1234567890',
        'python_version': '3.9',
        'additional_info': {
            'file_size': f"{os.path.getsize(filepath) / 1024 / 1024:.2f} MB",
            'analysis_complete': True
        }
    }

if __name__ == '__main__':
    try:
        # Configuration
        port = int(os.getenv('PORT', 5000))
        host = os.getenv('HOST', '0.0.0.0')
        debug = os.getenv('FLASK_DEBUG', 'true').lower() == 'true'
        
        logger.info(f"Starting ratters.rip server on {host}:{port}")
        app.run(host=host, port=port, debug=debug)
        
    except Exception as e:
        logger.critical(f"Failed to start server: {str(e)}")
        raise