"""
Flask Web Server for Online Image Lab
Handles file uploads and image processing requests
Supports persistent image sessions for multiple operations
"""

import os
import time
import uuid
import shutil
import cv2
import atexit
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, session, jsonify
from werkzeug.utils import secure_filename
from apscheduler.schedulers.background import BackgroundScheduler
from processor import ImageProcessor
from config import Config

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Ensure upload directories exist
for folder in [app.config['UPLOAD_FOLDER'], app.config['PROCESSED_FOLDER'], 
               app.config['WORKING_FOLDER'], app.config['PREVIEW_FOLDER']]:
    os.makedirs(folder, exist_ok=True)


def cleanup_old_files():
    """Delete files older than the configured max age."""
    folders = [
        app.config['UPLOAD_FOLDER'],
        app.config['PROCESSED_FOLDER'],
        app.config['WORKING_FOLDER'],
        app.config['PREVIEW_FOLDER']
    ]
    
    current_time = time.time()
    max_age = app.config['FILE_MAX_AGE_SECONDS']
    
    print(f"Running cleanup task. Max age: {max_age}s")
    
    for folder in folders:
        if not os.path.exists(folder):
            continue
            
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            # Skip hidden files like .gitkeep
            if filename.startswith('.'):
                continue
                
            try:
                file_age = current_time - os.path.getmtime(file_path)
                if file_age > max_age:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        print(f"Deleted old file: {file_path}")
            except Exception as e:
                print(f"Error deleting {file_path}: {e}")

# Initialize and start scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(func=cleanup_old_files, trigger="interval", minutes=app.config['CLEANUP_INTERVAL_MINUTES'])
scheduler.start()

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())


def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def generate_unique_filename(original_filename: str, extension: str = None) -> str:
    if extension:
        ext = extension
    else:
        ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else 'png'
    return f"{uuid.uuid4().hex}.{ext}"


def create_preview(source_path: str, preview_filename: str) -> str:
    """Create a smaller preview image for faster loading."""
    img = cv2.imread(source_path)
    if img is None:
        return None
    
    h, w = img.shape[:2]
    max_size = app.config['PREVIEW_MAX_SIZE']
    if max(h, w) > max_size:
        scale = max_size / max(h, w)
        new_w, new_h = int(w * scale), int(h * scale)
        img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
    
    preview_path = os.path.join(app.config['PREVIEW_FOLDER'], preview_filename)
    cv2.imwrite(preview_path, img, [cv2.IMWRITE_JPEG_QUALITY, 85])
    return url_for('static', filename=f'preview/{preview_filename}')


@app.route('/')
def index():
    original_image = session.get('original_preview')
    current_image = session.get('current_preview')
    operations_history = session.get('operations_history', [])
    
    return render_template('index.html', 
                           original_image=original_image,
                           processed_image=current_image,
                           processed_filename=session.get('processed_filename'),
                           operations_history=operations_history,
                           has_session=original_image is not None)


