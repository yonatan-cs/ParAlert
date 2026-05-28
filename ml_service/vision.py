"""
Media safety analyzers for images and videos. OWNER: Dev 1.

This module is split by task:
  - MediaDownloader: URL -> local temp file.
  - ImageSafetyAnalyzer: image file -> unsafe visual-content score.
  - VideoSafetyAnalyzer: video file -> sampled-frame unsafe visual-content score.
  - ImageAuthenticityAnalyzer: image file -> AI-generated score.
  - VideoAuthenticityAnalyzer: video file -> AI/deepfake score.
  - MediaAnalyzer: orchestrates URL download + image/video routing.
"""
from __future__ import annotations

import tempfile
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

MEDIA_MODEL = "Falconsai/nsfw_image_detection"
AI_IMAGE_MODEL = "capcheck/ai-image-detection"
AI_VIDEO_MODEL = "Vansh180/VideoMae-ffc23-deepfake-detector"
MEDIA_THRESHOLD = 0.5
AI_THRESHOLD = 0.5
DOWNLOAD_TIMEOUT_SECONDS = 20
MAX_DOWNLOAD_BYTES = 50 * 1024 * 1024
VIDEO_SAMPLE_SECONDS = 2
MAX_VIDEO_FRAMES = 12
DOWNLOAD_HEADERS = {
    "User-Agent": "SafeNetHackathon/0.1 (educational demo; contact: local)",
}

_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
_VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
_UNSAFE_LABELS = {"nsfw", "porn", "sexy", "hentai", "unsafe"}
_AI_LABEL_HINTS = {"ai", "fake", "generated", "synthetic", "deepfake", "artificial"}
_REAL_LABEL_HINTS = {"real", "human", "authentic", "natural"}


@dataclass
class MediaAnalysis:
    """Compact result returned by media analyzers."""

    is_harmful: bool
    score: float
    category: str
    explanation: str
    model_used: str
    safety_score: float = 0.0
    ai_score: float = 0.0


class PipelineModelProvider:
    """Lazy owner of a Hugging Face pipeline model."""

    def __init__(self, task: str, model_id: str, fallback_name: str, use_model: bool = True):
        self.task = task
        self.model_id = model_id
        self.fallback_name = fallback_name
        self.model = None
        self.model_name = fallback_name
        if use_model:
            self.load()

    def load(self) -> None:
        """Load the configured Hugging Face pipeline."""
        if self.model is not None:
            return
        try:
            from transformers import pipeline

            self.model = pipeline(self.task, model=self.model_id)
            self.model_name = self.model_id
        except Exception as exc:
            print(f"[media] model load failed for {self.model_id}: {exc}")
            self.model = None
            self.model_name = self.fallback_name


class MediaDownloader:
    """Download media URLs to temporary local files."""

    def download(self, media_url: str, target_dir: Path) -> Path:
        """Download a URL to target_dir with timeout and size limits."""
        if self._is_youtube_url(media_url):
            return self._download_youtube(media_url, target_dir)
        return self._download_direct(media_url, target_dir)

    def _download_direct(self, media_url: str, target_dir: Path) -> Path:
        """Download a direct image/video URL with requests."""
        import requests

        parsed = urlparse(media_url)
        suffix = Path(parsed.path).suffix.lower() or ".bin"
        target = target_dir / f"media{suffix}"

        with requests.get(
            media_url,
            stream=True,
            timeout=DOWNLOAD_TIMEOUT_SECONDS,
            headers=DOWNLOAD_HEADERS,
        ) as response:
            response.raise_for_status()
            downloaded = 0
            with target.open("wb") as file:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if not chunk:
                        continue
                    downloaded += len(chunk)
                    if downloaded > MAX_DOWNLOAD_BYTES:
                        raise ValueError("media file is too large")
                    file.write(chunk)

        return target

    def _download_youtube(self, media_url: str, target_dir: Path) -> Path:
        """Download a YouTube URL as a small mp4 with yt-dlp."""
        from yt_dlp import YoutubeDL

        output_template = str(target_dir / "youtube.%(ext)s")
        options = {
            "format": "worst[ext=mp4]/worst",
            "outtmpl": output_template,
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "max_filesize": MAX_DOWNLOAD_BYTES,
        }
        with YoutubeDL(options) as ydl:
            info = ydl.extract_info(media_url, download=True)

        downloaded = Path(ydl.prepare_filename(info))
        if not downloaded.exists():
            matches = list(target_dir.glob("youtube.*"))
            if not matches:
                raise ValueError("yt-dlp did not create a video file")
            downloaded = matches[0]

        if downloaded.suffix.lower() not in _VIDEO_EXTENSIONS:
            mp4_target = target_dir / "youtube.mp4"
            downloaded.rename(mp4_target)
            downloaded = mp4_target

        return downloaded

    def _is_youtube_url(self, media_url: str) -> bool:
        host = urlparse(media_url).netloc.lower()
        return "youtube.com" in host or "youtu.be" in host


