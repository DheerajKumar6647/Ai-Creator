import pytest
import asyncio
from sqlmodel import Session, SQLModel, create_engine
from app.database.seed import seed_curriculum, seed_candidates
from app.services.interview_service import InterviewService
from app.agents.termination_detector import detect_termination_intent, detect_termination_intent_heuristic

# ==============================================================================
# UNIT TESTS FOR TERMINATION DETECTOR (CATEGORIES A - F)
# ==============================================================================

@pytest.mark.asyncio
async def test_category_a_explicit_english_withdrawal():
    texts = [
        "I don't want to give this test.",
        "I don't want to continue.",
        "Please stop the interview.",
        "Stop this test.",
        "I want to quit.",
        "I want to leave.",
        "Can we end this interview?",
        "I don't want to answer any more questions.",
        "I have changed my mind.",
        "I would like to withdraw.",
        "Please cancel my interview.",
        "I am done with this interview.",
        "Let's stop here.",
        "I don't want to take the interview anymore.",
        "I don't wish to continue with the assessment.",
        "End the test.",
        "Terminate the interview.",
        "I want to exit the interview.",
        "No more questions please.",
        "I refuse to continue.",
        "I am not interested in taking this test.",
        "I don't want to participate.",
        "I want to discontinue the interview."
    ]
    for text in texts:
        res = await detect_termination_intent(text)
        assert res["termination_requested"] is True, f"Failed to detect withdrawal for: '{text}'"
        assert res["termination_reason"] == "candidate_withdrawal"


@pytest.mark.asyncio
async def test_category_b_hinglish_and_hindi_withdrawal():
    texts = [
        "Mujhe ye test nahi dena hai.",
        "Mujhe interview nahi dena.",
        "mujhe nahi dena",
        "nhi dena hai",
        "mujhe nahi karna",
        "main nahi dunga",
        "mana kar raha hu",
        "Mujhe test continue nahi karna.",
        "Is test ko band kar do.",
        "Interview rok do.",
        "Mujhe ye interview nahi dena hai.",
        "Main test chhodna chahta hu.",
        "Mujhe aur questions nahi chahiye.",
        "Bas karo, mujhe test nahi dena.",
        "Main continue nahi karna chahta.",
        "Mera interview yahin stop kar do.",
        "Mujhe interview se exit karna hai.",
        "Maine decide kiya hai ki mujhe test nahi dena.",
        "Mujhe assessment continue nahi karna.",
        "Main ye test nahi dena chahta.",
        "Mujhe ab aur answer nahi karne.",
        "Interview cancel kar do.",
        "मुझे यह टेस्ट नहीं देना है।",
        "मुझे इंटरव्यू नहीं देना।",
        "मैं आगे जारी नहीं रखना चाहता।",
        "इंटरव्यू बंद कर दीजिए।",
        "टेस्ट रोक दीजिए।",
        "मैं यह टेस्ट छोड़ना चाहता हूँ।",
        "मुझे और सवालों का जवाब नहीं देना।",
        "मेरा इंटरव्यू यहीं खत्म कर दीजिए।"
    ]
    for text in texts:
        res = await detect_termination_intent(text)
        assert res["termination_requested"] is True, f"Failed to detect Hinglish/Hindi withdrawal for: '{text}'"
        assert res["termination_reason"] == "candidate_withdrawal"


@pytest.mark.asyncio
async def test_category_c_indirect_polite_withdrawal():
    texts = [
        "I think I would rather not continue.",
        "I don't think I want to do this anymore.",
        "Maybe we should stop the interview here.",
        "I'd prefer to end the assessment.",
        "I would like to stop now.",
        "I think I'm done.",
        "Can we call it a day?",
        "I don't feel like continuing.",
        "I'd rather not answer any more questions."
    ]
    for text in texts:
        res = await detect_termination_intent(text)
        assert res["termination_requested"] is True, f"Failed to detect indirect withdrawal for: '{text}'"
        assert res["termination_reason"] == "candidate_withdrawal"


