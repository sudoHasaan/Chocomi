import json
import logging

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from conversation_manager import ConversationSession
from llm_engine import stream_response
from models import IncomingWSPayload, OutgoingWSMessage

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


@app.post("/chat")
async def chat_rest(payload: IncomingWSPayload):
    session = ConversationSession()
    session.addUserTurn(payload.message)
    messages = session.build_messages()

    reply_parts: list[str] = []
    async for token in stream_response(messages):
        reply_parts.append(token)

    return {"reply": "".join(reply_parts)}


@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
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

            session.addUserTurn(payload.message)
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

            session.addAssistantTurn("".join(full_reply))

            done = OutgoingWSMessage(type="done")
            await websocket.send_text(done.model_dump_json())

    except WebSocketDisconnect:
        logger.info("WebSocket connection closed")