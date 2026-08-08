import json
from app.agents.state import InterviewState
from app.prompts.planner_prompt import get_planner_prompt, get_turn_planner_prompt
from app.services.llm_provider import LLMProvider
from app.utils.logger import logger

async def planner_node(state: InterviewState) -> InterviewState:
    logger.info(f"Running Planner Node for session: {state.get('session_id')}")
    llm = LLMProvider()
    
    curriculum_json = json.dumps(state.get("curriculum_graph", []), indent=2)
    candidate_profile_json = json.dumps(state.get("candidate_profile", {}), indent=2)
    evaluations = state.get("evaluations", [])
    
    # If starting interview, generate initial overall plan first
    if not state.get("interview_plan"):
        prompt = get_planner_prompt(curriculum_json, candidate_profile_json)
        plan_data = await llm.generate_json(prompt, temperature=0.2)
        state["interview_plan"] = plan_data
        if "difficulty_curve" in plan_data and isinstance(plan_data["difficulty_curve"], list):
            state["current_difficulty"] = plan_data["difficulty_curve"][0]

    # Generate turn plan
    questions_asked = state.get("questions", [])
    topics_covered = state.get("covered_topics", [])
    detected_gaps = state.get("detected_gaps", [])
    current_topic = state.get("current_topic", "day1_tokenization")
    current_difficulty = state.get("current_difficulty", 2)
    question_types_used = state.get("question_types_used", [])
    questions_remaining = max(0, 8 - len(questions_asked))

    turn_prompt = get_turn_planner_prompt(
        curriculum_json=curriculum_json,
        candidate_profile_json=candidate_profile_json,
        topics_covered_json=json.dumps(topics_covered),
        questions_asked_json=json.dumps([q.get("question_text", "") for q in questions_asked]),
        recent_evaluations_json=json.dumps(evaluations[-1:] if evaluations else []),
        detected_gaps_json=json.dumps(detected_gaps),
        current_topic=current_topic,
        current_difficulty=current_difficulty,
        question_types_used_json=json.dumps(question_types_used),
        questions_remaining=questions_remaining
    )


    turn_plan = await llm.generate_json(turn_prompt, temperature=0.3)
    logger.info(f"Turn plan generated: {turn_plan}")

    
    # Validate and fallback turn_plan structure
    if not isinstance(turn_plan, dict):
        turn_plan = {}
    
    topic = turn_plan.get("topic") or current_topic
    difficulty = turn_plan.get("difficulty")
    if isinstance(difficulty, str):
        diff_map = {"easy": 1, "medium": 3, "hard": 5}
        difficulty = diff_map.get(difficulty.lower(), current_difficulty)
    elif not isinstance(difficulty, int) or not (1 <= difficulty <= 5):
        difficulty = current_difficulty

    question_type = turn_plan.get("question_type") or "conceptual"

    topic_sel_reason = turn_plan.get("topic_selection_reason", f"Selected {topic} based on candidate performance and curriculum assessment requirements.")
    topic_sel_basis = turn_plan.get("topic_selection_basis", ["performance_assessment", "curriculum_coverage"])
    q_type_reason = turn_plan.get("question_type_reason", f"Selected {question_type} to evaluate candidate's technical depth.")

    state["turn_plan"] = {
        "topic": topic,
        "topic_selection_reason": topic_sel_reason,
        "topic_selection_basis": topic_sel_basis,
        "objective": turn_plan.get("objective", f"Assess understanding of {topic}"),
        "difficulty": difficulty,
        "question_type": question_type,
        "question_type_reason": q_type_reason,
        "reason": turn_plan.get("reason", "Follow turn strategy"),
        "is_follow_up": bool(turn_plan.get("is_follow_up", False)),
        "follow_up_reason": turn_plan.get("follow_up_reason", "none"),
        "target_concept": turn_plan.get("target_concept", ""),
        "evidence_from_answer": turn_plan.get("evidence_from_answer", ""),
        "off_topic_action": turn_plan.get("off_topic_action", "none")
    }

    state["topic_selection_reason"] = topic_sel_reason
    state["topic_selection_basis"] = topic_sel_basis
    state["question_type_reason"] = q_type_reason
    state["off_topic_action"] = turn_plan.get("off_topic_action", "none")
    state["follow_up_reason"] = turn_plan.get("follow_up_reason", "none")
    state["target_concept"] = turn_plan.get("target_concept", "")
    state["evidence_from_answer"] = turn_plan.get("evidence_from_answer", "")

    state["current_topic"] = topic
    state["current_difficulty"] = difficulty


    
    # Update question types used list
    types_used = list(state.get("question_types_used", []))
    if question_type not in types_used:
        types_used.append(question_type)
        state["question_types_used"] = types_used

    state["last_decision"] = f"Planner node created turn plan for topic '{topic}' at difficulty {difficulty} ({question_type})"
    state["next_action"] = "GENERATE_QUESTION"
    
    return state

