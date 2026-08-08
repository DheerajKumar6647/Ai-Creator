import pytest
import asyncio
from sqlmodel import Session, SQLModel, create_engine
from app.database.seed import seed_curriculum, seed_candidates
from app.services.interview_service import InterviewService
from app.repositories.interview_repository import InterviewRepository

@pytest.mark.asyncio
async def test_complete_e2e_interview_flow():
    """
    Complete E2E Integration Test:
    1. Create candidate / seed candidates
    2. Start interview session & receive Question 1
    3. Submit answers & verify evaluations and turn planning through 8 turns
    4. Verify DB persistence of session, questions, answers, evaluations, and final feedback
    5. Verify Start New Interview creates a fresh session without state contamination
    """
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    
    with Session(engine) as session:
        seed_curriculum(session)
        seed_candidates(session)
        service = InterviewService(session)
        repo = InterviewRepository(session)
        
        # 1. Start Interview Session
        cand_id = "cand_alex_chen"
        state = await service.start_interview(cand_id)
        
        session_id_1 = state["session_id"]
        assert session_id_1.startswith("session_")
        assert state["interview_status"] == "in_progress"
        assert state["current_question"] is not None
        assert state["current_question"]["question_text"] != ""
        assert state["current_question"]["question_number"] == 1 if "question_number" in state["current_question"] else True
        
        # Verify DB persistence of Question 1
        db_qs = repo.get_questions_for_session(session_id_1)
        assert len(db_qs) == 1
        assert db_qs[0].question_text == state["current_question"]["question_text"]
        
        # 2. Case A: Submit Weak Answer for Q1
        ans_weak = "I think RAG basically searches a database and gives the result to the LLM."
        state_turn1 = await service.submit_answer(session_id_1, ans_weak)
        
        assert len(state_turn1["questions"]) == 2
        assert len(state_turn1["evaluations"]) == 1
        assert state_turn1["evaluations"][0]["technical_accuracy"] < 7.0
        
        # 3. Submit Answers for Q2 through Q7
        for turn in range(2, 8):
            ans = f"In this step for turn {turn}, dense vector search uses HNSW graph indexing to achieve fast approximate nearest neighbor search with cross-encoder reranking."
            state_turn = await service.submit_answer(session_id_1, ans)
            assert len(state_turn["questions"]) == turn + 1 or state_turn["interview_status"] == "completed"
        
        # 4. Submit Final Answer for Q8
        ans_final = "To prevent indirect prompt injection, NeMo Guardrails inspects input/output payloads with secondary safety classifiers and Pydantic schema validation."
        final_state = await service.submit_answer(session_id_1, ans_final)
        
        assert final_state["interview_status"] == "completed"
        assert final_state["final_feedback"] is not None
        assert final_state["final_feedback"]["overall_rating"] > 0
        
        # Verify DB persistence of completed session and feedback report
        db_session = repo.get_session(session_id_1)
        assert db_session.status == "completed"
        assert db_session.questions_answered >= 8
        assert db_session.overall_score > 0
        
        db_evals = repo.get_evaluations_for_session(session_id_1)
        assert len(db_evals) == 8
        
        # 5. Start New Interview Session (Requirement 10)
        new_state = await service.start_interview(cand_id)
        session_id_2 = new_state["session_id"]
        
        assert session_id_2 != session_id_1
        assert new_state["interview_status"] == "in_progress"
        assert new_state["current_question"] is not None
        assert len(new_state["questions"]) == 1
        assert len(new_state["evaluations"]) == 0
        
        # Verify DB persistence of new session
        db_session_2 = repo.get_session(session_id_2)
        assert db_session_2.session_id == session_id_2
        assert db_session_2.status == "in_progress"
        assert db_session_2.questions_answered == 0
