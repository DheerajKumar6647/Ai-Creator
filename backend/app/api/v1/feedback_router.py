from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from app.database.connection import get_session
from app.repositories.feedback_repository import FeedbackRepository
from app.schemas.schemas import FeedbackResponse

router = APIRouter(prefix="/feedback", tags=["Feedback"])

@router.get("/{session_id}", response_model=FeedbackResponse)
def get_feedback(session_id: str, session: Session = Depends(get_session)):
    repo = FeedbackRepository(session)
    report = repo.get_by_session_id(session_id)
    if not report:
        raise HTTPException(status_code=404, detail=f"Feedback report for session {session_id} not found.")
    return FeedbackResponse(**report.model_dump())
