from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from typing import List
from app.database.connection import get_session
from app.repositories.curriculum_repository import CurriculumRepository
from app.schemas.schemas import CurriculumDayResponse, CurriculumTopicResponse

router = APIRouter(prefix="/curriculum", tags=["Curriculum"])

@router.get("", response_model=List[CurriculumDayResponse])
def get_curriculum(session: Session = Depends(get_session)):
    repo = CurriculumRepository(session)
    days = repo.get_all_days()
    result = []
    for d in days:
        topics = repo.get_topics_for_day(d.day_number)
        t_responses = [CurriculumTopicResponse(**t.model_dump()) for t in topics]
        day_dict = d.model_dump()
        day_dict["topics"] = t_responses
        result.append(CurriculumDayResponse(**day_dict))
    return result

@router.get("/days/{day_number}", response_model=CurriculumDayResponse)
def get_day(day_number: int, session: Session = Depends(get_session)):
    repo = CurriculumRepository(session)
    d = repo.get_day(day_number)
    if not d:
        raise HTTPException(status_code=404, detail=f"Day {day_number} not found")
    topics = repo.get_topics_for_day(day_number)
    t_responses = [CurriculumTopicResponse(**t.model_dump()) for t in topics]
    day_dict = d.model_dump()
    day_dict["topics"] = t_responses
    return CurriculumDayResponse(**day_dict)
