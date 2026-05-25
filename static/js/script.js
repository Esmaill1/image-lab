// Initialize tooltips and other bootstrap components if needed
// Note: hasSession and downloadUrl are defined in the HTML template

document.addEventListener('DOMContentLoaded', function() {
    // Restore accordion state
    const lastOpen = localStorage.getItem('imagelab_accordion');
    if (lastOpen) {
        const collapseEl = document.getElementById(lastOpen);
        if (collapseEl) {
            const bsCollapse = bootstrap.Collapse.getInstance(collapseEl) || new bootstrap.Collapse(collapseEl, { show: false });
            bsCollapse.show();
        }
    }
    
    // Save accordion state
    document.querySelectorAll('.accordion-collapse').forEach(collapse => {
        collapse.addEventListener('shown.bs.collapse', function() {
            localStorage.setItem('imagelab_accordion', this.id);
        });
    });
});

// File upload with progress
document.getElementById('imageInput').addEventListener('change', function(e) {
    if (!this.files || !this.files[0]) return;
    
    const file = this.files[0];
    
    // Client-side validation
    const maxSize = 16 * 1024 * 1024; // 16MB
    if (file.size > maxSize) {
        showAlert('danger', 'File too large. Max size is 16MB.');
        this.value = ''; // Clear input
        return;
    }
    
    const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/bmp', 'image/webp'];
    if (!allowedTypes.includes(file.type)) {
        showAlert('danger', 'Invalid file type. Allowed: JPG, PNG, GIF, BMP, WEBP.');
        this.value = ''; // Clear input
        return;
    }

    const formData = new FormData();
    formData.append('image', file);
    
    const xhr = new XMLHttpRequest();
    const progressDiv = document.getElementById('uploadProgress');
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    
    progressDiv.classList.add('active');
    
    xhr.upload.addEventListener('progress', function(e) {
        if (e.lengthComputable) {
            const percent = Math.round((e.loaded / e.total) * 100);
            progressBar.style.width = percent + '%';
            progressText.textContent = 'Uploading... ' + percent + '%';
        }
    });
    
    xhr.addEventListener('load', function() {
        progressDiv.classList.remove('active');
        progressBar.style.width = '0%';
        
        if (xhr.status === 200) {
            const response = JSON.parse(xhr.responseText);
            if (response.success) {
                window.hasSession = true;
                updateUIForSession();
                document.getElementById('originalImageContainer').innerHTML = 
                    '<img src="' + response.original_image + '" alt="Original">';
                document.getElementById('processedImageContainer').innerHTML = 
                    '<img src="' + response.processed_image + '" alt="Processed">';
                showAlert('success', response.message);
                updateOperationsHistory([]);
                document.getElementById('undoBtn').disabled = true;
                document.getElementById('downloadSection').style.display = 'none';
            } else {
                showAlert('danger', response.error);
            }
        }
    });
    
    xhr.addEventListener('error', function() {
        progressDiv.classList.remove('active');
        showAlert('danger', 'Upload failed');
    });
    
    xhr.open('POST', '/upload');
    xhr.send(formData);
});

function applyOperation(operation, params) {
    if (!window.hasSession) {
        showAlert('warning', 'Please upload an image first');
        return;
    }
    
    const overlay = document.getElementById('processingOverlay');
    overlay.classList.add('active');
    
    const formData = new FormData();
    formData.append('operation', operation);
    for (const key in params) {
        formData.append(key, params[key]);
    }
    
    fetch('/process', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        overlay.classList.remove('active');
        if (data.success) {
            document.getElementById('processedImageContainer').innerHTML = 
                '<img src="' + data.processed_image + '?t=' + Date.now() + '" alt="Processed">';
            updateOperationsHistory(data.operations_history);
            document.getElementById('undoBtn').disabled = !data.can_undo;
            window.downloadUrl = data.download_url;
            document.getElementById('downloadBtn').href = window.downloadUrl;
            document.getElementById('downloadSection').style.display = 'block';
            showAlert('success', 'Applied: ' + data.operation);
        } else {
            showAlert('danger', data.error);
        }
    })
    .catch(err => {
        overlay.classList.remove('active');
        showAlert('danger', 'Processing failed');
    });
}

