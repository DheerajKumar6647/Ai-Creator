import json
from app.agents.state import InterviewState
from app.prompts.feedback_prompt import get_feedback_prompt
from app.services.llm_provider import LLMProvider
from app.utils.logger import logger

async def feedback_generator_node(state: InterviewState) -> InterviewState:
    logger.info(f"Running Feedback Generator Node for session: {state.get('session_id')}")
    llm = LLMProvider()
    
    questions = state.get("questions", [])
    answers = state.get("answers", [])
    evaluations = state.get("evaluations", [])
    
    history_items = []
    for q, a in zip(questions, answers):
        history_items.append({
            "question": q.get("question_text"),
            "topic": q.get("topic"),
            "difficulty": q.get("difficulty"),
            "answer": a.get("answer_text")
        })
        
    full_history_json = json.dumps(history_items, indent=2)
    evaluations_summary_json = json.dumps(evaluations, indent=2)
    candidate_model_json = json.dumps(state.get("candidate_model", {}), indent=2)
    
    prompt = get_feedback_prompt(full_history_json, evaluations_summary_json, candidate_model_json)
    feedback_data = await llm.generate_json(prompt, temperature=0.2)
    
    # Calculate reproducible final score strictly from stored evaluations
    scores = [float(e.get("overall_score", 0.0)) for e in evaluations]
    final_score = round(sum(scores) / len(scores), 2) if scores else 0.0
    
    total_questions = len(evaluations)
    questions_correct = sum(1 for e in evaluations if e.get("relevance") == "correct_and_relevant" or e.get("correctness") == "correct")
    questions_partially_correct = sum(1 for e in evaluations if e.get("relevance") == "partially_correct_and_relevant" or e.get("correctness") in ["partially_correct", "shallow"])
    questions_incorrect = sum(1 for e in evaluations if e.get("relevance") in ["incorrect_but_relevant", "refusal_no_answer"] or e.get("correctness") in ["incorrect", "misconception"])
    questions_off_topic = sum(1 for e in evaluations if e.get("relevance") == "incorrect_and_off_topic" or e.get("correctness") == "off_topic")

    feedback_data["overall_score"] = final_score
    feedback_data["overall_rating"] = final_score
    feedback_data["technical_score"] = final_score
    feedback_data["total_questions"] = total_questions
    feedback_data["questions_correct"] = questions_correct
    feedback_data["questions_partially_correct"] = questions_partially_correct
    feedback_data["questions_incorrect"] = questions_incorrect
    feedback_data["questions_off_topic"] = questions_off_topic
    feedback_data["average_score"] = final_score

    if "hiring_recommendation_reason" not in feedback_data:
        feedback_data["hiring_recommendation_reason"] = feedback_data.get("recommendation_reasoning", "Based on interview performance")
    if "question_level_progression" not in feedback_data:
        feedback_data["question_level_progression"] = [q.get("difficulty", 2) for q in questions]

    state["final_feedback"] = feedback_data
    state["technical_score"] = final_score
    state["overall_score"] = final_score
    
    rec_decision = feedback_data.get("hiring_recommendation", "HIRE")
    rec_reason = feedback_data.get("hiring_recommendation_reason") or feedback_data.get("recommendation_reasoning", "")
    
    state["hiring_recommendation"] = {
        "decision": rec_decision,
        "confidence": feedback_data.get("recommendation_confidence", 0.85),
        "reasoning": rec_reason
    }
    state["interview_status"] = "completed"
    state["last_decision"] = f"Generated final report. Final Score: {final_score}, Recommendation: {rec_decision}"
    state["next_action"] = "END"
    
    return state

