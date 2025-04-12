import os
import json
import tempfile
from http import HTTPStatus
from backend.pybit import PyBitDecompiler

# Initialize decompiler
DECOMPILER = PyBitDecompiler()

def analyze_file(file_content, filename):
    """Handle file analysis with proper cleanup"""
    temp_path = None
    try:
        # Create temp file with proper extension
        ext = os.path.splitext(filename)[1].lower()
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp:
            temp.write(file_content)
            temp_path = temp.name
        
        # Analyze using PyBitDecompiler
        return DECOMPILER.analyze_file(temp_path)
        
    except Exception as e:
        return {'error': str(e)}
    finally:
        # Cleanup temp file
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except:
                pass

def lambda_handler(event, context):
    try:
        # Get binary file data
        file_content = event.get('body')
        if isinstance(file_content, str):
            file_content = file_content.encode('utf-8')
        
        # Get filename from headers
        filename = event.get('headers', {}).get('x-filename', 'uploaded_file')
        
        # Validate input
        if not file_content:
            raise ValueError("No file content provided")
        
        # Process file
        result = analyze_file(file_content, filename)
        
        if 'error' in result:
            raise Exception(result['error'])
            
        return {
            'statusCode': HTTPStatus.OK,
            'body': json.dumps(result),
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }
        }
        
    except Exception as e:
        return {
            'statusCode': HTTPStatus.INTERNAL_SERVER_ERROR,
            'body': json.dumps({'error': str(e)}),
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }
        }