"""ASR engine – faster-whisper (CTranslate2) running on CPU."""

import asyncio
import io
import logging
import tempfile
from functools import lru_cache

from faster_whisper import WhisperModel

from config import settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _get_model() -> WhisperModel:
    """Lazy-load and cache the Whisper model (singleton)."""
    logger.info("Loading faster-whisper model: %s (cpu)", settings.asrModel)
    model = WhisperModel(
        settings.asrModel,
        device="cpu",
        compute_type="int8",     # fastest quantisation for CPU
    )
    logger.info("ASR model loaded")
    return model


async def transcribe(audio_bytes: bytes) -> str:
    """
    Transcribe raw audio bytes (any ffmpeg-supported format) → text.

    Runs inference in a thread-pool so the async event loop stays free.
    """
    loop = asyncio.get_running_loop()

    def _run() -> str:
        # Write bytes to a temp file (faster-whisper needs a path or file-like)
        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        model = _get_model()
        segments, _info = model.transcribe(
            tmp_path,
            beam_size=1,          # greedy → fastest
            language="en",
            vad_filter=True,      # skip silence
        )
        text = " ".join(seg.text.strip() for seg in segments)
        return text.strip()

    return await loop.run_in_executor(None, _run)
