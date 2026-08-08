from sqlmodel import SQLModel, Field, JSON
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

def utc_now():
    return datetime.now(timezone.utc)

class Candidate(SQLModel, table=True):
    id: str = Field(default=None, primary_key=True)
    name: str
    email: Optional[str] = None
    target_role: Optional[str] = "AI Engineer"
    experience_level: Optional[str] = "Mid-Senior"
    years_of_experience: Optional[float] = 3.0
    primary_skills: List[str] = Field(default_factory=list, sa_type=JSON)
    resume_summary: Optional[str] = None
    completed_days: List[int] = Field(default_factory=list, sa_type=JSON)
    skipped_days: List[int] = Field(default_factory=list, sa_type=JSON)
    attempts: int = Field(default=0)
    completion_percentage: float = Field(default=0.0)
    learning_signals: Dict[str, Any] = Field(default_factory=dict, sa_type=JSON)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


