import os
from werkzeug.utils import secure_filename
from services.processing import process_file

def handle_upload(file, output_dir):
    if not file or file.filename == '':
        return None, "No file selected"
    filename = secure_filename(file.filename)
    input_path = os.path.join(output_dir, f"input_{filename}")
    file.save(input_path)
    
    output_filename = f"processed_{filename}"
    output_path = os.path.join(output_dir, output_filename)
    
    try:
        process_file(input_path, output_path)
        return output_filename, None
    except Exception as e:
        return None, str(e)
