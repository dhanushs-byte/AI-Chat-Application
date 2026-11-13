import os

from dotenv import load_dotenv
from sqlalchemy.orm import Session

from app.models import Message

load_dotenv()

MAX_HISTORY_TURNS = int(
    os.getenv("MAX_HISTORY_TURNS", "10")
)


SYSTEM_PROMPT = """
You are a helpful AI assistant.
Answer the user clearly and accurately.
"""


def load_full_history(
    db: Session,
    session_id
):

    messages = (
        db.query(Message)
        .filter(Message.session_id == session_id)
        .order_by(Message.created_at.asc(), Message.id.asc())
        .all()
    )

    return [
        {
            "role": message.role,
            "content": message.content
        }
        for message in messages
    ]


def apply_sliding_window(
    history: list,
    max_turns: int = MAX_HISTORY_TURNS
):

    # Preserve the system prompt.
    system_message = {
        "role": "system",
        "content": SYSTEM_PROMPT
    }

    # Keep the latest N user/assistant turns.
    recent_messages = history[-(max_turns * 2):]

    return [system_message] + recent_messages


def get_llm_history(
    db: Session,
    session_id
):

    # Always load complete history from PostgreSQL first.
    full_history = load_full_history(
        db,
        session_id
    )

    # Apply memory trimming only for the LLM context.
    return apply_sliding_window(full_history)