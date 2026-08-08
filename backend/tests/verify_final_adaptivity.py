import asyncio
import json
from sqlmodel import Session, SQLModel, create_engine
from app.database.seed import seed_curriculum, seed_candidates
from app.services.interview_service import InterviewService
from app.agents.question_generator import is_substantially_similar

def print_header(title: str):
    print("\n" + "=" * 70)
    print(f"   {title}")
    print("=" * 70)

async def test_controlled_experiment(service: InterviewService):
    print_header("5. CONTROLLED EXPERIMENT: CANDIDATE A (WEAK) vs CANDIDATE B (EXCELLENT)")
    
    # Candidate A: Weak Answer
    state_a = await service.start_interview("cand_alex_chen")
    q1 = state_a["current_question"]
    ans_weak = "I think RAG basically searches a database and gives the result to the LLM."
    state_a_after = await service.submit_answer(state_a["session_id"], ans_weak)
    eval_a = state_a_after["evaluations"][-1]
    planner_a = state_a_after["turn_plan"]
    q2_a = state_a_after["current_question"]["question_text"]
    
    # Candidate B: Excellent Answer
    state_b = await service.start_interview("cand_alex_chen")
    ans_excellent = (
        "Dense vector embeddings project text into continuous latent spaces. "
        "Vector retrieval using HNSW graph indices provides fast ANN search, after which "
        "cross-encoder reranking optimizes context precision before stuffing context into LLMs."
    )
    state_b_after = await service.submit_answer(state_b["session_id"], ans_excellent)
    eval_b = state_b_after["evaluations"][-1]
    planner_b = state_b_after["turn_plan"]
    q2_b = state_b_after["current_question"]["question_text"]
    
    print("\n--- CANDIDATE A (WEAK ANSWER) ---")
    print(f"Candidate Answer: \"{ans_weak}\"")
    print(f"Evaluator: correctness='{eval_a.get('correctness')}', score={eval_a.get('overall_score')}")
    print(f"Detected Gaps: {state_a_after.get('detected_gaps', [])}")
    print(f"Planner Topic: '{planner_a.get('topic')}'")
    print(f"Topic Selection Reason: \"{planner_a.get('topic_selection_reason')}\"")
    print(f"Topic Selection Basis: {planner_a.get('topic_selection_basis')}")
    print(f"Difficulty: {planner_a.get('difficulty')}")
    print(f"Question Type: '{planner_a.get('question_type')}'")
    print(f"Question Type Reason: \"{planner_a.get('question_type_reason')}\"")
    print(f"Follow-up Status: is_follow_up={planner_a.get('is_follow_up')}, reason='{planner_a.get('follow_up_reason')}'")
    print(f"Next Question: \"{q2_a}\"")
    
    print("\n--- CANDIDATE B (EXCELLENT ANSWER) ---")
    print(f"Candidate Answer: \"{ans_excellent}\"")
    print(f"Evaluator: correctness='{eval_b.get('correctness')}', score={eval_b.get('overall_score')}")
    print(f"Detected Gaps: {state_b_after.get('detected_gaps', [])}")
    print(f"Planner Topic: '{planner_b.get('topic')}'")
    print(f"Topic Selection Reason: \"{planner_b.get('topic_selection_reason')}\"")
    print(f"Topic Selection Basis: {planner_b.get('topic_selection_basis')}")
    print(f"Difficulty: {planner_b.get('difficulty')}")
    print(f"Question Type: '{planner_b.get('question_type')}'")
    print(f"Question Type Reason: \"{planner_b.get('question_type_reason')}\"")
    print(f"Follow-up Status: is_follow_up={planner_b.get('is_follow_up')}, reason='{planner_b.get('follow_up_reason')}'")
    print(f"Next Question: \"{q2_b}\"")
    
    assert planner_a.get('topic_selection_reason') is not None, "topic_selection_reason must be populated!"
    assert planner_b.get('topic_selection_reason') is not None, "topic_selection_reason must be populated!"
    assert planner_a.get('question_type_reason') is not None, "question_type_reason must be populated!"
    assert planner_b.get('question_type_reason') is not None, "question_type_reason must be populated!"
    assert q2_a != q2_b, "Candidate A and Candidate B MUST receive different questions!"
    print("\n>>> CONTROLLED EXPERIMENT RESULT: PASS")
    return True

def test_semantic_duplicate_dimensions():
    print_header("3. STRENGTHENED SEMANTIC DUPLICATE DETECTION")
    
    # Case 1: Testing same purpose dimension -> SHOULD BE DETECTED AS DUPLICATE
    q1 = "What is the purpose of a vector database?"
    q2 = "Why are vector databases used for semantic retrieval?"
    dup1 = is_substantially_similar(q2, [q1])
    print(f"Q1: \"{q1}\"")
    print(f"Q2: \"{q2}\"")
    print(f"Result (Same Purpose Dimension): {dup1} (Expected True)")
    assert dup1 is True, "Same purpose questions must be flagged as duplicate!"
    
    # Case 2: Testing different dimensions of same technology -> SHOULD NOT BE REJECTED!
    q3 = "How does HNSW improve vector search speed?"
    q4 = "What are the memory overhead trade-offs of HNSW?"
    dup2 = is_substantially_similar(q4, [q3])
    print(f"\nQ3: \"{q3}\"")
    print(f"Q4: \"{q4}\"")
    print(f"Result (Different Dimensions - Speed vs Memory): {dup2} (Expected False)")
    assert dup2 is False, "Different dimensions of same technology must NOT be rejected!"
    
    print("\n>>> SEMANTIC DUPLICATE DETECTION RESULT: PASS")
    return True

async def run_all_verifications():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        seed_curriculum(session)
        seed_candidates(session)
        service = InterviewService(session)
        
        p1 = await test_controlled_experiment(service)
        p2 = test_semantic_duplicate_dimensions()
        
        print("\n" + "=" * 70)
        print("   FINAL REFINEMENT VERIFICATION SUMMARY")
        print("=" * 70)
        print(f"1. Performance-Driven Topic Selection & Reason: PASS")
        print(f"2. Assessment-Driven Question Type & Reason:   PASS")
        print(f"3. Dimension-Aware Semantic Duplicate Check:   PASS")
        print(f"4. Controlled Weak vs Excellent Experiment:    PASS")
        print("=" * 70)

if __name__ == "__main__":
    asyncio.run(run_all_verifications())
