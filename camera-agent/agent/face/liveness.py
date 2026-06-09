import numpy as np


class LivenessChecker:
    def is_live_candidate(self, frame: np.ndarray) -> bool:
        # Lightweight liveness placeholder. Real implementation should inspect consecutive frames.
        return frame.size > 0

