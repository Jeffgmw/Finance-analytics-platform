from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database.connection import get_db
from ..schemas.analytics import AIChatRequest
from ..services.ai_service import chat

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.post("/chat")
async def ai_chat(request: AIChatRequest, db: Session = Depends(get_db)):
    try:
        return await chat(db, request.message)
    except Exception as exc:
        raise HTTPException(
            status_code=502, detail="AI service is temporarily unavailable."
        ) from exc
