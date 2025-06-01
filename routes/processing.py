from flask import Blueprint, render_template, request, redirect, url_for, send_from_directory
from controllers.processing import handle_upload
from config import Config
import os

processing_bp = Blueprint('processing', __name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

@processing_bp.route('/')
def index():
    return render_template('index.html')

@processing_bp.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(url_for('processing.index', error='No file part'))
    file = request.files['file']
    if file.filename == '':
        return redirect(url_for('processing.index', error='No file selected'))
    if file and allowed_file(file.filename):
        output_filename, error = handle_upload(file, Config.UPLOAD_FOLDER)
        if error:
            return redirect(url_for('processing.index', error=error))
        return redirect(url_for('processing.result', filename=output_filename))
    return redirect(url_for('processing.index', error='Invalid file type'))

@processing_bp.route('/result/<filename>')
def result(filename):
    return render_template('result.html', filename=filename)

@processing_bp.route('/download/<filename>')
def download(filename):
    return send_from_directory(Config.UPLOAD_FOLDER, filename, as_attachment=True)
