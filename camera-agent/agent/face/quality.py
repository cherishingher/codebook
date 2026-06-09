import cv2
import numpy as np


class FaceQualityChecker:
    def is_usable(self, frame: np.ndarray) -> bool:
        if frame.size == 0:
            return False
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        brightness = float(np.mean(gray))
        blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        return 35.0 <= brightness <= 230.0 and blur_score >= 20.0