@app.route('/upload', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({'success': False, 'error': 'No file uploaded'})
    
    file = request.files['image']
    
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'})
    
    if not allowed_file(file.filename):
        return jsonify({'success': False, 'error': 'Invalid file type'})
    
    clear_session_files()
    
    original_filename = generate_unique_filename(secure_filename(file.filename))
    original_path = os.path.join(app.config['UPLOAD_FOLDER'], original_filename)
    file.save(original_path)
    
    working_filename = f"working_{original_filename}"
    working_path = os.path.join(app.config['WORKING_FOLDER'], working_filename)
    shutil.copy(original_path, working_path)
    
    # Create preview images
    preview_original = f"preview_orig_{original_filename}.jpg"
    preview_working = f"preview_work_{original_filename}.jpg"
    original_preview_url = create_preview(original_path, preview_original)
    working_preview_url = create_preview(working_path, preview_working)
    
    session['original_image'] = url_for('static', filename=f'uploads/{original_filename}')
    session['original_filename'] = original_filename
    session['original_preview'] = original_preview_url
    session['current_image'] = url_for('static', filename=f'working/{working_filename}')
    session['current_filename'] = working_filename
    session['current_preview'] = working_preview_url
    session['operations_history'] = []
    session['image_history'] = [working_filename]
    session['preview_history'] = [preview_working]
    
    return jsonify({
        'success': True,
        'original_image': original_preview_url,
        'processed_image': working_preview_url,
        'message': 'Image uploaded successfully!'
    })


@app.route('/process', methods=['POST'])
def process_image():
    if 'current_filename' not in session:
        return jsonify({'success': False, 'error': 'Please upload an image first'})
    
    operation = request.form.get('operation', '')
    if not operation:
        return jsonify({'success': False, 'error': 'No operation selected'})
    
    current_filename = session['current_filename']
    current_path = os.path.join(app.config['WORKING_FOLDER'], current_filename)
    
    if not os.path.exists(current_path):
        clear_session_files()
        return jsonify({'success': False, 'error': 'Working image not found'})
    
    params = {}
    operation_display = operation.replace('_', ' ').title()
    target_ext = None
    
    try:
        if operation == 'resize':
            params['scale'] = float(request.form.get('scale', 100))
            operation_display = f"Resize ({params['scale']}%)"
        elif operation == 'rotate':
            params['angle'] = float(request.form.get('angle', 0))
            operation_display = f"Rotate ({params['angle']}°)"
        elif operation == 'brightness':
            params['value'] = int(request.form.get('brightness_value', 0))
            operation_display = f"Brightness ({'+' if params['value'] >= 0 else ''}{params['value']})"
        elif operation == 'blur_gaussian':
            params['kernel_size'] = int(request.form.get('gaussian_kernel', 5))
            operation_display = f"Gaussian Blur (k={params['kernel_size']})"
        elif operation == 'denoise_median':
            params['kernel_size'] = int(request.form.get('median_kernel', 5))
            operation_display = f"Median Denoise (k={params['kernel_size']})"
        elif operation == 'edge_sobel':
            params['ksize'] = int(request.form.get('sobel_ksize', 3))
            operation_display = f"Sobel Edge (k={params['ksize']})"
        elif operation == 'sharpen':
            params['strength'] = float(request.form.get('sharpen_strength', 1.0))
            operation_display = f"Sharpen ({params['strength']}x)"
        elif operation == 'convert':
            target_ext = request.form.get('format', 'png').lower()
            if target_ext not in app.config['ALLOWED_EXTENSIONS']:
                raise ValueError("Invalid target format")
            operation_display = f"Convert to {target_ext.upper()}"
    except (ValueError, TypeError) as e:
        return jsonify({'success': False, 'error': f'Invalid parameter: {str(e)}'})
    
    try:
        processor = ImageProcessor(current_path)
        processor.process(operation, params)
        
        # Determine new extension
        if target_ext:
            ext = target_ext
        else:
            ext = current_filename.rsplit('.', 1)[1] if '.' in current_filename else 'png'
            
        new_working_filename = f"working_{uuid.uuid4().hex}.{ext}"
        new_working_path = os.path.join(app.config['WORKING_FOLDER'], new_working_filename)
        processor.save(new_working_path)
        
        processed_filename = f"processed_{uuid.uuid4().hex}.{ext}"
        processed_path = os.path.join(app.config['PROCESSED_FOLDER'], processed_filename)
        shutil.copy(new_working_path, processed_path)
        
        # Create preview
        preview_filename = f"preview_{uuid.uuid4().hex}.jpg"
        preview_url = create_preview(new_working_path, preview_filename)
        
        session['current_image'] = url_for('static', filename=f'working/{new_working_filename}')
        session['current_filename'] = new_working_filename
        session['current_preview'] = preview_url
        session['processed_filename'] = processed_filename
        
        operations_history = session.get('operations_history', [])
        operations_history.append(operation_display)
        session['operations_history'] = operations_history
        
        image_history = session.get('image_history', [])
        image_history.append(new_working_filename)
        session['image_history'] = image_history
        
        preview_history = session.get('preview_history', [])
        preview_history.append(preview_filename)
        session['preview_history'] = preview_history
        
        return jsonify({
            'success': True,
            'processed_image': preview_url,
            'operation': operation_display,
            'operations_history': operations_history,
            'download_url': url_for('download_file', filename=processed_filename),
            'can_undo': len(image_history) > 1
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Processing error: {str(e)}'})


@app.route('/undo', methods=['POST'])
def undo_operation():
    image_history = session.get('image_history', [])
    operations_history = session.get('operations_history', [])
    preview_history = session.get('preview_history', [])
    
    if len(image_history) < 2:
        return jsonify({'success': False, 'error': 'Nothing to undo'})
    
    image_history.pop()
    preview_history.pop()
    removed_op = operations_history.pop() if operations_history else ''
    
    previous_filename = image_history[-1]
    previous_preview = preview_history[-1]
    previous_path = os.path.join(app.config['WORKING_FOLDER'], previous_filename)
    
    if not os.path.exists(previous_path):
        return jsonify({'success': False, 'error': 'Previous image not found'})
    
    preview_url = url_for('static', filename=f'preview/{previous_preview}')
    
    session['current_image'] = url_for('static', filename=f'working/{previous_filename}')
    session['current_filename'] = previous_filename
    session['current_preview'] = preview_url
    session['image_history'] = image_history
    session['operations_history'] = operations_history
    session['preview_history'] = preview_history
    
    return jsonify({
        'success': True,
        'processed_image': preview_url,
        'undone_operation': removed_op,
        'operations_history': operations_history,
        'can_undo': len(image_history) > 1
    })


@app.route('/reset', methods=['POST'])
def reset_image():
    if 'original_filename' not in session:
        return jsonify({'success': False, 'error': 'No image to reset'})
    
    original_filename = session['original_filename']
    original_path = os.path.join(app.config['UPLOAD_FOLDER'], original_filename)
    
    if not os.path.exists(original_path):
        clear_session_files()
        return jsonify({'success': False, 'error': 'Original image not found'})
    
    ext = original_filename.rsplit('.', 1)[1] if '.' in original_filename else 'png'
    working_filename = f"working_{uuid.uuid4().hex}.{ext}"
    working_path = os.path.join(app.config['WORKING_FOLDER'], working_filename)
    shutil.copy(original_path, working_path)
    
    preview_filename = f"preview_{uuid.uuid4().hex}.jpg"
    preview_url = create_preview(working_path, preview_filename)
    
    session['current_image'] = url_for('static', filename=f'working/{working_filename}')
    session['current_filename'] = working_filename
    session['current_preview'] = preview_url
    session['operations_history'] = []
    session['image_history'] = [working_filename]
    session['preview_history'] = [preview_filename]
    
    return jsonify({
        'success': True,
        'processed_image': preview_url,
        'operations_history': [],
        'can_undo': False
    })


@app.route('/clear', methods=['POST'])
def clear_session():
    clear_session_files()
    return jsonify({'success': True, 'message': 'Session cleared'})


def clear_session_files():
    original_filename = session.get('original_filename')
    image_history = session.get('image_history', [])
    processed_filename = session.get('processed_filename')
    preview_history = session.get('preview_history', [])
    
    if original_filename:
        original_path = os.path.join(app.config['UPLOAD_FOLDER'], original_filename)
        try:
            if os.path.exists(original_path):
                os.remove(original_path)
        except OSError:
            pass
        # Remove original preview
        preview_orig = f"preview_orig_{original_filename}.jpg"
        try:
            os.remove(os.path.join(app.config['PREVIEW_FOLDER'], preview_orig))
        except OSError:
            pass
        preview_work = f"preview_work_{original_filename}.jpg"
        try:
            os.remove(os.path.join(app.config['PREVIEW_FOLDER'], preview_work))
        except OSError:
            pass
    
    for filename in image_history:
        working_path = os.path.join(app.config['WORKING_FOLDER'], filename)
        try:
            if os.path.exists(working_path):
                os.remove(working_path)
        except OSError:
            pass
    
    for filename in preview_history:
        preview_path = os.path.join(app.config['PREVIEW_FOLDER'], filename)
        try:
            if os.path.exists(preview_path):
                os.remove(preview_path)
        except OSError:
            pass
    
    if processed_filename:
        processed_path = os.path.join(app.config['PROCESSED_FOLDER'], processed_filename)
        try:
            if os.path.exists(processed_path):
                os.remove(processed_path)
        except OSError:
            pass
    
    session.pop('original_image', None)
    session.pop('original_filename', None)
    session.pop('original_preview', None)
    session.pop('current_image', None)
    session.pop('current_filename', None)
    session.pop('current_preview', None)
    session.pop('processed_filename', None)
    session.pop('operations_history', None)
    session.pop('image_history', None)
    session.pop('preview_history', None)


@app.route('/download/<filename>')
def download_file(filename: str):
    return send_from_directory(app.config['PROCESSED_FOLDER'], filename, as_attachment=True)


@app.errorhandler(413)
def too_large(e):
    return jsonify({'success': False, 'error': 'File too large. Max 16MB.'})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)