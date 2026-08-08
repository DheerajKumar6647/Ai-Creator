from sqlmodel import SQLModel, Field, JSON
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

def utc_now():
    return datetime.now(timezone.utc)

class InterviewMemoryModel(SQLModel, table=True):
    __tablename__ = "interview_memory"
    session_id: str = Field(primary_key=True)
    summary: str
    covered_topics: List[str] = Field(default_factory=list, sa_type=JSON)
    remaining_topics: List[str] = Field(default_factory=list, sa_type=JSON)
    misconceptions: List[Dict[str, Any]] = Field(default_factory=list, sa_type=JSON)
    confidence_trend: List[float] = Field(default_factory=list, sa_type=JSON)
    last_updated: datetime = Field(default_factory=utc_now)

