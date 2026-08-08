import pytest
import asyncio
from sqlmodel import Session, SQLModel, create_engine
from app.database.seed import seed_curriculum, seed_candidates
from app.services.interview_service import InterviewService
from app.agents.question_generator import validate_question_grounding, question_generator_node

def test_critical_regression_speculative_decoding_rejection():
    """
    CRITICAL REGRESSION TEST:
    Verify that an unrelated question (e.g. speculative decoding) is REJECTED
    when the turn plan topic is day6_vector_embeddings and target concept is ANN indexing.
    """
    turn_plan = {
        "topic": "day6_vector_embeddings",
        "target_concept": "ANN indexing",
        "is_follow_up": True,
        "follow_up_reason": "missing_concept"
    }
    
    unrelated_q = {
        "question_text": "How does speculative decoding accelerate LLM generation?",
        "topic": "day6_vector_embeddings"
    }
    
    val = validate_question_grounding(unrelated_q, turn_plan, [])
    print(f"Validation Result for Speculative Decoding on Embeddings Topic: {val}")
    
    assert val["grounding_valid"] is False, "Speculative decoding question MUST be rejected for vector embeddings topic!"
    assert val["topic_aligned"] is False, "Topic alignment MUST fail!"

def test_a_trade_off_question_accepted():
    turn_plan = {"topic": "day8_vector_databases", "question_type": "trade_off"}
    q_data = {"question_text": "What are the latency vs recall trade-offs of HNSW index parameters?", "topic": "day8_vector_databases", "question_type": "trade_off"}
    val = validate_question_grounding(q_data, turn_plan, [])
    assert val["question_type_aligned"] is True
    assert val["grounding_valid"] is True

def test_b_conceptual_question_rejected_when_trade_off_required():
    turn_plan = {"topic": "day8_vector_databases", "question_type": "trade_off"}
    q_data = {"question_text": "What is HNSW?", "topic": "day8_vector_databases", "question_type": "conceptual"}
    val = validate_question_grounding(q_data, turn_plan, [])
    assert val["question_type_aligned"] is False
    assert val["grounding_valid"] is False

def test_c_system_design_question_accepted():
    turn_plan = {"topic": "day8_vector_databases", "question_type": "system_design"}
    q_data = {"question_text": "Design a vector retrieval architecture for 100M documents with low-latency search.", "topic": "day8_vector_databases", "question_type": "system_design"}
    val = validate_question_grounding(q_data, turn_plan, [])
    assert val["question_type_aligned"] is True
    assert val["grounding_valid"] is True

def test_d_generic_topic_question_rejected_when_target_concept_required():
    turn_plan = {"topic": "day6_vector_embeddings", "is_follow_up": True, "target_concept": "ANN indexing"}
    q_data = {"question_text": "What are vector embeddings?", "topic": "day6_vector_embeddings"}
    val = validate_question_grounding(q_data, turn_plan, [])
    assert val["target_concept_aligned"] is False
    assert val["grounding_valid"] is False

def test_e_valid_target_concept_followup_accepted():
    turn_plan = {"topic": "day8_vector_databases", "is_follow_up": True, "target_concept": "ANN indexing"}
    q_data = {"question_text": "How does HNSW indexing enable approximate nearest-neighbor search?", "topic": "day8_vector_databases"}
    val = validate_question_grounding(q_data, turn_plan, [])
    assert val["target_concept_aligned"] is True
    assert val["grounding_valid"] is True


@pytest.mark.asyncio
async def test_1_weak_rag_answer_grounding():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        seed_curriculum(session)
        seed_candidates(session)
        service = InterviewService(session)
        
        state = await service.start_interview("cand_alex_chen")
        ans_weak = "I think RAG basically searches a database and gives the result to the LLM."
        state_after = await service.submit_answer(state["session_id"], ans_weak)
        
        q2 = state_after["current_question"]["question_text"]
        q2_topic = state_after["current_question"]["topic"]
        
        print(f"Test 1 Q2 Text: \"{q2}\"")
        print(f"Test 1 Q2 Topic: {q2_topic}")
        
        # Speculative decoding must NEVER appear for vector / RAG topics
        assert "speculative decoding" not in q2.lower(), "Unrelated speculative decoding question MUST NOT appear!"
        assert state_after["current_question"].get("grounding_validation", {}).get("grounding_valid") is True, "Grounding validation must be True!"

