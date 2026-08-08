from app.agents.state import InterviewState
from app.utils.logger import logger

async def memory_manager_node(state: InterviewState) -> InterviewState:
    logger.info(f"Running Memory Manager Node for session: {state.get('session_id')}")
    questions = state.get("questions", [])
    answers = state.get("answers", [])
    
    summary_parts = []
    for i, (q, a) in enumerate(zip(questions, answers), 1):
        q_txt = (q.get("question_text") or "")[:100]
        ans_txt = (a.get("answer_text") or "")[:150]
        topic = q.get("topic") or "General"
        diff = q.get("difficulty") or 1
        summary_parts.append(f"Q{i} [{topic}, Diff {diff}]: {q_txt}...\nAns: {ans_txt}...")
        
    state["conversation_summary"] = "\n\n".join(summary_parts[-4:])  # Rolling 4 turn summary
    state["last_decision"] = "Updated conversation memory summary."
    return state
