import uuid
from typing import Optional, Dict, Any
from datetime import datetime, timezone

from sqlmodel import Session
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.curriculum_repository import CurriculumRepository
from app.repositories.interview_repository import InterviewRepository
from app.repositories.feedback_repository import FeedbackRepository
from app.models.interview import InterviewSession, InterviewQuestion, CandidateAnswer, Evaluation
from app.models.feedback import FeedbackReport
from app.agents.graph import interview_graph
from app.agents.state import InterviewState
from app.agents.termination_detector import detect_termination_intent
from app.utils.logger import logger

def _sqlmodel_to_dict(obj):
    if hasattr(obj, "__table__"):
        d = {c.name: getattr(obj, c.name) for c in obj.__table__.columns}
    elif hasattr(obj, "model_dump"):
        d = obj.model_dump(mode="json")
    else:
        d = dict(obj)

    for k, v in d.items():
        if isinstance(v, datetime):
            d[k] = v.isoformat()
    return d

class InterviewService:
    def __init__(self, session: Session):
        self.session = session
        self.candidate_repo = CandidateRepository(session)
        self.curriculum_repo = CurriculumRepository(session)
        self.interview_repo = InterviewRepository(session)
        self.feedback_repo = FeedbackRepository(session)

    async def start_interview(self, candidate_id: str) -> Dict[str, Any]:
        candidate = self.candidate_repo.get_by_id(candidate_id)
        if not candidate:
            # Auto-seed if database was unseeded in ephemeral serverless container
            from app.database.seed import run_seed
            run_seed()
            candidate = self.candidate_repo.get_by_id(candidate_id)

        if not candidate:
            # Fallback to first available candidate if specific ID not found
            all_cands = self.candidate_repo.list_all()
            if all_cands:
                candidate = all_cands[0]
                candidate_id = candidate.id
            else:
                raise ValueError(f"Candidate {candidate_id} not found.")

        session_id = f"session_{uuid.uuid4().hex[:10]}"
        
        # Load curriculum graph
        days = self.curriculum_repo.get_all_days()
        curriculum_graph = []
        all_topics = []
        for d in days:
            topics = self.curriculum_repo.get_topics_for_day(d.day_number)
            t_list = []
            for t in topics:
                all_topics.append(t.topic_id)
                t_list.append({
                    "topic_id": t.topic_id,
                    "name": t.name,
                    "description": t.description,
                    "difficulty": t.difficulty,
                    "learning_objectives": t.learning_objectives
                })
            curriculum_graph.append({
                "day_number": d.day_number,
                "title": d.title,
                "topics": t_list
            })

        # Initialize LangGraph State
        initial_state: InterviewState = {
            "session_id": session_id,
            "interview_id": session_id,
            "candidate_id": candidate_id,
            "candidate_profile": candidate.model_dump(mode="json"),
            "curriculum_graph": curriculum_graph,
            "interview_plan": {},
            "turn_plan": None,
            "candidate_model": candidate.learning_signals or {},
            "conversation_summary": "",
            "questions": [],
            "questions_asked": [],
            "answers": [],
            "candidate_answers": [],
            "evaluations": [],
            "answer_evaluations": [],
            "covered_topics": [],
            "topics_covered": [],
            "questions_by_topic": {},
            "strengths": [],
            "weaknesses": [],
            "detected_gaps": [],
            "question_types_used": [],
            "covered_days": [],
            "remaining_topics": all_topics,
            "misconceptions": [],
            "current_question": None,
            "current_question_index": 0,
            "question_number": 0,
            "current_topic": "day1_tokenization",
            "current_difficulty": 2,
            "follow_up_count": 0,
            "confidence_score": 7.0,
            "technical_score": 7.0,
            "communication_score": 7.0,
            "interview_status": "in_progress",
            "termination_requested": False,
            "termination_reason": None,
            "last_decision": "Initializing interview session",
            "next_action": "START"
        }

        # Run planner and first question node
        state = await interview_graph.ainvoke(initial_state)

        # Save session to DB
        db_session = InterviewSession(
            session_id=session_id,
            candidate_id=candidate_id,
            status="in_progress",
            started_at=datetime.now(timezone.utc),
            current_question_index=state.get("current_question_index", 0),
            questions_answered=0,
            difficulty_level=state.get("current_difficulty", 2),
            coverage_percentage=0.0,
            covered_days=state.get("covered_days", []),
            covered_topics=state.get("covered_topics", []),
            termination_requested=False,
            termination_reason=None
        )
        self.interview_repo.create_session(db_session)

        # Save current question to DB
        curr_q = state.get("current_question")
        if curr_q:
            q_db = InterviewQuestion(
                question_id=curr_q["question_id"],
                session_id=session_id,
                curriculum_day=curr_q.get("curriculum_day", 1),
                topic=curr_q.get("topic", "day1_tokenization"),
                difficulty=curr_q.get("difficulty", 2),
                question_text=curr_q.get("question_text", ""),
                question_type=curr_q.get("question_type", "Conceptual"),
                intent=curr_q.get("intent", ""),
                expected_concepts=curr_q.get("expected_concepts", []),
                is_follow_up=curr_q.get("is_follow_up", False)
            )
            self.interview_repo.save_question(q_db)

        state["termination_requested"] = False
        state["termination_reason"] = None
        return state

    async def submit_answer(self, session_id: str, answer_text: str) -> Dict[str, Any]:
        db_session = self.interview_repo.get_session(session_id)
        if not db_session:
            raise ValueError(f"Session {session_id} not found.")

        candidate = self.candidate_repo.get_by_id(db_session.candidate_id)
        questions = self.interview_repo.get_questions_for_session(session_id)
        answers = self.interview_repo.get_answers_for_session(session_id)
        evaluations = self.interview_repo.get_evaluations_for_session(session_id)

        # Save Answer to DB
        latest_q = questions[-1]
        ans_id = f"ans_{uuid.uuid4().hex[:8]}"
        ans_db = CandidateAnswer(
            answer_id=ans_id,
            question_id=latest_q.question_id,
            session_id=session_id,
            answer_text=answer_text,
            submitted_at=datetime.now(timezone.utc),
            word_count=len(answer_text.split()),
            character_count=len(answer_text)
        )
        self.interview_repo.save_answer(ans_db)

        # ----------------------------------------------------------------------
        # HIGHEST PRIORITY CHECK: Candidate Intent Termination Detection
        # Check BEFORE evaluator, planner, question generator, difficulty adapter
        # ----------------------------------------------------------------------
        term_res = await detect_termination_intent(answer_text, latest_q.question_text)
        if term_res["termination_requested"]:
            logger.info(f"Terminating session {session_id} immediately due to candidate withdrawal request: {answer_text}")
            
            db_session.status = "terminated_by_candidate"
            db_session.termination_requested = True
            db_session.termination_reason = "candidate_withdrawal"
            db_session.completed_at = datetime.now(timezone.utc)
            db_session.questions_answered = len(answers) + 1
            self.interview_repo.update_session(db_session)

            q_list = [_sqlmodel_to_dict(q) for q in questions]
            a_list = [_sqlmodel_to_dict(a) for a in answers] + [_sqlmodel_to_dict(ans_db)]
            e_list = [_sqlmodel_to_dict(e) for e in evaluations]

            term_state: InterviewState = {
                "session_id": session_id,
                "interview_id": session_id,
                "candidate_id": db_session.candidate_id,
                "candidate_profile": candidate.model_dump(mode="json") if candidate else {},
                "questions": q_list,
                "questions_asked": q_list,
                "answers": a_list,
                "candidate_answers": a_list,
                "evaluations": e_list,
                "answer_evaluations": e_list,
                "current_question": None,
                "current_question_index": len(q_list) - 1,
                "question_number": len(q_list),
                "current_topic": latest_q.topic,
                "current_difficulty": db_session.difficulty_level,
                "confidence_score": db_session.confidence_score,
                "technical_score": db_session.technical_score,
                "communication_score": db_session.communication_score,
                "interview_status": "terminated_by_candidate",
                "termination_requested": True,
                "termination_reason": "candidate_withdrawal",
                "last_decision": "Candidate requested interview termination. Session terminated immediately.",
                "next_action": "TERMINATE"
            }
            return term_state

        # Reconstruct LangGraph State
        q_list = [_sqlmodel_to_dict(q) for q in questions]
        a_list = [_sqlmodel_to_dict(a) for a in answers] + [_sqlmodel_to_dict(ans_db)]
        e_list = [_sqlmodel_to_dict(e) for e in evaluations]

        topic_day_map = {
            "day1_tokenization": 1,
            "day1_api_calling": 1,
            "day2_structured_outputs": 2,
            "day2_function_calling": 2,
            "day6_vector_embeddings": 6,
            "day7_chunking": 7,
            "day8_vector_databases": 8,
            "day9_rag_pipelines": 9,
            "day13_agent_basics": 13,
            "day14_agent_memory": 14,
            "day21_rag_evaluation": 21,
            "day26_production_guardrails": 26
        }

        all_topics = [t.topic_id for t in self.curriculum_repo.get_all_topics()]
        covered_topics_set = set(db_session.covered_topics or [])
        for q in questions:
            if q.topic:
                covered_topics_set.add(q.topic)
        covered_topics_list = list(covered_topics_set)

        covered_days_set = set(db_session.covered_days or [])
        for q in questions:
            if q.curriculum_day:
                covered_days_set.add(q.curriculum_day)
            elif q.topic and q.topic in topic_day_map:
                covered_days_set.add(topic_day_map[q.topic])
        covered_days_list = list(covered_days_set)

        remaining_topics_list = [t for t in all_topics if t not in covered_topics_list]


        # Extract stored strengths/weaknesses/gaps from prior evaluations
        strengths_list = []
        weaknesses_list = []
        detected_gaps_list = []
        misconceptions_list = []
        for ev in e_list:
            for s in ev.get("strengths", []):
                if s and s not in strengths_list:
                    strengths_list.append(s)
            for w in ev.get("weaknesses", []):
                if w and w not in weaknesses_list:
                    weaknesses_list.append(w)
            for m in ev.get("misconceptions", []):
                m_item = m if isinstance(m, dict) else {"misconception": str(m)}
                if m_item not in misconceptions_list:
                    misconceptions_list.append(m_item)

        follow_up_count_calc = sum(1 for q in questions if q.is_follow_up)

        current_state: InterviewState = {
            "session_id": session_id,
            "interview_id": session_id,
            "candidate_id": db_session.candidate_id,
            "candidate_profile": candidate.model_dump(mode="json") if candidate else {},
            "curriculum_graph": [],
            "interview_plan": {},
            "turn_plan": None,
            "candidate_model": candidate.learning_signals if candidate else {},
            "conversation_summary": "",
            "questions": q_list,
            "questions_asked": q_list,
            "answers": a_list,
            "candidate_answers": a_list,
            "evaluations": e_list,
            "answer_evaluations": e_list,
            "covered_topics": covered_topics_list,
            "topics_covered": covered_topics_list,
            "covered_days": covered_days_list,
            "remaining_topics": remaining_topics_list,
            "strengths": strengths_list,
            "weaknesses": weaknesses_list,
            "detected_gaps": detected_gaps_list,
            "misconceptions": misconceptions_list,
            "current_question": q_list[-1],
            "current_question_index": len(q_list) - 1,
            "question_number": len(q_list),
            "current_topic": latest_q.topic,
            "current_difficulty": db_session.difficulty_level,
            "follow_up_count": follow_up_count_calc,

            "learning_objective": f"Master core engineering concepts, operational mechanics, and trade-offs of {latest_q.topic}",
            "assessment_objective": f"Evaluate technical depth, candidate reasoning, and design maturity at difficulty level {db_session.difficulty_level}",
            "confidence_score": db_session.confidence_score,
            "technical_score": db_session.technical_score,
            "communication_score": db_session.communication_score,
            "interview_status": db_session.status,
            "last_decision": "Processing submitted answer",
            "next_action": "EVALUATE"
        }


        # Step 1: Evaluator Node
        from app.agents.evaluator import evaluator_node
        from app.agents.memory import memory_manager_node
        from app.agents.planner import planner_node
        from app.agents.coverage_validator import coverage_validator_node
        from app.agents.question_generator import question_generator_node
        from app.agents.feedback_generator import feedback_generator_node

        state = await evaluator_node(current_state)
        
        # Save evaluation to DB
        latest_eval = state["evaluations"][-1]
        tech_acc = latest_eval.get("technical_accuracy")
        if not isinstance(tech_acc, (int, float)):
            tech_acc = latest_eval.get("overall_score", 7.0)

        eval_db = Evaluation(
            evaluation_id=latest_eval["evaluation_id"],
            question_id=latest_q.question_id,
            session_id=session_id,
            correctness=str(latest_eval.get("correctness", "correct")),
            technical_accuracy=float(tech_acc),

            conceptual_understanding=7.0,
            knowledge_depth=7.0,
            reasoning_quality=7.0,
            engineering_thinking=7.0,
            communication=7.0,
            confidence=7.0,
            overall_score=float(latest_eval.get("overall_score", 7.0)),
            strengths=latest_eval.get("strengths", []),
            weaknesses=latest_eval.get("weaknesses", []),
            misconceptions=latest_eval.get("misconceptions", []),
            evidence=latest_eval.get("evidence", ""),
            recommended_follow_up=bool(latest_eval.get("recommended_follow_up", False)),
            follow_up_reason=str(latest_eval.get("recommended_follow_up") or "")
        )
        self.interview_repo.save_evaluation(eval_db)

        # Step 2: Memory Manager Node
        state = await memory_manager_node(state)

        # Step 3: Turn Planner Node
        state = await planner_node(state)

        # Step 4: Coverage Validator Node
        state = await coverage_validator_node(state)

        # Step 5: Feedback Generator Node or Question Generator Node
        if state.get("next_action") == "GENERATE_FEEDBACK":
            state = await feedback_generator_node(state)
            fb = state.get("final_feedback", {})
            fb_db = FeedbackReport(
                feedback_id=f"fb_{uuid.uuid4().hex[:8]}",
                session_id=session_id,
                overall_rating=fb.get("overall_rating", fb.get("overall_score", 8.0)),
                technical_summary=fb.get("technical_summary", ""),
                communication_summary=fb.get("communication_summary", ""),
                engineering_thinking_summary=fb.get("engineering_thinking_summary", ""),
                overall_readiness=fb.get("overall_readiness", "Ready"),
                hiring_recommendation=fb.get("hiring_recommendation", "HIRE"),
                recommendation_confidence=fb.get("recommendation_confidence", 0.85),
                recommendation_reasoning=fb.get("hiring_recommendation_reason") or fb.get("recommendation_reasoning", ""),
                scores=fb.get("scores", {}),
                strengths=fb.get("strengths", []),
                weaknesses=fb.get("weaknesses", []),
                misconception_report=fb.get("misconception_report", []),
                topic_breakdown=fb.get("topic_breakdown", []),
                learning_roadmap=fb.get("learning_roadmap", [])
            )
            self.feedback_repo.save_report(fb_db)
            db_session.status = "completed"
            db_session.completed_at = datetime.now(timezone.utc)
        else:
            state = await question_generator_node(state)

        # Save newly generated question to DB if available
        if state.get("current_question") and state["current_question"]["question_id"] != latest_q.question_id:
            new_q = state["current_question"]
            new_q_db = InterviewQuestion(
                question_id=new_q["question_id"],
                session_id=session_id,
                curriculum_day=new_q.get("curriculum_day", 1),
                topic=new_q.get("topic", "day1_tokenization"),
                difficulty=new_q.get("difficulty", 2),
                question_text=new_q.get("question_text", ""),
                question_type=new_q.get("question_type", "Conceptual"),
                intent=new_q.get("intent", ""),
                expected_concepts=new_q.get("expected_concepts", []),
                is_follow_up=new_q.get("is_follow_up", False)
            )
            self.interview_repo.save_question(new_q_db)

        # Update DB session stats
        db_session.questions_answered = len(state.get("answers", []))
        db_session.difficulty_level = state.get("current_difficulty", 2)
        db_session.follow_up_count = state.get("follow_up_count", 0)
        db_session.covered_days = list(state.get("covered_days", []))
        db_session.covered_topics = list(state.get("covered_topics", []))
        db_session.technical_score = state.get("technical_score", 7.0)
        db_session.communication_score = state.get("communication_score", 7.0)
        if state.get("interview_status") == "completed":
            db_session.status = "completed"
            db_session.completed_at = datetime.now(timezone.utc)
            fb = state.get("final_feedback", {})
            if fb:
                db_session.overall_score = float(fb.get("overall_rating", fb.get("overall_score", 8.0)))
            elif evaluations:
                avg = sum(e.overall_score for e in evaluations) / len(evaluations)
                db_session.overall_score = float(avg)

        self.interview_repo.update_session(db_session)

        state["termination_requested"] = False
        state["termination_reason"] = None
        return state

