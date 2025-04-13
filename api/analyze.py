import os
import json
import tempfile
from http import HTTPStatus
from backend.pybit import PyBitDecompiler

DECOMPILER = PyBitDecompiler()

def analyze_file(file_path):
    """Analyze file with proper error handling"""
    try:
        return DECOMPILER.analyze_file(file_path)
    except Exception as e:
        return {'error': f"Analysis failed: {str(e)}"}

def lambda_handler(event, context):
    # Validate request
    if not event.get('body'):
        return {
            'statusCode': HTTPStatus.BAD_REQUEST,
            'body': json.dumps({'error': 'No file content provided'}),
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }
        }

    # Process file
    temp_path = None
    try:
        # Handle binary/base64
        file_content = event['body']
        if isinstance(file_content, str):
            if file_content.startswith('Request En'):  # Catch malformed requests
                raise ValueError("Invalid request format")
            file_content = file_content.encode()

        # Create temp file
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(file_content)
            temp_path = tmp.name

        # Get filename
        filename = event.get('headers', {}).get('x-filename', 'uploaded_file')

        # Analyze
        result = analyze_file(temp_path)
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
    finally:
        # Cleanup
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass