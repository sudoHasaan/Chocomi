import json
import logging

from fastapi import FastAPI, File, Response, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from conversation_manager import ConversationSession
from llm_engine import stream_response
from models import IncomingWSPayload, OutgoingWSMessage
from asr_engine import transcribe
from tts_engine import synthesize

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="TechShop Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.corsOrigins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok", "model": settings.ollamaModel}


@app.post("/api/asr")
async def asr_endpoint(file: UploadFile = File(...)):
    """Accept an audio file and return its transcript."""
    audio_bytes = await file.read()
    transcript = await transcribe(audio_bytes)
    return {"transcript": transcript}


@app.post("/api/tts")
async def tts_endpoint(payload: dict):
    """Accept text and return synthesized speech (WAV)."""
    text = payload.get("text", "")
    if not text:
        return Response(status_code=400, content="Missing 'text' in payload")

    audio_bytes = await synthesize(text)
    return Response(content=audio_bytes, media_type="audio/wav")


@app.post("/chat")
async def chat_rest(payload: IncomingWSPayload):
    session = ConversationSession()
    await session.ingestUserTurn(payload.message)
    messages = session.buildMessages()

    reply_parts: list[str] = []
    async for token in stream_response(messages):
        reply_parts.append(token)

    return {"reply": "".join(reply_parts)}


@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    import base64
    await websocket.accept()
    session = ConversationSession()
    logger.info("WebSocket connection opened")

    try:
        while True:
            raw = await websocket.receive_text()

            try:
                payload = IncomingWSPayload.model_validate(json.loads(raw))
            except Exception:
                err = OutgoingWSMessage(type="error", message="Invalid payload")
                await websocket.send_text(err.model_dump_json())
                continue

            user_text = ""
            if payload.type == "voice":
                if not payload.audio:
                    err = OutgoingWSMessage(type="error", message="Missing audio data")
                    await websocket.send_text(err.model_dump_json())
                    continue
                
                try:
                    audio_bytes = base64.b64decode(payload.audio)
                    user_text = await transcribe(audio_bytes)
                    # Send transcript back to client so they can display it
                    t_msg = OutgoingWSMessage(type="transcript", content=user_text)
                    await websocket.send_text(t_msg.model_dump_json())
                except Exception as e:
                    logger.error("ASR error: %s", e)
                    err = OutgoingWSMessage(type="error", message="Speech recognition failed")
                    await websocket.send_text(err.model_dump_json())
                    continue
            else:
                user_text = payload.message

            if not user_text.strip():
                # If voice was silence/empty, just continue
                continue

            await session.ingestUserTurn(user_text)
            messages = session.buildMessages()

            full_reply: list[str] = []
            try:
                async for token in stream_response(messages):
                    full_reply.append(token)
                    chunk = OutgoingWSMessage(type="token", content=token)
                    await websocket.send_text(chunk.model_dump_json())
            except Exception as e:
                logger.error("LLM error: %s", e)
                err = OutgoingWSMessage(type="error", message="LLM inference failed")
                await websocket.send_text(err.model_dump_json())
                continue

            assistant_reply = "".join(full_reply)
            session.addAssistantTurn(assistant_reply)

            # Generate TTS if it was a voice interaction (or always if we want)
            if payload.type == "voice" and assistant_reply:
                try:
                    audio_bytes = await synthesize(assistant_reply)
                    audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
                    v_msg = OutgoingWSMessage(type="audio", content=audio_b64)
                    await websocket.send_text(v_msg.model_dump_json())
                except Exception as e:
                    logger.error("TTS error: %s", e)
                    # Don't fail the whole chat just because TTS failed

            done = OutgoingWSMessage(type="done")
            await websocket.send_text(done.model_dump_json())

    except WebSocketDisconnect:
        logger.info("WebSocket connection closed")