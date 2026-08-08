from sqlmodel import Session, select
from typing import Optional
from app.models.feedback import FeedbackReport

class FeedbackRepository:
    def __init__(self, session: Session):
        self.session = session

    def save_report(self, report: FeedbackReport) -> FeedbackReport:
        self.session.add(report)
        self.session.commit()
        self.session.refresh(report)
        return report

    def get_by_session_id(self, session_id: str) -> Optional[FeedbackReport]:
        statement = select(FeedbackReport).where(FeedbackReport.session_id == session_id)
        return self.session.exec(statement).first()
