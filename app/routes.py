from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)

from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ChatSession, Message
from app.schemas import (
    SessionResponse,
    MessageResponse,
    MessageListResponse,
    ChatRequest
)
from app.auth import verify_api_key
import json
import os

from fastapi import Request
from fastapi.responses import StreamingResponse

from app.database import SessionLocal
from app.chat import get_llm_history
from app.llm import (
    create_stream,
    count_tokens,
    calculate_cost
)
from app.rate_limit import check_rate_limit


router = APIRouter(
    dependencies=[Depends(verify_api_key)]
)


# POST /sessions
@router.post(
    "/sessions",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED
)
def create_session(
    db: Session = Depends(get_db)
):

    new_session = ChatSession()

    db.add(new_session)
    db.commit()
    db.refresh(new_session)

    return new_session


# GET /sessions
@router.get(
    "/sessions",
    response_model=list[SessionResponse]
)
def list_sessions(
    db: Session = Depends(get_db)
):

    return (
        db.query(ChatSession)
        .order_by(ChatSession.created_at.desc())
        .all()
    )


# GET /sessions/{session_id}/messages
@router.get(
    "/sessions/{session_id}/messages",
    response_model=MessageListResponse
)
def get_messages(
    session_id: UUID,
    db: Session = Depends(get_db)
):

    session = (
        db.query(ChatSession)
        .filter(ChatSession.id == session_id)
        .first()
    )

    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session not found"
        )

    messages = (
        db.query(Message)
        .filter(Message.session_id == session_id)
        .order_by(Message.created_at.asc(), Message.id.asc())
        .all()
    )

    return {
        "session_id": session_id,
        "messages": messages
    }


# DELETE /sessions/{session_id}
@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_session(
    session_id: UUID,
    db: Session = Depends(get_db)
):

    session = (
        db.query(ChatSession)
        .filter(ChatSession.id == session_id)
        .first()
    )

    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session not found"
        )

    db.delete(session)
    db.commit()

    return None


@router.post("/sessions/{session_id}/chat")
def chat_with_ai(
    session_id: UUID,
    request: ChatRequest,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):

    # 1. Verify session exists
    chat_session = (
        db.query(ChatSession)
        .filter(ChatSession.id == session_id)
        .first()
    )

    if not chat_session:
        raise HTTPException(
            status_code=404,
            detail="Session not found"
        )

    # 2. Check API-key rate limit
    check_rate_limit(db, api_key)

    # 3. Store user message
    user_message = Message(
        session_id=session_id,
        role="user",
        content=request.message,
        tokens=count_tokens(request.message)
    )

    db.add(user_message)
    db.commit()

    # 4. Load complete history and trim for LLM
    history = get_llm_history(db, session_id)

    def generate():

        stream_db = SessionLocal()

        assistant_content = ""

        try:
            # 5. OpenRouter streaming request
            stream = create_stream(history)

            input_tokens = count_tokens(
                " ".join(
                    item["content"]
                    for item in history
                )
            )

            output_tokens = 0

            for chunk in stream:

                # Capture usage information if supplied
                if getattr(chunk, "usage", None):
                    input_tokens = chunk.usage.prompt_tokens
                    output_tokens = chunk.usage.completion_tokens

                if not chunk.choices:
                    continue

                delta = chunk.choices[0].delta
                content = delta.content

                if content:

                    assistant_content += content

                    yield "data: " + json.dumps({
                        "type": "token",
                        "content": content
                    }) + "\n\n"

            # 6. Calculate token usage
            if output_tokens == 0:
                output_tokens = count_tokens(
                    assistant_content
                )

            total_tokens = input_tokens + output_tokens

            cost = calculate_cost(
                input_tokens,
                output_tokens
            )

            # 7. Store final assistant response
            if assistant_content:

                assistant_message = Message(
                    session_id=session_id,
                    role="assistant",
                    content=assistant_content,
                    tokens=output_tokens
                )

                stream_db.add(assistant_message)

                saved_session = (
                    stream_db.query(ChatSession)
                    .filter(ChatSession.id == session_id)
                    .first()
                )

                if saved_session:
                    saved_session.total_tokens += total_tokens
                    saved_session.total_cost += cost

                stream_db.commit()

            # 8. Send usage information
            yield "data: " + json.dumps({
                "type": "done",
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "cost": cost
            }) + "\n\n"

        except Exception:
            stream_db.rollback()

            yield "data: " + json.dumps({
                "type": "error",
                "message": (
                    "The AI service is temporarily unavailable. "
                    "Please try again later."
                )
            }) + "\n\n"

        finally:
            stream_db.close()

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )
