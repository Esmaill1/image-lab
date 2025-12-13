"""
Image Processing Module for Online Image Lab
Implements various image processing operations using OpenCV
"""

import cv2
import numpy as np


class ImageProcessor:
    """
   . A class to perform various image processing operations using OpenCV.
    
    Supported operations:
    - Geometric: resize, rotate
    - Enhancement: hist_eq, brightness, negative
    - Restoration: blur_gaussian, denoise_median
    - Analysis: edge_sobel
    """
    
    def __init__(self, image_path: str):
        """
        Initialize the processor with an image.
        
        Args:
            image_path: Path to the input image file
        """
        self.image = cv2.imread(image_path)
        if self.image is None:
            raise ValueError(f"Could not load image from: {image_path}")
        self.result = self.image.copy()
    
    def process(self, operation: str, params: dict) -> np.ndarray:
        """
        Process the image based on the specified operation and parameters.
        
        Args:
            operation: The name of the operation to perform
            params: Dictionary of parameters for the operation
            
        Returns:
            The processed image as a numpy array
        """
        operations = {
            'resize': self._resize,
            'rotate': self._rotate,
            'hist_eq': self._histogram_equalization,
            'brightness': self._brightness,
            'negative': self._negative,
            'blur_gaussian': self._gaussian_blur,
            'denoise_median': self._median_blur,
            'edge_sobel': self._sobel_edge,
            'sharpen': self._sharpen
        }
        
        if operation not in operations:
            raise ValueError(f"Unknown operation: {operation}")
        
        self.result = operations[operation](params)
        return self.result
    
    def save(self, output_path: str) -> bool:
        """
        Save the processed image to the specified path.
        
        Args:
            output_path: Path where the processed image will be saved
            
        Returns:
            True if save was successful, False otherwise
        """
        return cv2.imwrite(output_path, self.result)
    
    # ==================== Geometric Operations (Lab 4) ====================
    
    def _resize(self, params: dict) -> np.ndarray:
        """
        Resize the image by a percentage scale.
        
        Args:
            params: Dictionary containing 'scale' (percentage, e.g., 50 for 50%)
            
        Returns:
            Resized image
        """
        scale = params.get('scale', 100) / 100.0
        if scale <= 0:
            scale = 0.1
        
        width = int(self.image.shape[1] * scale)
        height = int(self.image.shape[0] * scale)
        
        # Ensure minimum dimensions
        width = max(1, width)
        height = max(1, height)
        
        return cv2.resize(self.image, (width, height), interpolation=cv2.INTER_LINEAR)
    
    def _rotate(self, params: dict) -> np.ndarray:
        """
        Rotate the image by a specific angle.
        
        Args:
            params: Dictionary containing 'angle' (0-360 degrees)
            
        Returns:
            Rotated image
        """
        angle = params.get('angle', 0)
        
        # Get image dimensions
        height, width = self.image.shape[:2]
        center = (width // 2, height // 2)
        
        # Calculate rotation matrix
        rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        
        # Calculate new bounding box size
        cos = np.abs(rotation_matrix[0, 0])
        sin = np.abs(rotation_matrix[0, 1])
        new_width = int((height * sin) + (width * cos))
        new_height = int((height * cos) + (width * sin))
        
        # Adjust the rotation matrix
        rotation_matrix[0, 2] += (new_width / 2) - center[0]
        rotation_matrix[1, 2] += (new_height / 2) - center[1]
        
        return cv2.warpAffine(self.image, rotation_matrix, (new_width, new_height),
                              borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 255, 255))
    
    # ==================== Enhancement Operations (Lab 5) ====================
    
    def _histogram_equalization(self, params: dict) -> np.ndarray:
        """
        Apply Histogram Equalization.
        Converts to YUV, equalizes Y channel, converts back to BGR.
        
        Args:
            params: Not used for this operation
            
        Returns:
            Image with equalized histogram
        """
        # Convert BGR to YUV
        yuv = cv2.cvtColor(self.image, cv2.COLOR_BGR2YUV)
        
        # Equalize the Y channel (luminance)
        yuv[:, :, 0] = cv2.equalizeHist(yuv[:, :, 0])
        
        # Convert back to BGR
        return cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR)
    
    def _brightness(self, params: dict) -> np.ndarray:
        """
        Adjust image brightness by adding/subtracting a scalar value.
        
        Args:
            params: Dictionary containing 'value' (-100 to 100)
            
        Returns:
            Brightness-adjusted image
        """
        value = params.get('value', 0)
        
        # Convert to float to prevent overflow/underflow
        result = self.image.astype(np.float32) + value
        
        # Clip values to valid range and convert back to uint8
        result = np.clip(result, 0, 255).astype(np.uint8)
        
        return result
    
    def _negative(self, params: dict) -> np.ndarray:
        """
        Invert the image colors (255 - pixel).
        
        Args:
            params: Not used for this operation
            
        Returns:
            Inverted (negative) image
        """
        return 255 - self.image
    
    # ==================== Restoration Operations (Lab 6) ====================
    
    def _gaussian_blur(self, params: dict) -> np.ndarray:
        """
        Apply Gaussian Blur with a specified kernel size.
        
        Args:
            params: Dictionary containing 'kernel_size' (must be odd)
            
        Returns:
            Blurred image
        """
        k = params.get('kernel_size', 5)
        
        # Ensure kernel size is odd and positive
        k = max(1, int(k))
        if k % 2 == 0:
            k += 1
        
        return cv2.GaussianBlur(self.image, (k, k), 0)
    
    def _median_blur(self, params: dict) -> np.ndarray:
        """
        Apply Median Blur to remove salt-and-pepper noise.
        
        Args:
            params: Dictionary containing 'kernel_size' (must be odd)
            
        Returns:
            Denoised image
        """
        k = params.get('kernel_size', 5)
        
        # Ensure kernel size is odd and positive
        k = max(1, int(k))
        if k % 2 == 0:
            k += 1
        
        return cv2.medianBlur(self.image, k)
    
    # ==================== Analysis Operations (Lab 7) ====================
    
    def _sobel_edge(self, params: dict) -> np.ndarray:
        """
        Detect edges using the Sobel operator.
        Combines X and Y gradients.
        
        Args:
            params: Dictionary containing optional 'ksize' (Sobel kernel size, default 3)
            
        Returns:
            Edge-detected image
        """
        ksize = params.get('ksize', 3)
        
        # Ensure ksize is odd and in valid range (1, 3, 5, 7)
        ksize = max(1, min(7, int(ksize)))
        if ksize % 2 == 0:
            ksize += 1
        
        # Convert to grayscale for edge detection
        gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        
        # Apply Sobel operator in X and Y directions
        sobel_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=ksize)
        sobel_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=ksize)
        
        # Combine gradients using magnitude
        magnitude = np.sqrt(sobel_x**2 + sobel_y**2)
        
        # Normalize to 0-255 range
        magnitude = np.clip(magnitude, 0, 255).astype(np.uint8)
        
        # Convert back to BGR for consistency
        return cv2.cvtColor(magnitude, cv2.COLOR_GRAY2BGR)
    
    def _sharpen(self, params: dict) -> np.ndarray:
        """
        Sharpen image using Laplacian edge enhancement.
        Adds edges back to original image to enhance sharpness.
        
        Args:
            params: Dictionary containing 'strength' (0.1 to 3.0)
            
        Returns:
            Sharpened image
        """
        strength = params.get('strength', 1.0)
        strength = max(0.1, min(3.0, float(strength)))
        
        # Convert to float for processing
        img_float = self.image.astype(np.float32)
        
        # Apply Laplacian to detect edges
        laplacian = cv2.Laplacian(img_float, cv2.CV_32F, ksize=3)
        
        # Sharpen: original + strength * edges
        sharpened = img_float - strength * laplacian
        
        # Clip and convert back to uint8
        sharpened = np.clip(sharpened, 0, 255).astype(np.uint8)
        
        return sharpened
