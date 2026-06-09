import numpy as np


class FaceQualityChecker:
    def is_usable(self, frame: np.ndarray) -> bool:
        return frame.size > 0

