import pytest
import asyncio
from typing import List
from sqlmodel import Session, SQLModel, create_engine

from app.agents.question_generator import is_substantially_similar, normalize_text
from app.database.seed import seed_curriculum, seed_candidates
from app.services.interview_service import InterviewService

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        seed_curriculum(session)
        seed_candidates(session)
        yield session

def test_is_substantially_similar_exact_and_semantic_cases():
    # 1. User Prompt Example 1: Purpose of Vector DB -> DUPLICATE
    q1 = "What is the purpose of a vector database?"
    q2_dup = "Why do we use vector databases for semantic retrieval?"
    assert is_substantially_similar(q2_dup, [q1]) is True, "Expected semantic duplicate to be rejected"

    # 2. User Prompt Example 2: HNSW Acceleration / Speed -> DUPLICATE
    q3 = "How does HNSW accelerate vector search?"
    q4_dup = "How does HNSW improve the speed of vector search?"
    assert is_substantially_similar(q4_dup, [q3]) is True, "Expected speed duplicate to be rejected"

    # 3. User Prompt Example 3: Definition reworded -> DUPLICATE
    q5 = "What is HNSW?"
    q6_dup = "Explain the HNSW algorithm."
    assert is_substantially_similar(q6_dup, [q5]) is True, "Expected definition duplicate to be rejected"

    # 4. User Prompt Example 4: Different technical dimensions -> NOT DUPLICATE
    q7 = "How does HNSW accelerate vector search?"
    q8_valid = "What are the memory overhead trade-offs of HNSW?"
    assert is_substantially_similar(q8_valid, [q7]) is False, "Expected different technical dimension to be allowed"

def test_followup_question_duplicate_enforcement():
    # Follow-up questions must ALSO be checked for semantic duplicates!
    asked = ["What is the purpose of HNSW?"]
    followup_dup = "Why do we use HNSW?"
    assert is_substantially_similar(followup_dup, asked) is True, "Follow-up asking exact duplicate must be rejected"

    followup_valid = "How do ef_construction and M parameters affect HNSW index build latency?"
    assert is_substantially_similar(followup_valid, asked) is False, "Follow-up probing deeper dimension must be allowed"

@pytest.mark.asyncio
async def test_full_8_question_interview_no_duplicates(db_session):
    interview_service = InterviewService(db_session)
    state = await interview_service.start_interview("cand_alex_chen")
    session_id = state["session_id"]

    sample_answers = [
        "Dense vector embeddings represent text in continuous vector space where semantically similar items are close together.",
        "Chunk size trade-offs involve context granularity versus token window overhead and retrieval precision.",
        "HNSW graph indexing constructs multi-layer proximity graphs to enable logarithmic time approximate nearest neighbor search.",
        "Memory overhead in HNSW scales with graph degree M and vector dimensionality, requiring quantization for large datasets.",
        "BM25 provides exact keyword match while dense vectors capture semantic meaning; RRF merges their ordinal ranks.",
        "Context precision measures how relevant retrieved document chunks are relative to the prompt context.",
        "Input guardrails isolate user input using tags and sanitize indirect injections before LLM invocation.",
        "PagedAttention manages KV cache memory allocation in page tables to avoid VRAM memory fragmentation."
    ]

    asked_texts: List[str] = []
    curr_q = state.get("current_question")
    assert curr_q is not None, "Initial question must be generated"
    asked_texts.append(curr_q["question_text"])

    # Run 8 turns
    for i in range(7):
        ans_text = sample_answers[i % len(sample_answers)]
        state = await interview_service.submit_answer(session_id, ans_text)
        
        if state.get("interview_status") == "completed":
            break
            
        curr_q = state.get("current_question")
        if curr_q and curr_q.get("question_text"):
            q_text = curr_q["question_text"]
            # Verify that new question is NOT a duplicate of any previously asked question
            is_dup = is_substantially_similar(q_text, asked_texts)
            assert not is_dup, f"Turn {i+2} generated a duplicate question: '{q_text}' against previous: {asked_texts}"
            asked_texts.append(q_text)

    # Assert no exact or semantic duplicates in entire interview run
    assert len(asked_texts) >= 5, "Interview should generate multiple turns"
    for idx, q_text in enumerate(asked_texts):
        prior_questions = asked_texts[:idx]
        assert not is_substantially_similar(q_text, prior_questions), f"Question {idx+1} '{q_text}' duplicated prior questions {prior_questions}"
