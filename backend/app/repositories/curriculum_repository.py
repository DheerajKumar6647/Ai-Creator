from sqlmodel import Session, select
from typing import Optional, List
from app.models.curriculum import CurriculumDayModel, CurriculumTopicModel

class CurriculumRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_all_days(self) -> List[CurriculumDayModel]:
        statement = select(CurriculumDayModel).order_by(CurriculumDayModel.day_number)
        return list(self.session.exec(statement).all())

    def get_day(self, day_number: int) -> Optional[CurriculumDayModel]:
        return self.session.get(CurriculumDayModel, day_number)

    def get_all_topics(self) -> List[CurriculumTopicModel]:
        statement = select(CurriculumTopicModel)
        return list(self.session.exec(statement).all())

    def get_topic(self, topic_id: str) -> Optional[CurriculumTopicModel]:
        return self.session.get(CurriculumTopicModel, topic_id)

    def get_topics_for_day(self, day_number: int) -> List[CurriculumTopicModel]:
        statement = select(CurriculumTopicModel).where(CurriculumTopicModel.day_number == day_number)
        return list(self.session.exec(statement).all())