class ImageSafetyAnalyzer:
    """Analyze image files for unsafe visual content."""

    def __init__(self, model_provider: PipelineModelProvider):
        self.model_provider = model_provider

    def score_path(self, image_path: Path) -> float:
        """Return only the unsafe-content score for an image."""
        self.model_provider.load()
        if self.model_provider.model is None:
            return 0.0

        from PIL import Image

        with Image.open(image_path) as image:
            results = self.model_provider.model(image.convert("RGB"))

        return _label_score(results, positive_hints=_UNSAFE_LABELS)


class VideoSafetyAnalyzer:
    """Analyze video files by sampling frames and scoring each frame."""

    def __init__(self, image_analyzer: ImageSafetyAnalyzer):
        self.image_analyzer = image_analyzer

    def score_path(self, video_path: Path) -> float:
        """Return the highest unsafe-content score from sampled frames."""
        import cv2
        from PIL import Image

        self.image_analyzer.model_provider.load()
        model = self.image_analyzer.model_provider.model
        if model is None:
            return 0.0

        capture = cv2.VideoCapture(str(video_path))
        if not capture.isOpened():
            return 0.0

        fps = capture.get(cv2.CAP_PROP_FPS) or 25
        frame_step = max(int(fps * VIDEO_SAMPLE_SECONDS), 1)
        frame_index = 0
        sampled = 0
        max_score = 0.0

        try:
            while sampled < MAX_VIDEO_FRAMES:
                ok, frame = capture.read()
                if not ok:
                    break
                if frame_index % frame_step == 0:
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    image = Image.fromarray(rgb_frame)
                    max_score = max(max_score, _label_score(model(image), _UNSAFE_LABELS))
                    sampled += 1
                frame_index += 1
        finally:
            capture.release()

        return max_score if sampled else 0.0


class ImageAuthenticityAnalyzer:
    """Analyze whether an image looks AI-generated."""

    def __init__(self, model_provider: PipelineModelProvider):
        self.model_provider = model_provider

    def score_path(self, image_path: Path) -> float:
        self.model_provider.load()
        if self.model_provider.model is None:
            return 0.0

        from PIL import Image

        with Image.open(image_path) as image:
            results = self.model_provider.model(image.convert("RGB"))
        return _ai_generated_score(results)


class VideoAuthenticityAnalyzer:
    """Analyze whether a video looks AI-generated/deepfake."""

    def __init__(self, model_provider: PipelineModelProvider):
        self.model_provider = model_provider

    def score_path(self, video_path: Path) -> float:
        self.model_provider.load()
        if self.model_provider.model is None:
            return 0.0
        try:
            results = self.model_provider.model(str(video_path))
            return _ai_generated_score(results)
        except Exception as exc:
            print(f"[media] video authenticity failed: {exc}")
            return 0.0


