
import cv2
import numpy as np


class ImageProcessor:

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

        operations = {
            'resize': self._resize,
            'rotate': self._rotate,
            'hist_eq': self._histogram_equalization,
            'brightness': self._brightness,
            'negative': self._negative,
            'blur_gaussian': self._gaussian_blur,
            'denoise_median': self._median_blur,
            'edge_sobel': self._sobel_edge,
            'sharpen': self._sharpen,
            'convert': self._convert
        }
        
        if operation not in operations:
            raise ValueError(f"Unknown operation: {operation}")
        
        self.result = operations[operation](params)
        return self.result
    
    def save(self, output_path: str) -> bool:
        
        return cv2.imwrite(output_path, self.result)
    
    # ==================== Geometric Operations ====================
    
    def _resize(self, params: dict) -> np.ndarray:

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
    
    # ==================== Enhancement Operations ====================
    
    def _histogram_equalization(self, params: dict) -> np.ndarray:

        yuv = cv2.cvtColor(self.image, cv2.COLOR_BGR2YUV)
        
        # Equalize the Y channel (luminance)
        yuv[:, :, 0] = cv2.equalizeHist(yuv[:, :, 0])
        
        # Convert back to BGR
        return cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR)
    
    def _brightness(self, params: dict) -> np.ndarray:

        value = params.get('value', 0)  
        result = self.image.astype(np.float32) + value
        result = np.clip(result, 0, 255).astype(np.uint8)
        
        return result
    
    def _negative(self, params: dict) -> np.ndarray:
        return 255 - self.image
    
    # ==================== Restoration Operations  ====================
    
    def _gaussian_blur(self, params: dict) -> np.ndarray:
      
        k = params.get('kernel_size', 5)
        k = max(1, int(k))
        if k % 2 == 0:
            k += 1
        return cv2.GaussianBlur(self.image, (k, k), 0)
    
    def _median_blur(self, params: dict) -> np.ndarray:
        ## salt and papper remover

        k = params.get('kernel_size', 5)
        
        k = max(1, int(k))
        if k % 2 == 0:
            k += 1
        
        return cv2.medianBlur(self.image, k)
    
    # ==================== Analysis Operations ====================
    
    def _sobel_edge(self, params: dict) -> np.ndarray:
        """
        Detect edges using the Sobel operator.
        """
        ksize = params.get('ksize', 3)
        ksize = max(1, min(7, int(ksize)))
        if ksize % 2 == 0:
            ksize += 1    
            
        # Convert to grayscale
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

    # ==================== Utility Operations ====================

    def _convert(self, params: dict) -> np.ndarray:

        return self.image
