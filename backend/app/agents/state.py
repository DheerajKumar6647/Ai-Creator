from typing import TypedDict, List, Dict, Any, Optional

class InterviewState(TypedDict, total=False):
    session_id: str
    interview_id: str
    candidate_id: str
    candidate_profile: Dict[str, Any]
    curriculum: Dict[str, Any]
    curriculum_graph: List[Dict[str, Any]]
    interview_plan: Dict[str, Any]
    turn_plan: Optional[Dict[str, Any]]
    candidate_model: Dict[str, Any]
    conversation_summary: str
    questions: List[Dict[str, Any]]
    answers: List[Dict[str, Any]]
    evaluations: List[Dict[str, Any]]
    covered_topics: List[str]
    covered_days: List[int]
    remaining_topics: List[str]
    misconceptions: List[Dict[str, Any]]
    current_question: Optional[Dict[str, Any]]
    current_question_index: int
    question_number: int
    questions_asked: List[Dict[str, Any]]
    topics_covered: List[str]
    questions_by_topic: Dict[str, int]
    candidate_answers: List[Dict[str, Any]]
    answer_evaluations: List[Dict[str, Any]]
    strengths: List[str]
    weaknesses: List[str]
    detected_gaps: List[str]
    current_topic: str
    current_difficulty: int
    question_types_used: List[str]
    follow_up_count: int
    skipped_curriculum_topics: List[str]
    completed_curriculum_topics: List[str]
    coverage_requirements: Dict[str, Any]
    recent_question_texts: List[str]
    recent_answer_summaries: List[str]
    confidence_score: float
    technical_score: float
    communication_score: float
    knowledge_depth: float
    interview_status: str
    last_decision: str
    relevance: Optional[str]
    topic_alignment: Optional[str]
    off_topic_action: Optional[str]
    follow_up_reason: Optional[str]
    target_concept: Optional[str]
    evidence_from_answer: Optional[str]
    learning_objective: Optional[str]
    assessment_objective: Optional[str]
    topic_selection_reason: Optional[str]
    topic_selection_basis: Optional[List[str]]
    question_type_reason: Optional[str]
    final_feedback: Optional[Dict[str, Any]]



    hiring_recommendation: Optional[Dict[str, Any]]
    error_state: Optional[str]
    termination_requested: bool
    termination_reason: Optional[str]

