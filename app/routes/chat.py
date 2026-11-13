from fastapi import APIRouter, Depends
from app.schemas import ChatRequest, ChatResponse
from app.auth import verify_api_key

router = APIRouter()


@router.post(
    "/chat",
    response_model=ChatResponse
)
async def chat_with_ai(
    request: ChatRequest,
    api_key: str = Depends(verify_api_key)
):
    return ChatResponse(
        response="Chat endpoint is working",
        session_id="test-session"
    )