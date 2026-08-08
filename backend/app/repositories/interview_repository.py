from sqlmodel import Session, select
from typing import Optional, List
from app.models.interview import InterviewSession, InterviewQuestion, CandidateAnswer, Evaluation

class InterviewRepository:
    def __init__(self, session: Session):
        self.session = session

    def create_session(self, session_obj: InterviewSession) -> InterviewSession:
        self.session.add(session_obj)
        self.session.commit()
        self.session.refresh(session_obj)
        return session_obj

    def get_session(self, session_id: str) -> Optional[InterviewSession]:
        return self.session.get(InterviewSession, session_id)

    def update_session(self, session_obj: InterviewSession) -> InterviewSession:
        self.session.add(session_obj)
        self.session.commit()
        self.session.refresh(session_obj)
        return session_obj

    def get_sessions_for_candidate(self, candidate_id: str) -> List[InterviewSession]:
        statement = select(InterviewSession).where(InterviewSession.candidate_id == candidate_id).order_by(InterviewSession.started_at.desc())
        return list(self.session.exec(statement).all())

    def save_question(self, question: InterviewQuestion) -> InterviewQuestion:
        self.session.add(question)
        self.session.commit()
        self.session.refresh(question)
        return question

    def get_questions_for_session(self, session_id: str) -> List[InterviewQuestion]:
        statement = select(InterviewQuestion).where(InterviewQuestion.session_id == session_id).order_by(InterviewQuestion.created_at)
        return list(self.session.exec(statement).all())

    def save_answer(self, answer: CandidateAnswer) -> CandidateAnswer:
        self.session.add(answer)
        self.session.commit()
        self.session.refresh(answer)
        return answer

    def get_answers_for_session(self, session_id: str) -> List[CandidateAnswer]:
        statement = select(CandidateAnswer).where(CandidateAnswer.session_id == session_id).order_by(CandidateAnswer.submitted_at)
        return list(self.session.exec(statement).all())

    def save_evaluation(self, eval_obj: Evaluation) -> Evaluation:
        self.session.add(eval_obj)
        self.session.commit()
        self.session.refresh(eval_obj)
        return eval_obj

    def get_evaluations_for_session(self, session_id: str) -> List[Evaluation]:
        statement = select(Evaluation).where(Evaluation.session_id == session_id).order_by(Evaluation.created_at)
        return list(self.session.exec(statement).all())
