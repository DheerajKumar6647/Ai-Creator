from sqlmodel import SQLModel, Field, JSON
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

def utc_now():
    return datetime.now(timezone.utc)

class FeedbackReport(SQLModel, table=True):
    __tablename__ = "feedback_report"
    feedback_id: str = Field(primary_key=True)
    session_id: str = Field(index=True, unique=True)
    overall_rating: float = 0.0
    technical_summary: str
    communication_summary: str
    engineering_thinking_summary: str
    overall_readiness: str
    hiring_recommendation: str  # STRONG_HIRE, HIRE, LEAN_HIRE, BORDERLINE, NEEDS_IMPROVEMENT, NOT_READY
    recommendation_confidence: float = 0.0
    recommendation_reasoning: str
    scores: Dict[str, float] = Field(default_factory=dict, sa_type=JSON)
    strengths: List[str] = Field(default_factory=list, sa_type=JSON)
    weaknesses: List[str] = Field(default_factory=list, sa_type=JSON)
    misconception_report: List[Dict[str, Any]] = Field(default_factory=list, sa_type=JSON)
    topic_breakdown: List[Dict[str, Any]] = Field(default_factory=list, sa_type=JSON)
    learning_roadmap: List[Dict[str, Any]] = Field(default_factory=list, sa_type=JSON)
    generated_at: datetime = Field(default_factory=utc_now)

