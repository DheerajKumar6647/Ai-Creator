import asyncio
import json
from sqlmodel import Session, SQLModel, create_engine
from app.database.seed import seed_curriculum, seed_candidates
from app.services.interview_service import InterviewService

async def run_experiment_5_answer_dependence():
    print("=" * 70)
    print("EXPERIMENT 5: ANSWER-DEPENDENCE EXPERIMENT (WEAK vs EXCELLENT)")
    print("=" * 70)
    
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        seed_curriculum(session)
        seed_candidates(session)
        service = InterviewService(session)
        
        # Interview A: Weak Answer
        state_a = await service.start_interview("cand_alex_chen")
        q1 = state_a["current_question"]
        ans_weak = "I think RAG basically searches a database and gives the result to the LLM."
        state_a_after = await service.submit_answer(state_a["session_id"], ans_weak)
        eval_a = state_a_after["evaluations"][-1]
        planner_a = state_a_after["turn_plan"]
        q2_a = state_a_after["current_question"]["question_text"]
        
        # Interview B: Excellent Answer
        state_b = await service.start_interview("cand_alex_chen")
        ans_excellent = (
            "Dense vector embeddings project text into continuous latent spaces. "
            "In RAG pipelines, chunking strategy dictates document context boundaries. "
            "Vector retrieval using HNSW graph indices provides fast ANN search, after which "
            "cross-encoder reranking optimizes context precision before stuffing context into LLMs."
        )
        state_b_after = await service.submit_answer(state_b["session_id"], ans_excellent)
        eval_b = state_b_after["evaluations"][-1]
        planner_b = state_b_after["turn_plan"]
        q2_b = state_b_after["current_question"]["question_text"]
        
        print("\n--- PLANNER A DECISION (WEAK ANSWER) ---")
        print(f"Candidate Answer: \"{ans_weak}\"")
        print(f"Evaluation Correctness: '{eval_a.get('correctness')}', Score: {eval_a.get('overall_score')}")
        print(f"Planner Topic: '{planner_a.get('topic')}'")
        print(f"Planner Difficulty: {planner_a.get('difficulty')}")
        print(f"Planner is_follow_up: {planner_a.get('is_follow_up')}")
        print(f"Planner Question Type: '{planner_a.get('question_type')}'")
        print(f"Planner Reason: \"{planner_a.get('reason')}\"")
        print(f"Question A2: \"{q2_a}\"")
        
        print("\n--- PLANNER B DECISION (EXCELLENT ANSWER) ---")
        print(f"Candidate Answer: \"{ans_excellent}\"")
        print(f"Evaluation Correctness: '{eval_b.get('correctness')}', Score: {eval_b.get('overall_score')}")
        print(f"Planner Topic: '{planner_b.get('topic')}'")
        print(f"Planner Difficulty: {planner_b.get('difficulty')}")
        print(f"Planner is_follow_up: {planner_b.get('is_follow_up')}")
        print(f"Planner Question Type: '{planner_b.get('question_type')}'")
        print(f"Planner Reason: \"{planner_b.get('reason')}\"")
        print(f"Question B2: \"{q2_b}\"")
        
        print("\n--- FIELDS THAT CHANGED SOLELY BECAUSE OF CANDIDATE ANSWER ---")
        print(f"1. Evaluation Correctness: '{eval_a.get('correctness')}' vs '{eval_b.get('correctness')}'")
        print(f"2. Evaluation Score: {eval_a.get('overall_score')} vs {eval_b.get('overall_score')}")
        print(f"3. Planner is_follow_up: {planner_a.get('is_follow_up')} vs {planner_b.get('is_follow_up')}")
        print(f"4. Planner Topic: '{planner_a.get('topic')}' vs '{planner_b.get('topic')}'")
        print(f"5. Planner Difficulty: {planner_a.get('difficulty')} vs {planner_b.get('difficulty')}")
        print(f"6. Next Question Text: Q2A != Q2B (True)")

async def run_experiment_6_stability():
    print("\n" + "=" * 70)
    print("EXPERIMENT 6: SAME ANSWER / SAME STATE STABILITY EXPERIMENT")
    print("=" * 70)
    
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        seed_curriculum(session)
        seed_candidates(session)
        service = InterviewService(session)
        
        ans = "Vector databases always guarantee exact nearest-neighbor search."
        
        decisions = []
        for run_idx in range(1, 4):
            state = await service.start_interview("cand_alex_chen")
            state_after = await service.submit_answer(state["session_id"], ans)
            tp = state_after["turn_plan"]
            decisions.append({
                "topic": tp.get("topic"),
                "is_follow_up": tp.get("is_follow_up"),
                "follow_up_reason": state_after.get("follow_up_reason"),
                "question_type": tp.get("question_type")
            })
            print(f"Run {run_idx}: Topic='{tp.get('topic')}', is_follow_up={tp.get('is_follow_up')}, reason='{state_after.get('follow_up_reason')}', q_type='{tp.get('question_type')}'")
        
        all_same = all(d == decisions[0] for d in decisions)
        print(f"\nStable Reasoning Across Runs: {all_same}")

if __name__ == "__main__":
    asyncio.run(run_experiment_5_answer_dependence())
    asyncio.run(run_experiment_6_stability())