class MediaAnalyzer:
    """Analyze a media URL by delegating to image or video analyzers."""

    def __init__(self, use_model: bool = True):
        self.safety_provider = PipelineModelProvider(
            "image-classification",
            MEDIA_MODEL,
            "media-safety-fallback",
            use_model=use_model,
        )
        self.ai_image_provider = PipelineModelProvider(
            "image-classification",
            AI_IMAGE_MODEL,
            "ai-image-fallback",
            use_model=False,
        )
        self.ai_video_provider = PipelineModelProvider(
            "video-classification",
            AI_VIDEO_MODEL,
            "ai-video-fallback",
            use_model=False,
        )
        self.downloader = MediaDownloader()
        self.image_analyzer = ImageSafetyAnalyzer(self.safety_provider)
        self.video_analyzer = VideoSafetyAnalyzer(self.image_analyzer)
        self.image_authenticity_analyzer = ImageAuthenticityAnalyzer(self.ai_image_provider)
        self.video_authenticity_analyzer = VideoAuthenticityAnalyzer(self.ai_video_provider)

    def analyze_url(self, media_url: str) -> MediaAnalysis:
        """Download media_url and analyze it according to its file type."""
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                media_path = self.downloader.download(media_url, Path(tmpdir))
                media_type = self._media_type(media_path)
                if media_type == "image":
                    safety_score = self.image_analyzer.score_path(media_path)
                    ai_score = self.image_authenticity_analyzer.score_path(media_path)
                    return _result(
                        score=max(safety_score, ai_score),
                        media_type="image",
                        model_used=self._model_used("image"),
                        safety_score=safety_score,
                        ai_score=ai_score,
                    )
                if media_type == "video":
                    safety_score = self.video_analyzer.score_path(media_path)
                    ai_score = self.video_authenticity_analyzer.score_path(media_path)
                    return _result(
                        score=max(safety_score, ai_score),
                        media_type="video",
                        model_used=self._model_used("video"),
                        safety_score=safety_score,
                        ai_score=ai_score,
                    )
                return _fallback(
                    f"unsupported media type: {media_path.suffix}",
                    self._model_used(media_type),
                )
        except Exception as exc:
            return _fallback(f"media analysis failed: {exc}", self._model_used("unknown"))

    def _media_type(self, media_path: Path) -> str:
        suffix = media_path.suffix.lower()
        if suffix in _IMAGE_EXTENSIONS:
            return "image"
        if suffix in _VIDEO_EXTENSIONS:
            return "video"
        return "unknown"

    def _model_used(self, media_type: str) -> str:
        if media_type == "image":
            return f"safety={self.safety_provider.model_name}; ai={self.ai_image_provider.model_name}"
        if media_type == "video":
            return f"safety={self.safety_provider.model_name}; ai={self.ai_video_provider.model_name}"
        return (
            f"safety={self.safety_provider.model_name}; "
            f"ai_image={self.ai_image_provider.model_name}; ai_video={self.ai_video_provider.model_name}"
        )


def _label_score(results: list[dict], positive_hints: set[str]) -> float:
    """Extract the highest score whose label contains a positive hint."""
    scores = [
        float(result["score"])
        for result in results
        if any(hint in result.get("label", "").lower() for hint in positive_hints)
    ]
    return max(scores) if scores else 0.0


def _ai_generated_score(results: list[dict]) -> float:
    """Return probability-like score for AI-generated/fake labels."""
    ai_score = _label_score(results, _AI_LABEL_HINTS)
    if ai_score:
        return ai_score

    # If a detector only exposes real/authentic labels, invert the strongest real score.
    real_score = _label_score(results, _REAL_LABEL_HINTS)
    return 1.0 - real_score if real_score else 0.0


def _result(
    score: float,
    media_type: str,
    model_used: str,
    safety_score: float,
    ai_score: float,
) -> MediaAnalysis:
    is_harmful = safety_score >= MEDIA_THRESHOLD or ai_score >= AI_THRESHOLD
    if safety_score >= MEDIA_THRESHOLD:
        category = "sexual"
    elif ai_score >= AI_THRESHOLD:
        category = "harassment"
    else:
        category = "none"
    return MediaAnalysis(
        is_harmful=is_harmful,
        score=score,
        category=category,
        explanation=(
            f"{media_type} safety_score={safety_score:.2f}, ai_score={ai_score:.2f}, "
            f"safety_threshold={MEDIA_THRESHOLD:.2f}, ai_threshold={AI_THRESHOLD:.2f}"
        ),
        model_used=model_used,
        safety_score=safety_score,
        ai_score=ai_score,
    )


def _fallback(reason: str, model_used: str) -> MediaAnalysis:
    return MediaAnalysis(
        is_harmful=False,
        score=0.0,
        category="none",
        explanation=reason,
        model_used=model_used,
        safety_score=0.0,
        ai_score=0.0,
    )


# Backward-compatible name for older code/tests.
VisionAnalyzer = MediaAnalyzer
