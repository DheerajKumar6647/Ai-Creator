from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime

class CreateCandidateRequest(BaseModel):
    name: str = Field(..., min_length=2)
    email: Optional[str] = None
    target_role: Optional[str] = "AI Engineer"
    experience_level: Optional[str] = "Mid-Senior"
    years_of_experience: Optional[float] = 3.0
    primary_skills: List[str] = []
    resume_summary: Optional[str] = None

class CandidateResponse(BaseModel):
    id: str
    name: str
    email: Optional[str] = None
    target_role: Optional[str] = "AI Engineer"
    experience_level: Optional[str] = "Mid-Senior"
    years_of_experience: Optional[float] = 3.0
    primary_skills: List[str] = Field(default_factory=list)
    resume_summary: Optional[str] = None
    completed_days: List[int] = Field(default_factory=list)
    skipped_days: List[int] = Field(default_factory=list)
    attempts: int = 0
    completion_percentage: float = 0.0
    learning_signals: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("primary_skills", "completed_days", "skipped_days", mode="before")
    @classmethod
    def default_list_if_none(cls, v):
        return v if v is not None else []

    @field_validator("learning_signals", mode="before")
    @classmethod
    def default_dict_if_none(cls, v):
        return v if v is not None else {}


# Curriculum Schemas
class CurriculumTopicResponse(BaseModel):
    topic_id: str
    day_number: int
    name: str
    description: str
    learning_objectives: List[str]
    prerequisites: List[str]
    tools_used: List[str]
    difficulty: int

class CurriculumDayResponse(BaseModel):
    day_number: int
    title: str
    description: str
    tools: List[str]
    difficulty: int
    prerequisites: List[Any] = []
    topics: List[CurriculumTopicResponse] = []

# Interview Session Schemas
class CreateInterviewRequest(BaseModel):
    candidate_id: str

class QuestionResponse(BaseModel):
    question_id: str
    session_id: str
    curriculum_day: int
    topic: str
    difficulty: int
    question_text: str
    question_type: str
    intent: str
    expected_concepts: List[str]
    is_follow_up: bool = False

class AnswerSubmitRequest(BaseModel):
    answer_text: str = Field(..., min_length=2)

class EvaluationResponse(BaseModel):
    evaluation_id: str
    question_id: str
    technical_accuracy: float
    conceptual_understanding: float
    knowledge_depth: float
    reasoning_quality: float
    engineering_thinking: float
    communication: float
    confidence: float
    overall_score: float
    strengths: List[str]
    weaknesses: List[str]
    evidence: str
    recommended_follow_up: bool

class InterviewSessionResponse(BaseModel):
    session_id: str
    candidate_id: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    current_question_index: int
    questions_answered: int
    difficulty_level: int
    coverage_percentage: float
    overall_score: float
    current_question: Optional[QuestionResponse] = None
    termination_requested: bool = False
    termination_reason: Optional[str] = None

# Feedback Schemas
class FeedbackResponse(BaseModel):
    feedback_id: str
    session_id: str
    overall_rating: float
    technical_summary: str
    communication_summary: str
    engineering_thinking_summary: str
    overall_readiness: str
    hiring_recommendation: str
    recommendation_confidence: float
    recommendation_reasoning: str
    scores: Dict[str, float]
    strengths: List[str]
    weaknesses: List[str]
    misconception_report: List[Dict[str, Any]]
    topic_breakdown: List[Dict[str, Any]]
    learning_roadmap: List[Dict[str, Any]]

class HealthResponse(BaseModel):
    status: str
    environment: str
    version: str = "1.0.0"