@pytest.mark.asyncio
async def test_category_d_technical_struggle_must_not_terminate():
    texts = [
        "I don't know.",
        "I don't know this.",
        "I'm not sure.",
        "I can't answer this.",
        "This is difficult.",
        "This question is hard.",
        "I forgot.",
        "Can you repeat the question?",
        "I need some time.",
        "I am confused.",
        "I don't understand.",
        "I don't know how this works.",
        "I don't know how HNSW works."
    ]
    for text in texts:
        res = await detect_termination_intent(text)
        assert res["termination_requested"] is False, f"False positive termination detected for struggling text: '{text}'"


@pytest.mark.asyncio
async def test_category_e_technical_use_of_stop_quit_must_not_terminate():
    texts = [
        "Why does the system stop generating tokens?",
        "The server stopped responding.",
        "How do you stop a retry loop?",
        "How do we stop an infinite retry loop?",
        "How can we stop hallucinations?"
    ]
    for text in texts:
        res = await detect_termination_intent(text)
        assert res["termination_requested"] is False, f"False positive termination detected for technical stop text: '{text}'"


@pytest.mark.asyncio
async def test_category_f_normal_technical_answer():
    texts = [
        "Byte-Pair Encoding works by iteratively merging the most frequent pair of adjacent bytes or characters in a text corpus.",
        "HNSW builds a multi-layer graph index for fast approximate nearest neighbor vector search with low latency.",
        "Dense embeddings map semantic text into high-dimensional vector spaces where cosine distance measures conceptual similarity."
    ]
    for text in texts:
        res = await detect_termination_intent(text)
        assert res["termination_requested"] is False, f"False positive termination detected for normal technical answer: '{text}'"


@pytest.mark.asyncio
async def test_regression_tests_1_to_8():
    """
    Explicit regression tests specified in task requirements:
    TEST 1: "Conditional routing decides whether to stop (END)." -> NOT TERMINATED
    TEST 2: "The node terminates execution when END is reached." -> NOT TERMINATED
    TEST 3: "How do we stop an infinite loop?" -> NOT TERMINATED
    TEST 4: "How can we stop hallucinations?" -> NOT TERMINATED
    TEST 5: "I don't want to continue this interview." -> TERMINATED
    TEST 6: "Please stop the test." -> TERMINATED
    TEST 7: "Mujhe interview nahi dena." -> TERMINATED
    TEST 8: "Mujhe continue nahi karna." -> TERMINATED
    """
    false_positives = [
        ("Conditional routing decides whether to stop (END).", 1),
        ("The node terminates execution when END is reached.", 2),
        ("How do we stop an infinite loop?", 3),
        ("How can we stop hallucinations?", 4)
    ]
    for text, test_num in false_positives:
        res = await detect_termination_intent(text)
        assert res["termination_requested"] is False, f"TEST {test_num} FAILED: False positive termination for '{text}'"

    true_withdrawals = [
        ("I don't want to continue this interview.", 5),
        ("Please stop the test.", 6),
        ("Mujhe interview nahi dena.", 7),
        ("Mujhe continue nahi karna.", 8)
    ]
    for text, test_num in true_withdrawals:
        res = await detect_termination_intent(text)
        assert res["termination_requested"] is True, f"TEST {test_num} FAILED: Failed to detect withdrawal for '{text}'"
        assert res["termination_reason"] == "candidate_withdrawal"