@pytest.mark.asyncio
async def test_2_misconception_grounding():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        seed_curriculum(session)
        seed_candidates(session)
        service = InterviewService(session)
        
        state = await service.start_interview("cand_alex_chen")
        ans_misc = "Vector databases always guarantee exact nearest-neighbor search."
        state_after = await service.submit_answer(state["session_id"], ans_misc)
        
        q2 = state_after["current_question"]["question_text"]
        print(f"Test 2 Q2 Text: \"{q2}\"")
        
        assert any(k in q2.lower() for k in ["exact", "ann", "hnsw", "vector", "search", "retrieval", "index"]), "Follow-up MUST concern vector search / ANN!"
        assert "speculative decoding" not in q2.lower()

@pytest.mark.asyncio
async def test_3_strong_embeddings_to_vector_db():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        seed_curriculum(session)
        seed_candidates(session)
        service = InterviewService(session)
        
        state = await service.start_interview("cand_alex_chen")
        ans_strong = "Dense vector embeddings project text into continuous latent spaces. Vector retrieval using HNSW graph indices provides fast ANN search."
        state_after = await service.submit_answer(state["session_id"], ans_strong)
        
        q2 = state_after["current_question"]["question_text"]
        q2_topic = state_after["current_question"]["topic"]
        print(f"Test 3 Q2 Text: \"{q2}\", Topic: {q2_topic}")
        
        assert q2_topic in ["day8_vector_databases", "day6_vector_embeddings", "day9_rag_pipelines"], "New topic must belong to curriculum vector domain!"
        assert "speculative decoding" not in q2.lower()

@pytest.mark.asyncio
async def test_4_chunking_weakness_grounding():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        seed_curriculum(session)
        seed_candidates(session)
        service = InterviewService(session)
        
        state = await service.start_interview("cand_alex_chen")
        ans_chunk = "Chunking splits text into smaller pieces, but I don't know how chunk overlap affects search precision."
        state_after = await service.submit_answer(state["session_id"], ans_chunk)
        
        q2 = state_after["current_question"]["question_text"]
        print(f"Test 4 Q2 Text: \"{q2}\"")
        assert any(k in q2.lower() for k in ["chunk", "overlap", "context", "precision", "retrieval", "vector", "search"])

@pytest.mark.asyncio
async def test_5_off_topic_redirect_grounding():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        seed_curriculum(session)
        seed_candidates(session)
        service = InterviewService(session)
        
        state = await service.start_interview("cand_alex_chen")
        ans_off = "I like cooking pasta on sunny weekends."
        state_after = await service.submit_answer(state["session_id"], ans_off)
        
        q2 = state_after["current_question"]["question_text"]
        print(f"Test 5 Q2 Text: \"{q2}\"")
        assert state_after.get("off_topic_action") in ["redirect", "pivot"]
        assert "cooking" not in q2.lower()

@pytest.mark.asyncio
async def test_6_strong_answer_new_topic_grounding():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        seed_curriculum(session)
        seed_candidates(session)
        service = InterviewService(session)
        
        state = await service.start_interview("cand_alex_chen")
        ans_strong = "Cross-encoder rerankers re-score candidate documents by jointly processing query and text, yielding superior precision compared to bi-encoder retrieval alone."
        state_after = await service.submit_answer(state["session_id"], ans_strong)
        
        q2_topic = state_after["current_question"]["topic"]
        q2 = state_after["current_question"]["question_text"]
        print(f"Test 6 Q2 Topic: {q2_topic}, Text: \"{q2}\"")
        
        assert state_after["current_question"].get("grounding_validation", {}).get("grounding_valid") is True
