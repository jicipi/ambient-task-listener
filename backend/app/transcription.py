from __future__ import annotations

import tempfile
import time
from pathlib import Path

import mlx_whisper

from app.logger import get_logger

logger = get_logger(__name__)

DEFAULT_MODEL = "mlx-community/whisper-small-mlx"
# DEFAULT_MODEL = "mlx-community/whisper-large-v3-turbo"


def transcribe_audio_file(audio_path: str, model_name: str = DEFAULT_MODEL) -> str:
    path = Path(audio_path)

    if not path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    t0 = time.perf_counter()

    result = mlx_whisper.transcribe(
        str(path),
        path_or_hf_repo=model_name,
        language="fr",
    )

    dt = time.perf_counter() - t0
    logger.info("transcription en %.2fs avec %s", dt, model_name)

    text = result.get("text", "").strip()
    return text


def transcribe_bytes_to_text(
    audio_bytes: bytes,
    suffix: str = ".wav",
    model_name: str = DEFAULT_MODEL,
) -> str:
    with tempfile.NamedTemporaryFile(delete=True, suffix=suffix) as tmp:
        tmp.write(audio_bytes)
        tmp.flush()
        return transcribe_audio_file(tmp.name, model_name=model_name)