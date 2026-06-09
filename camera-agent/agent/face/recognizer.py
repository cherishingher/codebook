import cv2
import numpy as np

from agent.config import settings
from agent.face.types import FaceMatch, FaceProfile


class FaceRecognizer:
    def __init__(self) -> None:
        self.profiles: list[FaceProfile] = []

    def update_profiles(self, profiles: list[FaceProfile]) -> None:
        self.profiles = profiles

    def recognize(self, frame: np.ndarray) -> list[FaceMatch]:
        if not self.profiles:
            return []
        feature = self._extract_feature(frame)
        matches: list[FaceMatch] = []
        for profile in self.profiles:
            if profile.feature.shape != feature.shape:
                continue
            confidence = self._cosine_similarity(feature, profile.feature)
            if confidence >= settings.recognition_threshold:
                height, width = frame.shape[:2]
                matches.append(FaceMatch(profile.student_id, confidence, (0, 0, width, height)))
        return sorted(matches, key=lambda item: item.confidence, reverse=True)[:1]

    @staticmethod
    def _extract_feature(frame: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        resized = cv2.resize(gray, (32, 32)).astype(np.float32) / 255.0
        feature = resized.flatten()
        norm = np.linalg.norm(feature)
        return feature if norm == 0 else feature / norm

    @staticmethod
    def _cosine_similarity(left: np.ndarray, right: np.ndarray) -> float:
        left_norm = np.linalg.norm(left)
        right_norm = np.linalg.norm(right)
        if left_norm == 0 or right_norm == 0:
            return 0.0
        return float(np.dot(left, right) / (left_norm * right_norm))
