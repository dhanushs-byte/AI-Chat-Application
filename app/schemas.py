from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class SessionResponse(BaseModel):

    id: UUID
    created_at: datetime
    total_tokens: int
    total_cost: float

    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseModel):

    id: int
    session_id: UUID
    role: str
    content: str
    tokens: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MessageListResponse(BaseModel):

    session_id: UUID
    messages: list[MessageResponse]


class ChatRequest(BaseModel):

    message: str = Field(
        min_length=1,
        max_length=10000
    )