import requests # type: ignore
import os
import tempfile

def TryDownload(url):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        # Get filename from URL or content-disposition
        filename = os.path.basename(url.split('?')[0])
        if 'content-disposition' in response.headers:
            content_disposition = response.headers['content-disposition']
            filename = content_disposition.split('filename=')[1].strip('"\'')
        
        # Save to temporary file
        temp_dir = tempfile.mkdtemp()
        filepath = os.path.join(temp_dir, filename)
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return filepath
    except Exception as e:
        raise Exception(f"Download failed: {str(e)}")