@pytest.mark.asyncio
async def test_critical_e2e_valid_technical_answer_flow():
    """
    CRITICAL END-TO-END TEST:
    Submit the exact technical answer from this bug report containing 'whether to stop (END)'.
    Verify flow:
    Candidate Answer -> Evaluator -> Normal evaluation -> Planner -> Next Question
    NOT:
    Candidate Answer -> Withdrawal Detector -> Terminate Interview
    """
    valid_technical_answer = (
        "1. What is Stateful Multi-step Architecture: Agent executes actions across multiple steps while "
        "keeping a persistent memory (state) of past inputs, outputs, and intermediate data.\n"
        "2. State Schema: Defines the shared data structure (e.g., messages, current step) passed between nodes and updated after each action.\n"
        "3. Node Functions: Python functions that process the current state, perform an action (e.g., call LLM, run tool), and return updated state values.\n"
        "4. Conditional Routing Edges: Logic functions that read the current state and dynamically decide which node to run next or whether to stop (END)."
    )

    # 1. Verify intent detector directly returns termination_requested = False
    res = await detect_termination_intent(valid_technical_answer)
    assert res["termination_requested"] is False, "Valid technical answer MUST NOT trigger termination!"

    # 2. Verify full InterviewService flow
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        seed_curriculum(session)
        seed_candidates(session)
        service = InterviewService(session)

        # Start interview -> Question 1
        state_q1 = await service.start_interview("cand_alex_chen")
        session_id = state_q1["session_id"]
        assert state_q1["interview_status"] == "in_progress"

        # Submit technical answer containing 'whether to stop (END)'
        next_state = await service.submit_answer(session_id, valid_technical_answer)

        # Assert session remains in progress and moves to evaluation and next question
        assert next_state["interview_status"] == "in_progress", "Interview status MUST remain in_progress!"
        assert next_state["termination_requested"] is False
        assert next_state["current_question"] is not None, "Next question MUST be generated!"
        assert len(next_state["answers"]) == 1
        assert len(next_state["evaluations"]) == 1, "Evaluation MUST be performed normally!"


# ==============================================================================
# END-TO-END REGRESSION TEST (CATEGORY G)
# ==============================================================================

@pytest.mark.asyncio
async def test_e2e_interview_termination_flow():
    """
    Full End-To-End test:
    1. Start interview -> Question 1 received.
    2. Submit normal technical answer -> Question 2 generated.
    3. Submit withdrawal statement: "I don't want to continue this interview, please stop it."
    4. Verify termination_requested == True, interview_status == "terminated_by_candidate", next_question == None.
    5. Verify question count did not increase with a new question.
    6. Start a brand new interview -> verify a new session_id is created and old session remains terminated.
    """
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        seed_curriculum(session)
        seed_candidates(session)
        service = InterviewService(session)

        # 1. Start Interview
        state_q1 = await service.start_interview("cand_alex_chen")
        session_id_1 = state_q1["session_id"]
        assert state_q1["interview_status"] == "in_progress"
        assert state_q1["current_question"] is not None
        assert state_q1["termination_requested"] is False

        # 2. Submit normal technical answer
        ans1 = "Tokenization breaks continuous text into subwords or tokens before vector encoding."
        state_q2 = await service.submit_answer(session_id_1, ans1)
        assert state_q2["interview_status"] == "in_progress"
        assert state_q2["current_question"] is not None
        assert state_q2["termination_requested"] is False
        q2_text = state_q2["current_question"]["question_text"]

        # 3. Submit withdrawal request
        ans_withdraw = "I don't want to continue this interview, please stop it."
        state_term = await service.submit_answer(session_id_1, ans_withdraw)

        # 4. Verify termination status and no next question
        assert state_term["interview_status"] == "terminated_by_candidate"
        assert state_term["termination_requested"] is True
        assert state_term["termination_reason"] == "candidate_withdrawal"
        assert state_term["current_question"] is None

        # Verify DB session record
        db_sess1 = service.interview_repo.get_session(session_id_1)
        assert db_sess1.status == "terminated_by_candidate"
        assert db_sess1.termination_requested is True
        assert db_sess1.termination_reason == "candidate_withdrawal"
        assert db_sess1.completed_at is not None

        # 5. Verify no extra question was generated for turn 3
        questions_sess1 = service.interview_repo.get_questions_for_session(session_id_1)
        assert len(questions_sess1) == 2, "No 3rd question should be stored after candidate withdrawal!"

        # 6. Start a new interview for the same candidate
        state_new = await service.start_interview("cand_alex_chen")
        session_id_2 = state_new["session_id"]

        assert session_id_2 != session_id_1, "New interview MUST generate a brand-new session_id!"
        assert state_new["interview_status"] == "in_progress"
        assert state_new["current_question"] is not None
        assert state_new["termination_requested"] is False

        # Verify old session remains persisted as terminated_by_candidate
        db_sess1_recheck = service.interview_repo.get_session(session_id_1)
        assert db_sess1_recheck.status == "terminated_by_candidate"

