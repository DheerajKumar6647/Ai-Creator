from sqlmodel import SQLModel, Field, JSON
from typing import Optional, List, Any, Union
from datetime import datetime, timezone

def utc_now():
    return datetime.now(timezone.utc)

class CurriculumDayModel(SQLModel, table=True):
    __tablename__ = "curriculum_day"
    day_number: int = Field(primary_key=True)
    title: str
    description: str
    tools: List[str] = Field(default_factory=list, sa_type=JSON)
    difficulty: int = 1
    prerequisites: List[Union[int, str]] = Field(default_factory=list, sa_type=JSON)
    created_at: datetime = Field(default_factory=utc_now)

class CurriculumTopicModel(SQLModel, table=True):
    __tablename__ = "curriculum_topic"
    topic_id: str = Field(primary_key=True)
    day_number: int = Field(index=True)
    name: str
    description: str
    learning_objectives: List[str] = Field(default_factory=list, sa_type=JSON)
    prerequisites: List[str] = Field(default_factory=list, sa_type=JSON)
    tools_used: List[str] = Field(default_factory=list, sa_type=JSON)
    difficulty: int = 1
    related_topics: List[str] = Field(default_factory=list, sa_type=JSON)
    created_at: datetime = Field(default_factory=utc_now)

