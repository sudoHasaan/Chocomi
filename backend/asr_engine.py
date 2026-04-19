"""ASR engine – Moonshine (UsefulSensors) running on CPU."""

import asyncio
import logging
import tempfile
import io
from functools import lru_cache

import numpy as np
import av
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
    Decode audio bytes (WebM/Opus/WAV) to float32 numpy array at target_sr.
    Uses 'av' (PyAV) for portable decoding without needing system FFmpeg.
    """
    with io.BytesIO(audio_bytes) as file_obj:
        with av.open(file_obj) as container:
            resampler = av.AudioResampler(
                format='s16',
                layout='mono',
                rate=target_sr,
            )
            
            frames = []
            for frame in container.decode(audio=0):
                # Resample frame to 16kHz mono
                resampled_frames = resampler.resample(frame)
                for f in resampled_frames:
                    frames.append(f.to_ndarray())
            
            if not frames:
                return np.array([], dtype=np.float32)
                
            # Combine and convert to float32 in range [-1, 1]
            audio_data = np.concatenate(frames, axis=1).reshape(-1)
            return audio_data.astype(np.float32) / 32768.0


async def transcribe(audio_bytes: bytes) -> str:
    """
    Transcribe raw audio bytes → text using Moonshine.
    """
    loop = asyncio.get_running_loop()

    def _run() -> str:
        try:
            # Decode using PyAV (doesn't need system ffmpeg)
            audio = _decode_audio(audio_bytes, target_sr=16000)
            
            if audio.size == 0:
                logger.warning("Decoded audio is empty")
                return ""

            asr = _get_pipeline()
            # Moonshine inference
            result = asr({"array": audio, "sampling_rate": 16000})
            return result["text"].strip()
        except Exception as e:
            logger.error("Transcription failed", exc_info=True)
            return ""

    return await loop.run_in_executor(None, _run)
