from app.agents.state import InterviewState
from app.utils.logger import logger

async def difficulty_controller_node(state: InterviewState) -> InterviewState:
    logger.info(f"Running Difficulty Controller Node for session: {state.get('session_id')}")
    evaluations = state.get("evaluations", [])
    current_difficulty = state.get("current_difficulty", 2)
    
    if evaluations:
        latest_eval = evaluations[-1]
        overall_score = latest_eval.get("overall_score", 7.0)
        
        # Smooth difficulty adjustment rules
        if overall_score >= 8.5 and current_difficulty < 5:
            current_difficulty += 1
            logger.info(f"Increasing difficulty to Level {current_difficulty}")
        elif overall_score < 6.0 and current_difficulty > 1:
            current_difficulty -= 1
            logger.info(f"Decreasing difficulty to Level {current_difficulty}")

    state["current_difficulty"] = current_difficulty
    state["last_decision"] = f"Difficulty adjusted to Level {current_difficulty}"
    state["next_action"] = "CHECK_COVERAGE"
    return state
