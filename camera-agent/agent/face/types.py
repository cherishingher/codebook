from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class FaceMatch:
    student_id: int
    confidence: float
    bbox: tuple[int, int, int, int]


@dataclass(frozen=True)
class FaceProfile:
    student_id: int
    feature: np.ndarray

