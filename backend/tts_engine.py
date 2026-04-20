"""TTS engine – Piper TTS running on CPU."""

import asyncio
import logging
import os
from functools import lru_cache
from pathlib import Path

# from piper.voice import PiperVoice

from config import settings

logger = logging.getLogger(__name__)


# @lru_cache(maxsize=1)
# def _get_voice() -> PiperVoice:
#     """Lazy-load and cache the Piper voice (singleton)."""
#     # Piper models consist of a .onnx file and a .onnx.json config
#     model_path = Path(settings.ttsDataDir) / f"{settings.ttsModel}.onnx"
#     config_path = Path(settings.ttsDataDir) / f"{settings.ttsModel}.onnx.json"
#
#     if not model_path.exists():
#         logger.error(f"TTS Model not found at {model_path}. Please ensure it is downloaded.")
#         # In a real production system, we'd handle auto-download here.
#         # For now, we'll raise an error if missing.
#         raise FileNotFoundError(f"Missing Piper model: {model_path}")
#
#     logger.info("Loading Piper voice: %s", settings.ttsModel)
#     voice = PiperVoice.load(str(model_path), config_path=str(config_path), use_cuda=False)
#     logger.info("TTS voice loaded")
#     return voice


async def synthesize(text: str) -> bytes:
    """
    Synthesize text → WAV bytes.

    Runs in a thread-pool so the async event loop stays free.
    """
    loop = asyncio.get_running_loop()

    def _run() -> bytes:
        try:
            import io
            import wave
            voice = _get_voice()
            buf = io.BytesIO()
            with wave.open(buf, "wb") as wav_file:
                voice.synthesize_wav(text, wav_file)
            return buf.getvalue()
        except Exception as e:
            logger.error(f"TTS error: {e}")
            return b""

    return await loop.run_in_executor(None, _run)
