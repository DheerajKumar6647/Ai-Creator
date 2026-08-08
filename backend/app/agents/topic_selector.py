from app.agents.state import InterviewState
from app.utils.logger import logger

async def topic_selector_node(state: InterviewState) -> InterviewState:
    logger.info(f"Running Topic Selector Node for session: {state.get('session_id')}")
    covered = state.get("covered_topics", [])
    remaining = [t for t in state.get("remaining_topics", []) if t not in covered]
    candidate_profile = state.get("candidate_profile", {})
    learning_signals = candidate_profile.get("learning_signals", {})
    weak_topics = learning_signals.get("weak_topics", [])
    
    # Priority:
    # 1. Weak topics in remaining
    # 2. First topic in remaining
    # 3. Fallback topic from default list
    selected_topic = None
    for t in weak_topics:
        if t in remaining:
            selected_topic = t
            break
            
    if not selected_topic and remaining:
        selected_topic = remaining[0]
        
    if not selected_topic:
        all_options = ["day1_tokenization", "day2_structured_outputs", "day6_vector_embeddings", "day7_chunking", "day8_vector_databases", "day9_rag_pipelines", "day13_agent_basics", "day21_rag_evaluation"]
        uncovered = [t for t in all_options if t not in covered]
        selected_topic = uncovered[0] if uncovered else "day9_rag_pipelines"

    state["current_topic"] = selected_topic
    state["last_decision"] = f"Selected topic: {selected_topic}"
    state["next_action"] = "GENERATE_QUESTION"
    return state