function undoOperation() {
    const overlay = document.getElementById('processingOverlay');
    overlay.classList.add('active');
    
    fetch('/undo', { method: 'POST' })
    .then(response => response.json())
    .then(data => {
        overlay.classList.remove('active');
        if (data.success) {
            document.getElementById('processedImageContainer').innerHTML = 
                '<img src="' + data.processed_image + '?t=' + Date.now() + '" alt="Processed">';
            updateOperationsHistory(data.operations_history);
            document.getElementById('undoBtn').disabled = !data.can_undo;
            showAlert('success', 'Undone: ' + data.undone_operation);
        } else {
            showAlert('danger', data.error);
        }
    });
}

function resetImage() {
    fetch('/reset', { method: 'POST' })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            document.getElementById('processedImageContainer').innerHTML = 
                '<img src="' + data.processed_image + '?t=' + Date.now() + '" alt="Processed">';
            updateOperationsHistory([]);
            document.getElementById('undoBtn').disabled = true;
            document.getElementById('downloadSection').style.display = 'none';
            showAlert('success', 'Image reset to original');
        } else {
            showAlert('danger', data.error);
        }
    });
}

function clearSession() {
    fetch('/clear', { method: 'POST' })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            window.hasSession = false;
            updateUIForNoSession();
            document.getElementById('originalImageContainer').innerHTML = 
                '<div class="placeholder-content"><i class="bi bi-image"></i><p>Upload an image to get started</p></div>';
            document.getElementById('processedImageContainer').innerHTML = 
                '<div class="placeholder-content"><i class="bi bi-gear"></i><p>Apply operations to see results</p></div>';
            updateOperationsHistory([]);
            showAlert('info', 'Session cleared');
        }
    });
}

function updateUIForSession() {
    document.getElementById('uploadArea').classList.add('has-image');
    document.getElementById('uploadIcon').className = 'bi bi-check-circle';
    document.getElementById('uploadText').textContent = 'Image loaded - Click to replace';
    document.getElementById('sessionControls').style.display = 'flex';
    document.getElementById('statusBadge').className = 'status-badge';
    document.getElementById('statusBadge').innerHTML = '<i class="bi bi-check-circle me-1"></i>Image Loaded';
}

function updateUIForNoSession() {
    document.getElementById('uploadArea').classList.remove('has-image');
    document.getElementById('uploadIcon').className = 'bi bi-cloud-arrow-up';
    document.getElementById('uploadText').textContent = 'Click to upload an image';
    document.getElementById('sessionControls').style.display = 'none';
    document.getElementById('downloadSection').style.display = 'none';
    document.getElementById('statusBadge').className = 'status-badge no-image';
    document.getElementById('statusBadge').innerHTML = '<i class="bi bi-image me-1"></i>No Image';
}

function updateOperationsHistory(history) {
    const section = document.getElementById('historySection');
    const list = document.getElementById('operationsList');
    
    if (history && history.length > 0) {
        section.style.display = 'block';
        list.innerHTML = history.map(op => '<span class="operation-tag">' + op + '</span>').join('');
    } else {
        section.style.display = 'none';
        list.innerHTML = '';
    }
}

function showAlert(type, message) {
    const container = document.getElementById('alertContainer');
    const alert = document.createElement('div');
    alert.className = 'alert alert-' + type + ' alert-dismissible fade show';
    alert.innerHTML = message + '<button type="button" class="btn-close" data-bs-dismiss="alert"></button>';
    container.appendChild(alert);
    
    setTimeout(() => {
        if (alert.parentNode) {
            new bootstrap.Alert(alert).close();
        }
    }, 4000);
}
