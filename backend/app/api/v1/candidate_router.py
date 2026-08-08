from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from typing import List
from app.database.connection import get_session
from app.repositories.candidate_repository import CandidateRepository
from app.schemas.schemas import CandidateResponse

import uuid
from app.models.candidate import Candidate
from app.schemas.schemas import CandidateResponse, CreateCandidateRequest

router = APIRouter(prefix="/candidates", tags=["Candidates"])

@router.get("", response_model=List[CandidateResponse])
def get_candidates(session: Session = Depends(get_session)):
    repo = CandidateRepository(session)
    candidates = repo.list_all()
    return [CandidateResponse(**c.model_dump()) for c in candidates]

@router.post("", response_model=CandidateResponse)
def create_candidate(request: CreateCandidateRequest, session: Session = Depends(get_session)):
    repo = CandidateRepository(session)
    cand_id = f"cand_{uuid.uuid4().hex[:8]}"
    cand_obj = Candidate(
        id=cand_id,
        name=request.name,
        email=request.email,
        target_role=request.target_role or "AI Engineer",
        experience_level=request.experience_level or "Mid-Senior",
        years_of_experience=request.years_of_experience if request.years_of_experience is not None else 3.0,

        primary_skills=request.primary_skills or ["Python", "LLMs", "RAG"],
        resume_summary=request.resume_summary or "",
        completed_days=[1, 2, 6],
        skipped_days=[],
        attempts=0,
        completion_percentage=25.0,
        learning_signals={
            "average_score": 7.5,
            "strong_topics": ["day1_tokenization", "day6_vector_embeddings"],
            "weak_topics": ["day8_vector_databases"],
            "likely_knowledge_gaps": ["HNSW index trade-offs", "Cross-Encoder reranking"],
            "preferred_difficulty": 2
        }
    )
    created = repo.create_candidate(cand_obj)
    return CandidateResponse(**created.model_dump())

@router.get("/{candidate_id}", response_model=CandidateResponse)
def get_candidate(candidate_id: str, session: Session = Depends(get_session)):
    repo = CandidateRepository(session)
    candidate = repo.get_by_id(candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail=f"Candidate {candidate_id} not found")
    return CandidateResponse(**candidate.model_dump())

@router.delete("/{candidate_id}")
def delete_candidate(candidate_id: str, session: Session = Depends(get_session)):
    repo = CandidateRepository(session)
    deleted = repo.delete(candidate_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Candidate {candidate_id} not found")
    return {"message": f"Candidate {candidate_id} deleted successfully", "success": True}

