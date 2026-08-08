import pytest
from app.agents.evaluator import compute_evaluation_metrics
from app.agents.feedback_generator import feedback_generator_node
from app.agents.termination_detector import detect_termination_intent_heuristic

def test_regression_off_topic_technically_correct_answer():
    """
    Question: "What is a state schema in a stateful multi-step AI architecture?"
    Candidate answer: "RAG retrieves relevant documents using vector similarity and passes them to an LLM."
    Expected: relevance = incorrect_and_off_topic, score <= 2.0
    """
    question = {
        "question_id": "q_agent_1",
        "question_text": "What is a state schema in a stateful multi-step AI architecture?",
        "topic": "day13_agent_basics",
        "expected_concepts": ["State schema definition", "Shared data structure", "State updates"],
        "intent": "Assess understanding of agent state schema"
    }
    answer = "RAG retrieves relevant documents using vector similarity and passes them to an LLM."
    
    result = compute_evaluation_metrics(question, answer, {})
    
    print("\n[TEST OUTPUT - Off-Topic Answer]")
    print(f"Relevance: {result['relevance']}")
    print(f"Correctness: {result['correctness']}")
    print(f"Overall Score: {result['overall_score']}")
    
    assert result["relevance"] == "incorrect_and_off_topic"
    assert result["correctness"] == "off_topic"
    assert result["overall_score"] <= 2.0, "Off-topic answer score MUST be <= 2.0"

def test_regression_correct_relevant_answer():
    """
    Question: "What are conditional routing edges?"
    Candidate answer: "Conditional routing edges inspect the current state and decide which node should execute next or whether the graph should terminate at END."
    Expected: relevance = correct_and_relevant, score >= 7.0
    """
    question = {
        "question_id": "q_agent_2",
        "question_text": "What are conditional routing edges?",
        "topic": "day13_agent_basics",
        "expected_concepts": ["Conditional routing edges", "Inspect state", "Next node selection", "END state"],
        "intent": "Assess conditional routing logic"
    }
    answer = "Conditional routing edges inspect the current state and decide which node should execute next or whether the graph should terminate at END."
    
    result = compute_evaluation_metrics(question, answer, {})
    
    print("\n[TEST OUTPUT - Correct Answer]")
    print(f"Relevance: {result['relevance']}")
    print(f"Correctness: {result['correctness']}")
    print(f"Overall Score: {result['overall_score']}")
    
    assert result["relevance"] == "correct_and_relevant"
    assert result["correctness"] == "correct"
    assert result["overall_score"] >= 7.0, "Correct relevant answer score MUST be >= 7.0"

def test_regression_partially_correct_answer():
    """
    Question: "What are conditional routing edges?"
    Candidate answer: "Nodes are Python functions that process the current state."
    Expected: relevance = partially_correct_and_relevant, score <= 6.0
    """
    question = {
        "question_id": "q_agent_3",
        "question_text": "What are conditional routing edges?",
        "topic": "day13_agent_basics",
        "expected_concepts": ["Conditional routing edges", "Inspect state", "Next node selection", "END state"],
        "intent": "Assess conditional routing logic"
    }
    answer = "Nodes are Python functions that process the current state."
    
    result = compute_evaluation_metrics(question, answer, {})
    
    print("\n[TEST OUTPUT - Partial Answer]")
    print(f"Relevance: {result['relevance']}")
    print(f"Correctness: {result['correctness']}")
    print(f"Overall Score: {result['overall_score']}")
    
    assert result["relevance"] == "partially_correct_and_relevant"
    assert result["overall_score"] <= 6.0, "Partial answer score MUST be <= 6.0"

def test_regression_misconception_answer():
    """
    Question: "Compare HNSW and IVF vector indices."
    Candidate answer: "Vector databases always guarantee exact nearest-neighbor search."
    Expected: correctness = misconception, score <= 4.0
    """
    question = {
        "question_id": "q_vec_1",
        "question_text": "Compare HNSW and IVF vector indices.",
        "topic": "day8_vector_databases",
        "expected_concepts": ["HNSW graph index", "IVF centroids", "ANN recall trade-offs"],
        "intent": "Evaluate index trade-offs"
    }
    answer = "Vector databases always guarantee exact nearest-neighbor search."
    
    result = compute_evaluation_metrics(question, answer, {})
    
    print("\n[TEST OUTPUT - Misconception Answer]")
    print(f"Relevance: {result['relevance']}")
    print(f"Correctness: {result['correctness']}")
    print(f"Overall Score: {result['overall_score']}")
    
    assert result["correctness"] == "misconception"
    assert result["overall_score"] <= 4.0, "Misconception answer score MUST be <= 4.0"

