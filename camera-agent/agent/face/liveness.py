import cv2
import numpy as np


class LivenessChecker:
    def __init__(self) -> None:
        self._previous_gray: np.ndarray | None = None

    def is_live_candidate(self, frame: np.ndarray) -> bool:
        if frame.size == 0:
            return False
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, (160, 90))
        if self._previous_gray is None:
            self._previous_gray = gray
            return True
        diff = float(np.mean(cv2.absdiff(gray, self._previous_gray)))
        self._previous_gray = gray
        return 0.4 <= diff <= 35.0
