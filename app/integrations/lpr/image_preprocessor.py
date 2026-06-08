

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

@dataclass
class RoiConfig: 
    x: int
    y: int
    width: int
    height: int
    
    @property
    def is_enabled(self) -> bool:
        return self.width > 0 and self.height > 0
    
    
class ImagePreprocessor:
    def __init__(self, roi: RoiConfig | None = None) -> None:
        self._roi = roi
        
    def decode_jpeg(self, image_bytes: bytes) -> np.ndarray:
        image_array = np.frombuffer(image_bytes, dtype=np.uint8)
        frame = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        if frame is None:
            raise ValueError("No se pudo decodificar la imagen JPEG")
        return frame
    
    def crop_roi(self, frame: np.ndarray) -> np.ndarray:
        if self._roi is None or not self._roi.is_enabled:
            return frame
        
        
        frame_height, frame_width = frame.shape[:2]
        x1 = max(0, min(self._roi.x, frame_width - 1))
        y1 = max(0, min(self._roi.y, frame_height - 1))
        x2 = max(x1 + 1, min(x1 + self._roi.width, frame_width))
        y2 = max(y1 + 1, min(y1 + self._roi.height, frame_height))
        return frame[y1:y2, x1:x2]
    
    def build_ocr_images(self, frame: np.ndarray) -> list[np.ndarray]:
        """Genera variantes de imagen para aumentar robustez del OCR."""
        cropped = self.crop_roi(frame)
        gray = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)
        enlarged = cv2.resize(gray, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
        equalized = cv2.equalizeHist(enlarged)
        blurred = cv2.GaussianBlur(equalized, (3, 3), 0)
        threshold = cv2.adaptiveThreshold(
            blurred,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            31,
            5,
        )
        return [cropped, enlarged, equalized, threshold]

        