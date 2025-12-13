import os

class Config:
    """Base configuration."""
    SECRET_KEY = 'online-image-lab-secret-key-2024'
    UPLOAD_FOLDER = os.path.join('static', 'uploads')
    PROCESSED_FOLDER = os.path.join('static', 'processed')
    WORKING_FOLDER = os.path.join('static', 'working')
    PREVIEW_FOLDER = os.path.join('static', 'preview')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    PREVIEW_MAX_SIZE = 600
    
    # Cleanup configuration
    CLEANUP_INTERVAL_MINUTES = 60
    FILE_MAX_AGE_SECONDS = 3600  # 1 hour
