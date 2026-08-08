from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from typing import List, Dict, Any
from app.database.connection import get_session
from app.services.interview_service import InterviewService
from app.repositories.interview_repository import InterviewRepository
from app.schemas.schemas import CreateInterviewRequest, AnswerSubmitRequest, QuestionResponse

router = APIRouter(prefix="/interviews", tags=["Interviews"])

@router.post("/start", response_model=Dict[str, Any])
async def start_interview(request: CreateInterviewRequest, session: Session = Depends(get_session)):
    service = InterviewService(session)
    try:
        state = await service.start_interview(request.candidate_id)
        return {
            "session_id": state["session_id"],
            "status": state["interview_status"],
            "termination_requested": state.get("termination_requested", False),
            "termination_reason": state.get("termination_reason"),
            "current_difficulty": state.get("current_difficulty", 2),
            "current_question": state.get("current_question"),
            "covered_days": state.get("covered_days", []),
            "covered_topics": state.get("covered_topics", [])
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{session_id}", response_model=Dict[str, Any])
def get_interview_session(session_id: str, session: Session = Depends(get_session)):
    repo = InterviewRepository(session)
    sess = repo.get_session(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    questions = repo.get_questions_for_session(session_id)
    answers = repo.get_answers_for_session(session_id)
    evaluations = repo.get_evaluations_for_session(session_id)
    
    current_q = None
    if sess.status not in ["terminated_by_candidate", "completed"] and questions:
        current_q = questions[-1].model_dump()
    
    return {
        "session_id": sess.session_id,
        "candidate_id": sess.candidate_id,
        "status": sess.status,
        "termination_requested": getattr(sess, "termination_requested", False),
        "termination_reason": getattr(sess, "termination_reason", None),
        "started_at": sess.started_at,
        "completed_at": sess.completed_at,
        "current_question_index": sess.current_question_index,
        "questions_answered": sess.questions_answered,
        "difficulty_level": sess.difficulty_level,
        "coverage_percentage": sess.coverage_percentage,
        "overall_score": sess.overall_score,
        "technical_score": sess.technical_score,
        "communication_score": sess.communication_score,
        "covered_days": sess.covered_days,
        "covered_topics": sess.covered_topics,
        "current_question": current_q,
        "question_count": len(questions),
        "answer_count": len(answers),
        "evaluations_count": len(evaluations)
    }

@router.post("/{session_id}/answers", response_model=Dict[str, Any])
async def submit_answer(
    session_id: str,
    request: AnswerSubmitRequest,
    session: Session = Depends(get_session)
):
    service = InterviewService(session)
    try:
        state = await service.submit_answer(session_id, request.answer_text)
        return {
            "session_id": state["session_id"],
            "status": state["interview_status"],
            "termination_requested": state.get("termination_requested", False),
            "termination_reason": state.get("termination_reason"),
            "current_difficulty": state.get("current_difficulty", 2),
            "current_question": state.get("current_question"),
            "last_evaluation": state["evaluations"][-1] if state.get("evaluations") else None,
            "final_feedback": state.get("final_feedback") if state.get("interview_status") == "completed" else None,
            "covered_days": state.get("covered_days", []),
            "covered_topics": state.get("covered_topics", [])
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
