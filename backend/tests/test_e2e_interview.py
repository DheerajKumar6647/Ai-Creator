import pytest
import asyncio
from sqlmodel import Session, SQLModel, create_engine
from app.database.seed import seed_curriculum, seed_candidates
from app.services.interview_service import InterviewService

@pytest.mark.asyncio
async def test_full_e2e_interview_flow():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        seed_curriculum(session)
        seed_candidates(session)
        
        service = InterviewService(session)
        state = await service.start_interview("cand_alex_chen")
        session_id = state["session_id"]
        
        answers_pool = [
            # Shallow answer -> triggers follow-up
            "RAG retrieves relevant documents and gives them to the model.",
            "Increasing chunk overlap from 10% to 50% increases context duplication in vector databases, leading to higher storage costs and potential retrieval precision degradation.",
            "Dense vector embeddings project text into continuous latent spaces. Cosine similarity measures angle between vectors while Euclidean distance measures magnitude difference.",
            # Shallow answer -> triggers follow-up
            "Approximate nearest neighbor search speeds up query time.",
            "HNSW creates multi-layer navigable small world graphs for fast logarithmic vector similarity search, trading RAM usage for low query latency.",
            "Cross-encoder rerankers re-score candidate documents by jointly processing query and text, yielding superior precision compared to bi-encoder retrieval alone.",
            "LangGraph uses state machines where nodes are functions and edges are conditional state transitions, providing deterministic control over AI agent workflows.",
            "Prompt injection attacks can be mitigated by strict input delimitation, schema validation, and running input/output guardrail models like NeMo Guardrails."
        ]

        
        turn = 0
        while state.get("interview_status") != "completed" and turn < 12:
            turn += 1
            ans = answers_pool[(turn - 1) % len(answers_pool)]
            state = await service.submit_answer(session_id, ans)

        assert state["interview_status"] == "completed"
        assert len(state["questions"]) >= 8
        assert len(state["covered_days"]) >= 4
        assert state["follow_up_count"] >= 2
        assert state["final_feedback"] is not None
        assert "hiring_recommendation" in state["final_feedback"]
        print(f"E2E Test Passed successfully! {len(state['questions'])} Qs answered across {len(state['covered_days'])} days. Final Decision: {state['final_feedback']['hiring_recommendation']}")

if __name__ == "__main__":
    asyncio.run(test_full_e2e_interview_flow())
