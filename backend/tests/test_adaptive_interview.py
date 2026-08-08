import pytest
import asyncio
from sqlmodel import Session, SQLModel, create_engine
from app.database.seed import seed_curriculum, seed_candidates
from app.services.interview_service import InterviewService
from app.agents.question_generator import is_substantially_similar

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        seed_curriculum(session)
        seed_candidates(session)
        yield session

def test_duplicate_question_prevention_logic():
    asked = [
        "Explain how subword tokenization like BPE handles out of vocabulary tokens.",
        "What is RAG and how does it retrieve relevant context?"
    ]

    # Similar conceptual questions should be detected
    assert is_substantially_similar("What is RAG and how does it retrieve relevant context?", asked) == True
    assert is_substantially_similar("Can you explain how subword tokenization like BPE handles out of vocabulary tokens?", asked) == True

    # Truly different questions should pass
    assert is_substantially_similar("Compare HNSW graph indexing with IVF inverted file indices in vector databases.", asked) == False

@pytest.mark.asyncio
async def test_adaptive_followup_and_difficulty_progression(db_session):
    service = InterviewService(db_session)
    state = await service.start_interview("cand_alex_chen")
    session_id = state["session_id"]

    q1 = state["current_question"]
    assert q1 is not None
    assert "question_text" in q1

    # Turn 1: Candidate gives a shallow/poor answer to Q1
    poor_ans = "RAG retrieves relevant documents and gives them to the model."
    state = await service.submit_answer(session_id, poor_ans)

    q2 = state["current_question"]
    assert q2["question_id"] != q1["question_id"]
    # Q2 should be a follow-up or targeted scenario probing the weakness
    eval1 = state["evaluations"][-1]
    assert eval1["correctness"] in ["shallow", "partially_correct", "incorrect"]
    assert len(state["detected_gaps"]) > 0

    # Turn 2: Candidate gives a strong, detailed answer to Q2
    strong_ans = "To diagnose irrelevant retrieval, I would inspect chunking overlap, check embedding model dimension alignment, compare BM25 keyword search with dense Cosine similarity, and add a Cross-Encoder reranker to re-score candidate chunks."
    state = await service.submit_answer(session_id, strong_ans)

    q3 = state["current_question"]
    assert q3["question_id"] != q2["question_id"]
    eval2 = state["evaluations"][-1]
    assert eval2["correctness"] == "correct"

    # Turn 3: Candidate continues to give strong answers -> verify topic switch or difficulty increase
    ans3 = "For 50 million embeddings, I would migrate from flat L2 search to an HNSW graph index or IVF-PQ vector index, shard vectors across distributed nodes using Pinecone or Qdrant, and filter metadata at query time using pre-filtering."
    state = await service.submit_answer(session_id, ans3)

    assert len(state["questions"]) >= 3
    # Check that questions do not duplicate
    asked_texts = [q["question_text"] for q in state["questions"]]
    for i, t1 in enumerate(asked_texts):
        for j, t2 in enumerate(asked_texts):
            if i != j:
                assert not is_substantially_similar(t1, [t2]), f"Duplicate detected between Q{i+1} and Q{j+1}: '{t1}' vs '{t2}'"

@pytest.mark.asyncio
async def test_full_adaptive_scenario_and_final_acceptance(db_session):
    service = InterviewService(db_session)
    state = await service.start_interview("cand_alex_chen")
    session_id = state["session_id"]

    answers_script = [
        # Q1 answer: Shallow
        "RAG retrieves relevant documents and gives them to the model.",
        # Q2 answer: Strong detailed response
        "To improve retrieval quality, I would implement hybrid search with BM25 and dense vector embeddings using Reciprocal Rank Fusion, followed by a Cross-Encoder reranker to score top 50 passages.",
        # Q3 answer: Strong response
        "At 50 million embeddings, flat vector search becomes too slow. I would construct an HNSW index with ef_construction=200 and M=16, or use IVF-PQ to compress vectors into product-quantized centroids to reduce memory consumption.",
        # Q4 answer: Shallow response
        "Approximate nearest neighbor search speeds up query time.",
        # Q5 answer: Strong detailed response
        "ANN search trades search recall accuracy for logarithmic QPS throughput by searching a multi-layer graph rather than comparing every vector in dataset.",
        # Q6 answer: Strong response
        "LangGraph uses state graph nodes and conditional edge functions to build cyclic, deterministic agent loops with persistence checkpointers.",
        # Q7 answer: Strong response
        "NeMo Guardrails and Llama Guard classify inputs and outputs to prevent prompt injection and secret data leakage.",
        # Q8 answer: Strong response
        "RAGAS evaluation calculates Faithfulness, Answer Relevance, and Context Recall using automated LLM-as-a-Judge rubrics."
    ]

    turn = 0
    fallback_answers = [
        "Subword tokenization splits words into subwords like BPE and WordPiece to handle out of vocabulary words efficiently.",
        "Structured outputs use JSON schema grammar constraints during LLM sampling to guarantee valid Pydantic fields.",
        "Vector embeddings map high dimensional text representations into continuous vector space for dense semantic retrieval.",
        "NeMo Guardrails inspect input and output payloads with secondary safety classifiers and Pydantic schema validation."
    ]
    while state.get("interview_status") != "completed" and turn < 12:
        ans = answers_script[turn] if turn < len(answers_script) else fallback_answers[(turn - len(answers_script)) % len(fallback_answers)]
        turn += 1
        state = await service.submit_answer(session_id, ans)


    # Verification assertions
    assert state["interview_status"] == "completed"
    assert len(state["questions"]) >= 8
    assert len(state["covered_days"]) >= 4
    assert state["final_feedback"] is not None

    fb = state["final_feedback"]
    assert "hiring_recommendation" in fb
    assert "strengths" in fb
    assert "weaknesses" in fb
    assert "overall_score" in fb or "overall_rating" in fb

    # Verify no question duplication across whole session
    all_q_texts = [q["question_text"] for q in state["questions"]]
    assert len(set(all_q_texts)) == len(all_q_texts), "Question texts must be unique!"

    for i in range(len(all_q_texts)):
        for j in range(i + 1, len(all_q_texts)):
            assert not is_substantially_similar(all_q_texts[i], [all_q_texts[j]]), f"Questions Q{i+1} and Q{j+1} are conceptually duplicate: '{all_q_texts[i]}' vs '{all_q_texts[j]}'"

    print(f"Final Acceptance Test Passed! Questions: {len(state['questions'])}, Covered Days: {len(state['covered_days'])}, Decision: {fb.get('hiring_recommendation')}")
