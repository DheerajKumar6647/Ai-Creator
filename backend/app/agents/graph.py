from langgraph.graph import StateGraph, END
from app.agents.state import InterviewState
from app.agents.planner import planner_node
from app.agents.question_generator import question_generator_node
from app.agents.evaluator import evaluator_node
from app.agents.memory import memory_manager_node
from app.agents.difficulty_controller import difficulty_controller_node
from app.agents.topic_selector import topic_selector_node
from app.agents.coverage_validator import coverage_validator_node
from app.agents.feedback_generator import feedback_generator_node
from app.utils.logger import logger

def route_after_evaluator(state: InterviewState) -> str:
    next_act = state.get("next_action")
    if next_act == "FOLLOW_UP":
        return "question_generator"
    return "memory_manager"

def route_after_coverage(state: InterviewState) -> str:
    next_act = state.get("next_action")
    if next_act == "GENERATE_FEEDBACK":
        return "feedback_generator"
    return "topic_selector"

def build_interview_graph():
    logger.info("Building LangGraph StateGraph for InterviewAI...")
    builder = StateGraph(InterviewState)
    
    # Add Nodes
    builder.add_node("planner", planner_node)
    builder.add_node("question_generator", question_generator_node)
    builder.add_node("evaluator", evaluator_node)
    builder.add_node("memory_manager", memory_manager_node)
    builder.add_node("difficulty_controller", difficulty_controller_node)
    builder.add_node("topic_selector", topic_selector_node)
    builder.add_node("coverage_validator", coverage_validator_node)
    builder.add_node("feedback_generator", feedback_generator_node)
    
    # Set Entry Point
    builder.set_entry_point("planner")
    
    # Add Edges
    builder.add_edge("planner", "question_generator")
    
    builder.add_conditional_edges(
        "evaluator",
        route_after_evaluator,
        {
            "question_generator": "question_generator",
            "memory_manager": "memory_manager"
        }
    )
    
    builder.add_edge("memory_manager", "difficulty_controller")
    builder.add_edge("difficulty_controller", "coverage_validator")
    
    builder.add_conditional_edges(
        "coverage_validator",
        route_after_coverage,
        {
            "feedback_generator": "feedback_generator",
            "topic_selector": "topic_selector"
        }
    )
    
    builder.add_edge("topic_selector", "question_generator")
    builder.add_edge("feedback_generator", END)
    
    return builder.compile()

interview_graph = build_interview_graph()
