import numpy as np

from agent.face.types import FaceMatch, FaceProfile


class FaceRecognizer:
    def __init__(self) -> None:
        self.profiles: list[FaceProfile] = []

    def update_profiles(self, profiles: list[FaceProfile]) -> None:
        self.profiles = profiles

    def recognize(self, frame: np.ndarray) -> list[FaceMatch]:
        # Placeholder. The production implementation will use InsightFace.
        return []

