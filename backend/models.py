from typing import Literal
from pydantic import BaseModel


class Message(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class IncomingWSPayload(BaseModel):
    type: Literal["text", "voice"] = "text"  # default to text for backward compatibility
    message: str = ""                        # used when type="text"
    audio: str = ""                          # base64 string, used when type="voice"


class OutgoingWSMessage(BaseModel):
    type: Literal["token", "done", "error", "transcript", "audio"]
    content: str = ""
    message: str = ""  # only used when type="error"