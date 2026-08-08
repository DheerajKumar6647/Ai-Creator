import json
import os
from sqlmodel import Session, select
from app.database.connection import engine, init_db
from app.models.candidate import Candidate
from app.models.curriculum import CurriculumDayModel, CurriculumTopicModel
from app.utils.logger import logger

def seed_curriculum(session: Session):
    file_path = os.path.join(os.path.dirname(__file__), "..", "curriculum", "curriculum_data.json")
    if not os.path.exists(file_path):
        logger.warning(f"Curriculum data file not found at {file_path}")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    curriculum_days = data.get("curriculum", [])
    for day_data in curriculum_days:
        existing_day = session.get(CurriculumDayModel, day_data["day_number"])
        if not existing_day:
            day_obj = CurriculumDayModel(
                day_number=day_data["day_number"],
                title=day_data["title"],
                description=day_data["description"],
                tools=day_data.get("tools", []),
                difficulty=day_data.get("difficulty", 1),
                prerequisites=day_data.get("prerequisites", [])
            )
            session.add(day_obj)

        for topic_data in day_data.get("topics", []):
            existing_topic = session.get(CurriculumTopicModel, topic_data["topic_id"])
            if not existing_topic:
                topic_obj = CurriculumTopicModel(
                    topic_id=topic_data["topic_id"],
                    day_number=day_data["day_number"],
                    name=topic_data["name"],
                    description=topic_data["description"],
                    learning_objectives=topic_data.get("learning_objectives", []),
                    prerequisites=topic_data.get("prerequisites", []),
                    tools_used=topic_data.get("tools_used", []),
                    difficulty=topic_data.get("difficulty", 1),
                    related_topics=topic_data.get("related_topics", [])
                )
                session.add(topic_obj)
    
    session.commit()
    logger.info("Curriculum data seeded successfully.")

def seed_candidates(session: Session):
    file_path = os.path.join(os.path.dirname(__file__), "..", "candidate", "candidate_data.json")
    if not os.path.exists(file_path):
        logger.warning(f"Candidate data file not found at {file_path}")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        candidates_list = json.load(f)

    for cand_data in candidates_list:
        existing = session.get(Candidate, cand_data["candidate_id"])
        if not existing:
            cand_obj = Candidate(
                id=cand_data["candidate_id"],
                name=cand_data["name"],
                email=cand_data.get("email"),
                target_role=cand_data.get("target_role", "AI Engineer"),
                experience_level=cand_data.get("experience_level", "Mid-Senior"),
                years_of_experience=cand_data.get("years_of_experience", 3.0),
                primary_skills=cand_data.get("primary_skills", []),
                resume_summary=cand_data.get("resume_summary", ""),
                completed_days=cand_data.get("completed_days", []),
                skipped_days=cand_data.get("skipped_days", []),
                attempts=cand_data.get("attempts", 0),
                completion_percentage=cand_data.get("completion_percentage", 0.0),
                learning_signals=cand_data.get("learning_signals", {})
            )
            session.add(cand_obj)
        else:
            existing.target_role = cand_data.get("target_role", existing.target_role)
            existing.experience_level = cand_data.get("experience_level", existing.experience_level)
            existing.years_of_experience = cand_data.get("years_of_experience", existing.years_of_experience)
            existing.primary_skills = cand_data.get("primary_skills", existing.primary_skills)
            existing.resume_summary = cand_data.get("resume_summary", existing.resume_summary)
            session.add(existing)

    session.commit()
    logger.info("Candidate profiles seeded successfully.")


def run_seed():
    init_db()
    with Session(engine) as session:
        seed_curriculum(session)
        seed_candidates(session)

if __name__ == "__main__":
    run_seed()
