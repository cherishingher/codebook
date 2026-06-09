from agent.api.client import ApiClient
from agent.face.types import FaceProfile


class FaceStore:
    def __init__(self, api: ApiClient) -> None:
        self.api = api

    def sync(self) -> list[FaceProfile]:
        raw_profiles = self.api.fetch_face_profiles()
        profiles: list[FaceProfile] = []
        for item in raw_profiles:
            _ = item
        return profiles

