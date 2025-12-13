# Online Image Lab - Project Context

## Project Overview

The Online Image Lab is a web-based image processing application that demonstrates fundamental computer vision techniques. Built with Python Flask backend and Bootstrap 5 frontend, it provides an intuitive interface for applying various image processing operations in real-time.

## Architecture

### Backend (Flask)
- **app.py**: Main Flask application handling routes, file uploads, and session management
- **processor.py**: Core image processing module using OpenCV
- **Session Management**: Persistent image sessions allowing multiple sequential operations
- **File Organization**: Separate folders for uploads, working files, processed images, and previews

### Frontend (Bootstrap 5)
- **Responsive Design**: Mobile-first approach with collapsible sidebar
- **AJAX Operations**: All image processing happens without page reloads
- **Real-time Feedback**: Progress bars for uploads, spinners for processing
- **LocalStorage**: Remembers user's preferred accordion tab

### Image Processing Pipeline

1. **Upload**: User uploads image → Creates working copy → Generates preview
2. **Process**: Apply operation → Update working image → Create new preview
3. **History**: Maintain stack of previous images for undo functionality
4. **Download**: Full-resolution processed image available for download

## Key Features

### Core Operations
| Category | Operations | Description |
|----------|------------|-------------|
| **Geometry** | Resize, Rotate | Scale and rotate images with proper bounds handling |
| **Enhancement** | Histogram Equalization, Brightness, Negative | Improve image appearance |
| **Filters** | Gaussian Blur, Median Denoise | Noise reduction and smoothing |
| **Edges** | Sobel Edge Detection, Sharpen | Edge detection and enhancement |

### Advanced Features
- **Undo System**: Step back through operation history
- **Reset**: Revert to original uploaded image
- **Session Persistence**: Multiple operations without re-uploading
- **Preview Images**: Smaller, optimized versions for faster loading
- **Progress Indicators**: Upload progress bar and processing spinner
- **Mobile Responsive**: Collapsible sidebar and touch-friendly controls

## Technical Implementation Details

### File Structure
```
ip/
├── .github/
│   └── workflows/
│       └── deploy.yml    # GitHub Actions deployment workflow
├── app.py                # Flask server and routes
├── processor.py          # ImageProcessor class with OpenCV operations
├── requirements.txt      # Python dependencies
├── context.md            # This file
├── README.md             # User documentation
├── Dockerfile            # Container definition
├── .dockerignore         # Docker build ignore rules
├── templates/
│   └── index.html        # Bootstrap 5 dashboard UI
└── static/
    ├── uploads/          # Original uploaded images (temporary)
    ├── working/          # Working images for undo history (temporary)
    ├── processed/        # Processed images for download (temporary)
    └── preview/          # Smaller preview images (temporary)
```

### Session Management
- **original_image**: URL to full-resolution original
- **original_preview**: URL to optimized preview
- **current_image**: URL to current working image
- **current_preview**: URL to current preview
- **image_history**: Stack of working filenames for undo
- **preview_history**: Stack of preview filenames
- **operations_history**: List of applied operation names

### Image Processing Techniques

#### Resize
- Uses linear interpolation for quality scaling
- Maintains aspect ratio
- Minimum dimension protection (1px)

#### Rotate
- Full 360-degree rotation
- Expands canvas to fit rotated image
- White background for uncovered areas

#### Histogram Equalization
- Converts to YUV color space
- Equalizes luminance channel only
- Preserves color information

#### Brightness
- Direct pixel value adjustment
- Clamps values to prevent overflow
- Range: -100 to +100

#### Gaussian Blur
- Configurable kernel size (odd numbers only)
- Maintains image dimensions
- Smooths high-frequency details

#### Median Denoise
- Salt-and-pepper noise removal
- Preserves edges better than Gaussian
- Odd kernel sizes only

#### Sobel Edge Detection
- Gradient-based edge detection
- Combines X and Y gradients
- Configurable kernel size (1, 3, 5, 7)

#### Sharpen
- Laplacian edge enhancement
- Adjustable strength (0.5x to 3.0x)
- Original - strength × edges

### Security Considerations
- File type validation (whitelist approach)
- Maximum file size limit (16MB)
- Secure filename generation with UUID
- Temporary file cleanup on session clear
- Path traversal protection

### Performance Optimizations
- Preview images (max 600px) for faster loading
- AJAX operations prevent full page reloads
- Lazy loading of images
- Efficient file cleanup
- Session-based state management

## CI/CD & Deployment

- **GitHub Actions**: Automated deployment workflow configured in `.github/workflows/deploy.yml`.
- **Trigger**: Pushes to `main` branch (ignoring image assets).
- **Process**: Connects to VPS via SSH and executes a deployment script (`~/deploy.sh`).
- **Containerization**: `Dockerfile` provided for consistent runtime environment based on Python 3.11-slim.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Main dashboard page |
| POST | `/upload` | Upload new image with progress tracking |
| POST | `/process` | Apply operation to current image |
| POST | `/undo` | Revert to previous state |
| POST | `/reset` | Reset to original image |
| POST | `/clear` | Clear session and delete all files |
| GET | `/download/<filename>` | Download processed image |

## Dependencies
- **Flask 2.3+**: Web framework
- **OpenCV 4.8+**: Image processing
- **NumPy 1.24+**: Numerical operations
- **Werkzeug 2.3+**: File handling utilities
- **Bootstrap 5.3.2**: Frontend framework
- **Bootstrap Icons**: UI icons

## Browser Compatibility
- Modern browsers with ES6 support
- Mobile browsers (iOS Safari, Chrome Mobile)
- Desktop browsers (Chrome, Firefox, Safari, Edge)

## Extension Points
- Add new operations to `processor.py`
- Extend API routes in `app.py`
- Modify UI components in `templates/index.html`
- Add authentication/authorization layer
- Integrate cloud storage for image persistence
- Add batch processing capabilities
- Implement image format conversion
- Add advanced filters (vintage, HDR, etc.)

## Educational Value
This project serves as a comprehensive demonstration of:
- Full-stack web development with Python
- Computer vision fundamentals with OpenCV
- Modern frontend development with Bootstrap
- Session management and state persistence
- File upload handling and security
- Responsive web design principles
- AJAX and asynchronous operations
- Image processing algorithms and techniques