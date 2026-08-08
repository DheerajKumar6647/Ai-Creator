from sqlmodel import Session, select
from typing import Optional, List
from app.models.candidate import Candidate

class CandidateRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, candidate_id: str) -> Optional[Candidate]:
        return self.session.get(Candidate, candidate_id)

    def list_all(self) -> List[Candidate]:
        statement = select(Candidate)
        return list(self.session.exec(statement).all())

    def create(self, candidate: Candidate) -> Candidate:
        self.session.add(candidate)
        self.session.commit()
        self.session.refresh(candidate)
        return candidate

    def create_candidate(self, candidate: Candidate) -> Candidate:
        return self.create(candidate)


    def update(self, candidate: Candidate) -> Candidate:
        self.session.add(candidate)
        self.session.commit()
        self.session.refresh(candidate)
        return candidate

    def delete(self, candidate_id: str) -> bool:
        candidate = self.get_by_id(candidate_id)
        if candidate:
            self.session.delete(candidate)
            self.session.commit()
            return True
        return False
