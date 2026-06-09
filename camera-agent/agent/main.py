from agent.api.client import ApiClient
from agent.camera.capture import CameraCapture
from agent.face.pipeline import RecognitionPipeline


def main() -> None:
    camera = CameraCapture()
    api = ApiClient()
    pipeline = RecognitionPipeline(api=api)
    camera.open()
    try:
        for frame in camera.frames():
            pipeline.process_frame(frame)
    finally:
        camera.close()


if __name__ == "__main__":
    main()

