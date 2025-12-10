"""
Flask Web Server for Online Image Lab
Handles file uploads and image processing requests
Supports persistent image sessions for multiple operations
"""

import os
import uuid
import shutil
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, session
from werkzeug.utils import secure_filename
from processor import ImageProcessor

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'online-image-lab-secret-key-2024'

# Configuration
UPLOAD_FOLDER = os.path.join('static', 'uploads')
PROCESSED_FOLDER = os.path.join('static', 'processed')
WORKING_FOLDER = os.path.join('static', 'working')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROCESSED_FOLDER'] = PROCESSED_FOLDER
app.config['WORKING_FOLDER'] = WORKING_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)
os.makedirs(WORKING_FOLDER, exist_ok=True)


def allowed_file(filename: str) -> bool:
    """Check if the file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def generate_unique_filename(original_filename: str) -> str:
    """Generate a unique filename to prevent overwrites."""
    ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else 'png'
    return f"{uuid.uuid4().hex}.{ext}"


@app.route('/')
def index():
    """Render the main dashboard page."""
    # Check if there's an existing session with images
    original_image = session.get('original_image')
    current_image = session.get('current_image')
    operations_history = session.get('operations_history', [])
    
    return render_template('index.html', 
                           original_image=original_image,
                           processed_image=current_image,
                           processed_filename=session.get('current_filename'),
                           operations_history=operations_history,
                           has_session=original_image is not None)


@app.route('/upload', methods=['POST'])
def upload_image():
    """Handle initial image upload."""
    if 'image' not in request.files:
        flash('No file uploaded', 'error')
        return redirect(url_for('index'))
    
    file = request.files['image']
    
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('index'))
    
    if not allowed_file(file.filename):
        flash('Invalid file type. Allowed: PNG, JPG, JPEG, GIF, BMP, WEBP', 'error')
        return redirect(url_for('index'))
    
    # Clear previous session
    clear_session_files()
    
    # Save uploaded file
    original_filename = generate_unique_filename(secure_filename(file.filename))
    original_path = os.path.join(app.config['UPLOAD_FOLDER'], original_filename)
    file.save(original_path)
    
    # Copy to working folder as current image
    working_filename = f"working_{original_filename}"
    working_path = os.path.join(app.config['WORKING_FOLDER'], working_filename)
    shutil.copy(original_path, working_path)
    
    # Store in session
    session['original_image'] = url_for('static', filename=f'uploads/{original_filename}')
    session['original_filename'] = original_filename
    session['current_image'] = url_for('static', filename=f'working/{working_filename}')
    session['current_filename'] = working_filename
    session['operations_history'] = []
    session['image_history'] = [working_filename]  # Stack of image filenames for undo
    
    flash('Image uploaded successfully! Now apply operations.', 'success')
    return redirect(url_for('index'))


@app.route('/process', methods=['POST'])
def process_image():
    """Apply an operation to the current working image."""
    # Check if we have a working image
    if 'current_filename' not in session:
        flash('Please upload an image first', 'error')
        return redirect(url_for('index'))
    
    # Get operation and parameters from form
    operation = request.form.get('operation', '')
    
    if not operation:
        flash('No operation selected', 'error')
        return redirect(url_for('index'))
    
    # Get current working image path
    current_filename = session['current_filename']
    current_path = os.path.join(app.config['WORKING_FOLDER'], current_filename)
    
    if not os.path.exists(current_path):
        flash('Working image not found. Please upload again.', 'error')
        clear_session_files()
        return redirect(url_for('index'))
    
    # Build parameters dictionary based on operation
    params = {}
    operation_display = operation.replace('_', ' ').title()
    
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
        
    except (ValueError, TypeError) as e:
        flash(f'Invalid parameter value: {str(e)}', 'error')
        return redirect(url_for('index'))
    
    # Process the image
    try:
        processor = ImageProcessor(current_path)
        processor.process(operation, params)
        
        # Generate new working filename
        ext = current_filename.rsplit('.', 1)[1] if '.' in current_filename else 'png'
        new_working_filename = f"working_{uuid.uuid4().hex}.{ext}"
        new_working_path = os.path.join(app.config['WORKING_FOLDER'], new_working_filename)
        processor.save(new_working_path)
        
        # Also save to processed folder for download
        processed_filename = f"processed_{uuid.uuid4().hex}.{ext}"
        processed_path = os.path.join(app.config['PROCESSED_FOLDER'], processed_filename)
        shutil.copy(new_working_path, processed_path)
        
        # Update session
        session['current_image'] = url_for('static', filename=f'working/{new_working_filename}')
        session['current_filename'] = new_working_filename
        session['processed_filename'] = processed_filename
        
        # Add to operations history
        operations_history = session.get('operations_history', [])
        operations_history.append(operation_display)
        session['operations_history'] = operations_history
        
        # Add to image history stack for undo
        image_history = session.get('image_history', [])
        image_history.append(new_working_filename)
        session['image_history'] = image_history
        
        flash(f'Applied: {operation_display}', 'success')
        return redirect(url_for('index'))
        
    except Exception as e:
        flash(f'Error processing image: {str(e)}', 'error')
        return redirect(url_for('index'))


@app.route('/reset', methods=['POST'])
def reset_image():
    """Reset to the original uploaded image."""
    if 'original_filename' not in session:
        flash('No image to reset', 'error')
        return redirect(url_for('index'))
    
    original_filename = session['original_filename']
    original_path = os.path.join(app.config['UPLOAD_FOLDER'], original_filename)
    
    if not os.path.exists(original_path):
        flash('Original image not found', 'error')
        clear_session_files()
        return redirect(url_for('index'))
    
    # Copy original back to working folder
    ext = original_filename.rsplit('.', 1)[1] if '.' in original_filename else 'png'
    working_filename = f"working_{uuid.uuid4().hex}.{ext}"
    working_path = os.path.join(app.config['WORKING_FOLDER'], working_filename)
    shutil.copy(original_path, working_path)
    
    # Update session
    session['current_image'] = url_for('static', filename=f'working/{working_filename}')
    session['current_filename'] = working_filename
    session['operations_history'] = []
    session['image_history'] = [working_filename]  # Reset history stack
    
    flash('Image reset to original', 'success')
    return redirect(url_for('index'))


@app.route('/undo', methods=['POST'])
def undo_operation():
    """Undo the last operation by reverting to previous image state."""
    image_history = session.get('image_history', [])
    operations_history = session.get('operations_history', [])
    
    # Need at least 2 images in history to undo (original + at least one operation)
    if len(image_history) < 2:
        flash('Nothing to undo', 'error')
        return redirect(url_for('index'))
    
    # Remove current image from history
    image_history.pop()
    
    # Get previous image
    previous_filename = image_history[-1]
    previous_path = os.path.join(app.config['WORKING_FOLDER'], previous_filename)
    
    if not os.path.exists(previous_path):
        flash('Previous image not found', 'error')
        return redirect(url_for('index'))
    
    # Remove last operation from history
    if operations_history:
        removed_op = operations_history.pop()
    
    # Update session
    session['current_image'] = url_for('static', filename=f'working/{previous_filename}')
    session['current_filename'] = previous_filename
    session['image_history'] = image_history
    session['operations_history'] = operations_history
    
    flash(f'Undone: {removed_op}', 'success')
    return redirect(url_for('index'))


@app.route('/clear', methods=['POST'])
def clear_session():
    """Clear the current session and start fresh."""
    clear_session_files()
    flash('Session cleared. Upload a new image to start.', 'info')
    return redirect(url_for('index'))


def clear_session_files():
    """Clear session data and delete associated files."""
    # Get filenames before clearing session
    original_filename = session.get('original_filename')
    image_history = session.get('image_history', [])
    processed_filename = session.get('processed_filename')
    
    # Delete original uploaded file
    if original_filename:
        original_path = os.path.join(app.config['UPLOAD_FOLDER'], original_filename)
        try:
            if os.path.exists(original_path):
                os.remove(original_path)
        except OSError:
            pass
    
    # Delete all working images from history
    for filename in image_history:
        working_path = os.path.join(app.config['WORKING_FOLDER'], filename)
        try:
            if os.path.exists(working_path):
                os.remove(working_path)
        except OSError:
            pass
    
    # Delete processed file
    if processed_filename:
        processed_path = os.path.join(app.config['PROCESSED_FOLDER'], processed_filename)
        try:
            if os.path.exists(processed_path):
                os.remove(processed_path)
        except OSError:
            pass
    
    # Clear session data
    session.pop('original_image', None)
    session.pop('original_filename', None)
    session.pop('current_image', None)
    session.pop('current_filename', None)
    session.pop('processed_filename', None)
    session.pop('operations_history', None)
    session.pop('image_history', None)


@app.route('/download/<filename>')
def download_file(filename: str):
    """Download the processed image."""
    return send_from_directory(app.config['PROCESSED_FOLDER'], filename, as_attachment=True)


@app.errorhandler(413)
def too_large(e):
    """Handle file too large error."""
    flash('File is too large. Maximum size is 16MB.', 'error')
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
