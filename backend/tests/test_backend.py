import pytest
import asyncio
from sqlmodel import Session, SQLModel, create_engine
from app.models.candidate import Candidate
from app.models.curriculum import CurriculumDayModel, CurriculumTopicModel
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.curriculum_repository import CurriculumRepository
from app.services.llm_provider import LLMProvider
from app.services.interview_service import InterviewService
from app.database.seed import seed_curriculum, seed_candidates

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        seed_curriculum(session)
        seed_candidates(session)
        yield session

def test_seed_and_repositories(db_session):
    cand_repo = CandidateRepository(db_session)
    curr_repo = CurriculumRepository(db_session)
    
    candidates = cand_repo.list_all()
    assert len(candidates) >= 3
    alex = cand_repo.get_by_id("cand_alex_chen")
    assert alex is not None
    assert alex.name == "Alex Chen"
    
    days = curr_repo.get_all_days()
    assert len(days) >= 5
    topics = curr_repo.get_topics_for_day(7)
    assert len(topics) > 0
    assert topics[0].topic_id == "day7_chunking"

@pytest.mark.asyncio
async def test_llm_provider_mock():
    provider = LLMProvider(provider_type="mock")
    plan = await provider.generate_json("Planner strategy prompt")
    assert "target_question_count" in plan
    assert plan["target_question_count"] == 8

@pytest.mark.asyncio
async def test_interview_start(db_session):
    service = InterviewService(db_session)
    state = await service.start_interview("cand_alex_chen")
    
    assert state["session_id"] is not None
    assert state["interview_status"] == "in_progress"
    assert state["current_question"] is not None
    assert isinstance(state["current_question"], dict)
    assert "question_text" in state["current_question"] or "question_id" in state["current_question"]
