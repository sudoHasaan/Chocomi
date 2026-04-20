"""ASR engine – Moonshine (UsefulSensors) running on CPU."""

import asyncio
import logging
import tempfile
import io
from functools import lru_cache

import numpy as np
# import av
from transformers import pipeline

from config import settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _get_pipeline():
    """Lazy-load and cache the Moonshine pipeline (singleton)."""
    logger.info("Loading Moonshine model: %s (cpu)", settings.asrModel)
    asr = pipeline(
        "automatic-speech-recognition",
        model=settings.asrModel,
        device="cpu",
    )
    logger.info("ASR pipeline loaded")
    return asr


def _decode_audio(audio_bytes: bytes, target_sr: int = 16000) -> np.ndarray:
    """
    Decode audio bytes → PCM array (mono, 16kHz).
    Handles WebM, Opus, and raw formats.
    """
    try:
        container = av.open(io.BytesIO(audio_bytes))
        audio_stream = container.streams.audio[0]
        audio_frame_array = []
        for frame in container.decode(audio_stream):
            audio_frame_array.append(frame.to_ndarray())
        if audio_frame_array:
            audio_array = np.concatenate(audio_frame_array, axis=1).squeeze()
        else:
            audio_array = np.array([], dtype=np.float32)
    except Exception as e:
        logger.warning(f"Failed to decode audio: {e}")
        audio_array = np.array([], dtype=np.float32)

    if len(audio_array) == 0:
        return np.array([], dtype=np.float32)

    if audio_array.dtype != np.float32:
        if np.issubdtype(audio_array.dtype, np.integer):
            audio_array = audio_array.astype(np.float32) / np.iinfo(audio_array.dtype).max
        else:
            audio_array = audio_array.astype(np.float32)

    if len(audio_array.shape) > 1:
        audio_array = np.mean(audio_array, axis=0)

    return audio_array


async def transcribe(audio_bytes: bytes) -> str:
    """
    Transcribe raw audio bytes → text using Moonshine.
    Runs in a thread-pool so the async event loop stays free.
    """
    if not audio_bytes:
        return ""

    loop = asyncio.get_running_loop()

    def _run() -> str:
        try:
            audio_array = _decode_audio(audio_bytes)
            if len(audio_array) == 0:
                return ""
            pipeline = _get_pipeline()
            result = pipeline(audio_array)
            logger.info("ASR result: %s", result)
            return result["text"] if isinstance(result, dict) and "text" in result else ""
        except Exception as e:
            logger.error(f"ASR error: {e}")
            return ""

    return await loop.run_in_executor(None, _run)
