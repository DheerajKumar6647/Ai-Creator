from sqlmodel import SQLModel, Field, JSON
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

def utc_now():
    return datetime.now(timezone.utc)

class InterviewSession(SQLModel, table=True):
    __tablename__ = "interview_session"
    session_id: str = Field(primary_key=True)
    candidate_id: str = Field(index=True)
    status: str = Field(default="created")  # created, in_progress, completed, failed
    started_at: datetime = Field(default_factory=utc_now)
    completed_at: Optional[datetime] = None
    current_question_index: int = 0
    questions_answered: int = 0
    difficulty_level: int = 1
    coverage_percentage: float = 0.0
    overall_score: float = 0.0
    technical_score: float = 0.0
    communication_score: float = 0.0
    confidence_score: float = 0.0
    covered_days: List[int] = Field(default_factory=list, sa_type=JSON)
    covered_topics: List[str] = Field(default_factory=list, sa_type=JSON)
    follow_up_count: int = 0
    termination_requested: bool = Field(default=False)
    termination_reason: Optional[str] = Field(default=None)

class InterviewQuestion(SQLModel, table=True):
    __tablename__ = "interview_question"
    question_id: str = Field(primary_key=True)
    session_id: str = Field(index=True)
    curriculum_day: int
    topic: str
    difficulty: int
    question_text: str
    question_type: str  # Conceptual, Architecture, Trade-off, Debugging, Scenario, Reflection
    intent: str
    expected_concepts: List[str] = Field(default_factory=list, sa_type=JSON)
    is_follow_up: bool = False
    parent_question_id: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)

class CandidateAnswer(SQLModel, table=True):
    __tablename__ = "candidate_answer"
    answer_id: str = Field(primary_key=True)
    question_id: str = Field(index=True)
    session_id: str = Field(index=True)
    answer_text: str
    submitted_at: datetime = Field(default_factory=utc_now)
    answer_duration: float = 0.0
    word_count: int = 0
    character_count: int = 0

class Evaluation(SQLModel, table=True):
    __tablename__ = "evaluation"
    evaluation_id: str = Field(primary_key=True)
    question_id: str = Field(index=True)
    session_id: str = Field(index=True)
    correctness: str = Field(default="correct")
    technical_accuracy: float = 0.0  # 0 to 10

    conceptual_understanding: float = 0.0
    knowledge_depth: float = 0.0
    reasoning_quality: float = 0.0
    engineering_thinking: float = 0.0
    communication: float = 0.0
    confidence: float = 0.0
    overall_score: float = 0.0
    strengths: List[str] = Field(default_factory=list, sa_type=JSON)
    weaknesses: List[str] = Field(default_factory=list, sa_type=JSON)
    misconceptions: List[Dict[str, Any]] = Field(default_factory=list, sa_type=JSON)
    evidence: str = ""
    recommended_follow_up: bool = False
    follow_up_reason: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)