def test_regression_candidate_explicit_termination():
    """
    Candidate explicitly requests stopping interview.
    Expected: termination_requested = True
    """
    ans = "I don't want to give the test"
    res = detect_termination_intent_heuristic(ans, "What is tokenization?")
    assert res["termination_requested"] is True
    assert res["termination_reason"] == "candidate_withdrawal"

def test_regression_exact_user_multi_concept_answer():
    """
    Requirement 11 Answer Test:
    Question: "What is Stateful Multi-step Architecture?"
    Answer: Candidate provides comprehensive 4-part answer.
    Expected: relevance = correct_and_relevant, score >= 7.0
    """
    question = {
        "question_id": "q_agent_11",
        "question_text": "What is Stateful Multi-step Architecture?",
        "topic": "day13_agent_basics",
        "expected_concepts": ["Stateful multi-step architecture", "Persistent memory", "State Schema", "Node Functions", "Conditional Routing Edges"],
        "intent": "Assess stateful agent architecture concepts"
    }
    answer = (
        "1. What is Stateful Multi-step Architecture: Agent executes actions across multiple steps while keeping a persistent memory (state) of past inputs, outputs, and intermediate data.\n"
        "2. State Schema: Defines the shared data structure (e.g., messages, current step) passed between nodes and updated after each action.\n"
        "3. Node Functions: Python functions that process the current state, perform an action (e.g., call LLM, run tool), and return updated state values.\n"
        "4. Conditional Routing Edges: Logic functions that read the current state and dynamically decide which node to run next or whether to stop (END)."
    )
    
    result = compute_evaluation_metrics(question, answer, {})
    
    print("\n[TEST OUTPUT - Comprehensive Multi-Concept Answer]")
    print(f"Relevance: {result['relevance']}")
    print(f"Correctness: {result['correctness']}")
    print(f"Overall Score: {result['overall_score']}")
    
    assert result["relevance"] == "correct_and_relevant"
    assert result["correctness"] == "correct"
    assert result["overall_score"] >= 7.0

@pytest.mark.asyncio
async def test_regression_final_score_reproducibility():
    """
    Requirement 8 Test:
    Verify final_score calculation strictly equals sum(scores) / len(evaluations)
    """
    evaluations = [
        {"overall_score": 1.5, "relevance": "incorrect_and_off_topic", "correctness": "off_topic"},
        {"overall_score": 9.5, "relevance": "correct_and_relevant", "correctness": "correct"},
        {"overall_score": 5.5, "relevance": "partially_correct_and_relevant", "correctness": "partially_correct"},
        {"overall_score": 4.0, "relevance": "incorrect_but_relevant", "correctness": "misconception"}
    ]
    
    state = {
        "session_id": "test_sess_score",
        "questions": [{"question_text": "q1"}, {"question_text": "q2"}, {"question_text": "q3"}, {"question_text": "q4"}],
        "answers": [{"answer_text": "a1"}, {"answer_text": "a2"}, {"answer_text": "a3"}, {"answer_text": "a4"}],
        "evaluations": evaluations,
        "candidate_model": {}
    }
    
    res_state = await feedback_generator_node(state)
    fb = res_state["final_feedback"]
    
    expected_avg = round((1.5 + 9.5 + 5.5 + 4.0) / 4.0, 2)
    print("\n[TEST OUTPUT - Final Score Reproducibility]")
    print(f"Calculated Final Score: {fb['overall_score']}")
    print(f"Expected Average: {expected_avg}")
    print(f"Total Questions: {fb['total_questions']}")
    print(f"Correct: {fb['questions_correct']}")
    print(f"Partially Correct: {fb['questions_partially_correct']}")
    print(f"Incorrect: {fb['questions_incorrect']}")
    print(f"Off-Topic: {fb['questions_off_topic']}")
    
    assert fb["overall_score"] == expected_avg
    assert fb["total_questions"] == 4
    assert fb["questions_correct"] == 1
    assert fb["questions_partially_correct"] == 1
    assert fb["questions_incorrect"] == 1
    assert fb["questions_off_topic"] == 1
