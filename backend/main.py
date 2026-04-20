import json
import logging
import re

from fastapi import FastAPI, File, Response, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from conversation_manager import ConversationSession
from llm_engine import stream_response
from models import IncomingWSPayload, OutgoingWSMessage
from asr_engine import transcribe
from tts_engine import synthesize
from crm_store import add_interaction, get_user_info
from tools import calculate, get_current_time, get_weather

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


@app.get("/api/crm/user/{user_id}")
async def crm_user_profile(user_id: str):
    return get_user_info(user_id)


def _extract_math_expression(text: str) -> str:
    pattern = r"\b[0-9][0-9\s\+\-\*\/\(\)\.]*[0-9]\b"
    matches = re.findall(pattern, text)
    if not matches:
        return ""
    candidate = max(matches, key=len).strip()
    return candidate if any(op in candidate for op in ["+", "-", "*", "/"]) else ""


def _extract_weather_location(text: str) -> str:
    m = re.search(r"weather\s+(?:in|for)\s+([A-Za-z\s]{2,40})", text, re.IGNORECASE)
    if not m:
        return "Karachi"
    location = re.sub(r"\s+", " ", m.group(1)).strip(" .,!?")
    # Strip common trailing filler phrases from natural questions.
    location = re.sub(r"\b(expected\s+to\s+be\s+like|like|today|now|currently|right\s+now)\b.*$", "", location, flags=re.IGNORECASE).strip(" .,!?")
    return location or "Karachi"


async def _maybe_answer_with_direct_tools(user_text: str) -> str | None:
    lower = user_text.lower()
    wants_time = bool(
        re.search(r"\b(what\s+time|current\s+time|time\s+is\s+it|what's\s+the\s+time|what\s+is\s+the\s+time|today|date)\b", lower)
    )
    wants_weather = "weather" in lower
    expression = _extract_math_expression(user_text)
    wants_math = bool(expression)

    if not (wants_time or wants_weather or wants_math):
        return None

    parts: list[str] = []
    if wants_math:
        math_result = await calculate(expression)
        parts.append(f"{expression} = {math_result}.")

    if wants_time:
        time_result = await get_current_time()
        parts.append(f"Current time is {time_result}.")

    if wants_weather:
        location = _extract_weather_location(user_text)
        weather_result = await get_weather(location)
        parts.append(f"Current weather in {location}: {weather_result}.")

    return " ".join(parts).strip()


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
    session = ConversationSession(userId=payload.userId or "anonymous-rest")
    await session.ingestUserTurn(payload.message)

    direct_reply = await _maybe_answer_with_direct_tools(payload.message)
    if direct_reply:
        session.addAssistantTurn(direct_reply)
        return {"reply": direct_reply}

    messages = session.buildMessages()

    reply_parts: list[str] = []
    async for token in stream_response(messages):
        reply_parts.append(token)

    return {"reply": "".join(reply_parts)}


@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    import base64
    await websocket.accept()
    user_id = websocket.query_params.get("user_id", "anonymous-websocket")
    session = ConversationSession(userId=user_id)
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

            # Allow payload-level user override for compatibility with existing clients.
            if payload.userId:
                user_id = payload.userId

            if not user_text.strip():
                # If voice was silence/empty, just continue
                continue

            await session.ingestUserTurn(user_text)
            add_interaction(user_id, f"user: {user_text}")

            direct_reply = await _maybe_answer_with_direct_tools(user_text)
            if direct_reply:
                for word in direct_reply.split(" "):
                    if word:
                        chunk = OutgoingWSMessage(type="token", content=word + " ")
                        await websocket.send_text(chunk.model_dump_json())

                session.addAssistantTurn(direct_reply)
                add_interaction(user_id, f"assistant: {direct_reply}")
                done = OutgoingWSMessage(type="done")
                await websocket.send_text(done.model_dump_json())
                continue

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
            add_interaction(user_id, f"assistant: {assistant_reply}")

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