"""
Manual media analyzer tests for Dev 1.

These tests avoid real harmful content. They create local safe images/videos,
serve them over localhost URLs, and run the real configured analyzers by
default. Use --fake only when you want a fast pipeline-only check.

Run external URL checks from the project root:
    .\\.venv\\Scripts\\python.exe .\\ml_service\\test_media_cases.py

Optional local generated-media check:
    .\\.venv\\Scripts\\python.exe .\\ml_service\\test_media_cases.py --local

Fast fake-model check:
    .\\.venv\\Scripts\\python.exe .\\ml_service\\test_media_cases.py --local --fake
"""
from __future__ import annotations

import os
import sys
import argparse
from datetime import datetime
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from contracts.schemas import IncomingMessage  # noqa: E402
from ml_service.analyzer import ToxicityAnalyzer  # noqa: E402
from ml_service.vision import MediaAnalysis  # noqa: E402
from ml_service.vision import MediaAnalyzer  # noqa: E402


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args) -> None:
        pass


class FakeVisionAnalyzer:
    def __init__(self, scores_by_suffix: dict[str, float]):
        self.scores_by_suffix = scores_by_suffix

    def analyze_url(self, media_url: str) -> MediaAnalysis:
        import requests

        response = requests.get(media_url, timeout=5)
        if response.status_code != 200:
            return MediaAnalysis(
                is_harmful=False,
                score=0.0,
                category="none",
                explanation=f"fake download failed: {response.status_code}",
                model_used="fake-vision",
            )

        suffix = Path(media_url.split("?", 1)[0]).suffix.lower()
        score = self.scores_by_suffix.get(suffix, 0.0)
        is_harmful = score >= 0.5
        return MediaAnalysis(
            is_harmful=is_harmful,
            score=score,
            category="sexual" if is_harmful else "none",
            explanation=f"fake media score={score:.2f}",
            model_used="fake-vision",
        )


def _message(case_id: str, text: str, media_url: str | None = None) -> IncomingMessage:
    return IncomingMessage(
        message_id=case_id,
        group_name="media test",
        sender_id="dani_2",
        sender_name="Dani",
        child_id="yonatan_1",
        text=text,
        media_url=media_url,
        timestamp=datetime.now(),
    )


def _level(explanation: str) -> str:
    return explanation.split(":", 1)[0]


def _make_image(path: Path) -> None:
    from PIL import Image

    Image.new("RGB", (96, 96), color=(20, 120, 200)).save(path)


def _make_video(path: Path) -> None:
    import cv2
    import numpy as np

    writer = cv2.VideoWriter(
        str(path),
        cv2.VideoWriter_fourcc(*"mp4v"),
        5.0,
        (96, 96),
    )
    for i in range(15):
        frame = np.zeros((96, 96, 3), dtype=np.uint8)
        frame[:, :, 0] = 20 + i * 5
        frame[:, :, 1] = 100
        frame[:, :, 2] = 180
        writer.write(frame)
    writer.release()


def _serve(directory: str):
    handler = partial(QuietHandler, directory=directory)
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


EXTERNAL_CASES = [
    {
        "name": "direct_mp4_video_download_test",
        "url": "https://samplelib.com/lib/preview/mp4/sample-5s.mp4",
        "expected_ai": "unknown",
        "note": "Direct mp4 URL used to verify video downloading works.",
    },
    {
        "name": "youtube_expected_ai_fake",
        "url": "https://www.youtube.com/watch?v=fF5RSmiXzIE&t=2s",
        "expected_ai": "fake",
        "note": "YouTube page URL, not a direct video file.",
    },
    {
        "name": "youtube_expected_real",
        "url": "https://www.youtube.com/watch?v=z6Lx5jnTJFQ&list=RDz6Lx5jnTJFQ&start_radio=1",
        "expected_ai": "real",
        "note": "YouTube page URL, not a direct video file.",
    },
    {
        "name": "wikimedia_expected_real_image",
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/70/Ben_Adam_%286925%29.jpg/250px-Ben_Adam_%286925%29.jpg",
        "expected_ai": "real",
        "note": "Direct image URL.",
    },
    {
        "name": "generated_photos_expected_fake_image",
        "url": "https://images.generated.photos/VbcD0DKjTWYOL1mPrZ9NMQSqxPA_eg-47ncZskfjMYI/rs:fit:256:256/czM6Ly9pY29uczgu/Z3Bob3Rvcy1wcm9k/LnBob3Rvcy92M18w/NzQ0NzMwLmpwZw.jpg",
        "expected_ai": "fake",
        "note": "Direct image URL.",
    },
]


def run_local_tests(use_fake: bool) -> None:
    with TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        image_path = tmp_path / "safe.png"
        video_path = tmp_path / "clip.mp4"
        _make_image(image_path)
        _make_video(video_path)

        server = _serve(tmpdir)
        try:
            base_url = f"http://127.0.0.1:{server.server_port}"
            image_url = f"{base_url}/safe.png"
            video_url = f"{base_url}/clip.mp4"
            missing_url = f"{base_url}/missing.png"

            analyzer = ToxicityAnalyzer(use_model=True, use_vision=True)
            if use_fake:
                analyzer = ToxicityAnalyzer(use_model=False, use_vision=True)
                analyzer.vision = FakeVisionAnalyzer({
                    ".png": 0.82,
                    ".mp4": 0.76,
                })

            cases = [
                ("text_only_safe", _message("media_001", "regular clean message")),
                ("image_url_harmful", _message("media_002", "look at this", image_url)),
                ("video_url_harmful", _message("media_003", "watch this video", video_url)),
                (
                    "text_and_media_take_max",
                    _message("media_004", "איזה אפס אתה", image_url),
                ),
                (
                    "missing_url_safe_fallback",
                    _message("media_005", "plain text", missing_url),
                ),
            ]

            print("case | level | score | toxic | category | model_used")
            print("-" * 96)
            for name, message in cases:
                result = analyzer.analyze(message)
                print(
                    f"{name} | {_level(result.explanation)} | "
                    f"{result.toxicity_score:.3f} | {result.is_toxic} | "
                    f"{result.category} | {result.model_used}"
                )
        finally:
            server.shutdown()


def run_external_url_tests() -> None:
    print("External media URL check")
    print("MediaAnalyzer now reports both harmful-content score and AI-generated/deepfake score.")
    print("Direct video URLs are downloaded directly. YouTube links use yt-dlp and may be blocked by YouTube.")
    print()
    print("case | expected_ai | score | safety_score | ai_score | harmful | category | model_used | note | explanation")
    print("-" * 150)

    media_analyzer = MediaAnalyzer(use_model=True)
    for case in EXTERNAL_CASES:
        result = media_analyzer.analyze_url(case["url"])
        print(
            f"{case['name']} | {case['expected_ai']} | {result.score:.3f} | "
            f"{result.safety_score:.3f} | {result.ai_score:.3f} | "
            f"{result.is_harmful} | {result.category} | {result.model_used} | "
            f"{case['note']} | {result.explanation}"
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--local",
        action="store_true",
        help="Run local generated image/video URL checks instead of external URLs.",
    )
    parser.add_argument(
        "--fake",
        action="store_true",
        help="Use fake deterministic media scores instead of real models.",
    )
    args = parser.parse_args()

    if args.local:
        run_local_tests(use_fake=args.fake)
    else:
        run_external_url_tests()


if __name__ == "__main__":
    main()
