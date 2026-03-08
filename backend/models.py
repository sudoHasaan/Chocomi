from typing import Literal
from pydantic import BaseModel


class Message(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class IncomingWSPayload(BaseModel):
    message: str


class OutgoingWSMessage(BaseModel):
    type: Literal["token", "done", "error"]
    content: str = ""
    message: str = ""  # only used when type="error"