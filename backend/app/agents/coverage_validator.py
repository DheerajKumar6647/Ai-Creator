from app.agents.state import InterviewState
from app.utils.logger import logger

async def coverage_validator_node(state: InterviewState) -> InterviewState:
    questions_count = len(state.get("questions", []))
    covered_days_count = len(state.get("covered_days", []))
    follow_ups_count = state.get("follow_up_count", 0)
    
    logger.info(f"Coverage check: Qs={questions_count}, Days={covered_days_count} ({state.get('covered_days')}), Follow-ups={follow_ups_count}")

    # Calculate coverage percentage based on 8 target questions
    target_questions = 8
    coverage_percentage = min(100.0, round((questions_count / target_questions) * 100.0, 1))
    state["interview_plan"] = state.get("interview_plan", {})
    state["interview_plan"]["coverage_percentage"] = coverage_percentage

    # Minimum completion criteria check
    is_complete = (
        (questions_count >= 8 and covered_days_count >= 4) or
        questions_count >= 10
    )


    if is_complete or state.get("interview_status") == "completing":
        state["next_action"] = "GENERATE_FEEDBACK"
        state["last_decision"] = f"Coverage criteria met ({questions_count} Qs, {covered_days_count} Days, {follow_ups_count} Follow-ups). Moving to feedback."
    else:
        state["next_action"] = "SELECT_TOPIC"
        state["last_decision"] = f"Coverage in progress ({questions_count}/8 Qs, {covered_days_count}/4 Days, {follow_ups_count}/2 Follow-ups). Continuing interview."
        
    return state
