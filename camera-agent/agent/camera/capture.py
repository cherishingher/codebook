from collections.abc import Iterator

import cv2
import numpy as np

from agent.config import settings


class CameraCapture:
    def __init__(self, camera_index: int | None = None) -> None:
        self.camera_index = settings.camera_index if camera_index is None else camera_index
        self.capture: cv2.VideoCapture | None = None

    def open(self) -> None:
        self.capture = cv2.VideoCapture(self.camera_index)
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, settings.frame_width)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, settings.frame_height)
        if not self.capture.isOpened():
            raise RuntimeError(f"Cannot open USB camera index {self.camera_index}")

    def frames(self) -> Iterator[np.ndarray]:
        if self.capture is None:
            raise RuntimeError("Camera is not open")
        while True:
            ok, frame = self.capture.read()
            if not ok:
                raise RuntimeError("Failed to read frame from camera")
            yield frame

    def close(self) -> None:
        if self.capture is not None:
            self.capture.release()
            self.capture = None

