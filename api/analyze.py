from http import HTTPStatus
import json
import tempfile
import os
from pybit import PyBitDecompiler  # Your analyzer class

def analyze_file(file_content):
    """Your analysis logic here"""
    decompiler = PyBitDecompiler()
    with tempfile.NamedTemporaryFile(delete=False) as temp:
        temp.write(file_content)
        temp_path = temp.name
    try:
        return decompiler.analyze_file(temp_path)
    finally:
        os.unlink(temp_path)

def lambda_handler(event, context):
    try:
        # Get uploaded file
        file_content = event.body.encode() if isinstance(event.body, str) else event.body
        if not file_content:
            return {
                'statusCode': HTTPStatus.BAD_REQUEST,
                'body': json.dumps({'error': 'No file uploaded'})
            }
        
        # Analyze file
        result = analyze_file(file_content)
        return {
            'statusCode': HTTPStatus.OK,
            'body': json.dumps(result)
        }
    except Exception as e:
        return {
            'statusCode': HTTPStatus.INTERNAL_SERVER_ERROR,
            'body': json.dumps({'error': str(e)})
        }