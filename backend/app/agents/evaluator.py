import json
import uuid
from app.agents.state import InterviewState
from app.prompts.evaluator_prompt import get_evaluator_prompt
from app.services.llm_provider import LLMProvider
from app.utils.logger import logger

def compute_evaluation_metrics(
    latest_question: dict,
    candidate_answer_text: str,
    raw_eval_data: dict
) -> dict:
    q_text = (latest_question.get("question_text") or "").strip().lower()
    topic = (latest_question.get("topic") or "").strip().lower()
    expected_concepts = latest_question.get("expected_concepts") or []
    intent = (latest_question.get("intent") or "").strip().lower()
    
    ans_text = (candidate_answer_text or "").strip()
    ans_lower = ans_text.lower()
    
    refusal_phrases = ["i don't know", "idk", "no idea", "i do not know", "i'm not sure", "skip", "pass", "no answer", "refuse"]
    is_refusal = not ans_text or (len(ans_text.split()) <= 4 and any(p in ans_lower for p in refusal_phrases))

    domain_concept_map = {
        "day13_agent_basics": ["state schema", "stateful", "conditional routing", "routing edge", "node function", "node", "langgraph", "end state", "persistent memory", "multi-step", "workflow"],
        "day14_agent_memory": ["state", "memory", "checkpointer", "thread", "checkpoint", "conversation history"],
        "day8_vector_databases": ["vector database", "vector db", "hnsw", "ivf", "ann", "approximate nearest", "nearest-neighbor", "index", "pinecone", "faiss", "qps", "recall"],
        "day9_rag_pipelines": ["rag", "retrieval", "query rewriting", "hybrid search", "bm25", "reranking", "dense retrieval", "context window", "ragas"],
        "day7_chunking": ["chunk", "chunking", "chunk size", "chunk overlap", "semantic chunking", "fixed-size chunking"],
        "day6_vector_embeddings": ["embedding", "dense vector", "latent space", "cosine similarity", "euclidean distance", "matryoshka", "dimension"],
        "day1_tokenization": ["token", "tokenization", "bpe", "subword", "oov", "tiktoken", "byte pair"],
        "day2_structured_outputs": ["pydantic", "json mode", "structured output", "function calling", "schema", "validation", "tool call"]
    }

    question_concepts = set()
    for concept in expected_concepts:
        if isinstance(concept, str):
            question_concepts.add(concept.lower())

    if "state schema" in q_text or "state schema" in intent:
        question_concepts.update(["state schema", "state", "schema", "shared data structure", "messages"])
    if "routing edge" in q_text or "conditional routing" in q_text or "routing" in q_text:
        question_concepts.update(["conditional routing", "routing edge", "routing", "next node", "end"])
    if "stateful" in q_text or "multi-step" in q_text:
        question_concepts.update(["stateful", "multi-step", "persistent memory", "agent"])
    if "hnsw" in q_text or "ivf" in q_text or "vector database" in q_text:
        question_concepts.update(["hnsw", "ivf", "ann", "vector database", "recall", "qps"])
    if "chunk" in q_text or "chunking" in q_text:
        question_concepts.update(["chunk", "chunking", "chunk overlap", "chunk size"])

    topic_keywords = domain_concept_map.get(topic, [])
    for kw in topic_keywords:
        if kw in q_text:
            question_concepts.add(kw)

    matches = [c for c in question_concepts if c in ans_lower]

    is_other_domain = False
    if topic in ["day13_agent_basics", "day14_agent_memory"]:
        rag_terms = ["rag retrieves", "vector similarity and passes", "vector databases use hnsw", "bm25", "document retrieval"]
        if any(term in ans_lower for term in rag_terms) and not any(kw in ans_lower for kw in ["state schema", "conditional routing", "node function", "stateful multi-step", "langgraph", "end state"]):
            is_other_domain = True

    elif topic in ["day8_vector_databases", "day6_vector_embeddings"]:
        agent_terms = ["conditional routing edge", "state schema", "pydantic model", "bpe tokenizer"]
        if any(term in ans_lower for term in agent_terms) and not any(kw in ans_lower for kw in ["vector", "index", "hnsw", "ivf", "ann", "embedding", "distance"]):
            is_other_domain = True

    raw_rel = str(raw_eval_data.get("relevance", "")).lower()
    raw_corr = str(raw_eval_data.get("correctness", "")).lower()

    if is_refusal or raw_rel == "refusal_no_answer":
        relevance = "refusal_no_answer"
        correctness = "incorrect"
    elif is_other_domain or raw_rel == "incorrect_and_off_topic" or raw_corr == "off_topic":
        relevance = "incorrect_and_off_topic"
        correctness = "off_topic"
    elif "always guarantee exact" in ans_lower or raw_corr == "misconception":
        relevance = "incorrect_but_relevant"
        correctness = "misconception"
    elif len(matches) >= 2 or raw_rel == "correct_and_relevant" or (raw_corr == "correct" and len(ans_text.split()) >= 15):
        relevance = "correct_and_relevant"
        correctness = "correct"
    elif len(matches) == 1 or raw_rel == "partially_correct_and_relevant" or raw_corr in ["partially_correct", "shallow"]:
        relevance = "partially_correct_and_relevant"
        correctness = "partially_correct"
    elif "don't know" in ans_lower or raw_corr == "incorrect":
        relevance = "incorrect_but_relevant"
        correctness = "incorrect"
    else:
        relevance = raw_rel if raw_rel in [
            "correct_and_relevant", "partially_correct_and_relevant", 
            "incorrect_but_relevant", "incorrect_and_off_topic", 
            "refusal_no_answer", "ambiguous_answer"
        ] else "partially_correct_and_relevant"
        correctness = raw_corr if raw_corr in [
            "correct", "partially_correct", "incorrect", "misconception", "off_topic"
        ] else "partially_correct"

    if relevance == "correct_and_relevant" and correctness == "correct":
        rel_score = float(raw_eval_data.get("relevance_to_question", 3.0))
        fact_score = float(raw_eval_data.get("factual_correctness", 3.0))
        comp_score = float(raw_eval_data.get("completeness", 2.0))
        depth_score = float(raw_eval_data.get("technical_depth_reasoning", 1.5))
        total_score = rel_score + fact_score + comp_score + depth_score
        total_score = max(7.0, min(10.0, total_score))
    elif relevance == "partially_correct_and_relevant" or correctness == "partially_correct":
        rel_score = float(raw_eval_data.get("relevance_to_question", 2.0))
        fact_score = float(raw_eval_data.get("factual_correctness", 2.0))
        comp_score = float(raw_eval_data.get("completeness", 1.0))
        depth_score = float(raw_eval_data.get("technical_depth_reasoning", 1.0))
        total_score = rel_score + fact_score + comp_score + depth_score
        total_score = max(4.5, min(6.0, total_score))
    elif correctness == "misconception":
        rel_score = 2.0
        fact_score = 1.0
        comp_score = 0.5
        depth_score = 0.5
        total_score = 4.0
    elif relevance == "refusal_no_answer":
        rel_score = 0.0
        fact_score = 0.0
        comp_score = 0.0
        depth_score = 0.0
        total_score = 1.0
    elif relevance == "incorrect_and_off_topic" or correctness == "off_topic":
        rel_score = 0.0
        fact_score = 1.0
        comp_score = 0.0
        depth_score = 0.5
        total_score = 1.5
    else:
        rel_score = 1.0
        fact_score = 1.0
        comp_score = 0.5
        depth_score = 0.5
        total_score = 3.0

    if relevance == "incorrect_and_off_topic" or correctness == "off_topic":
        total_score = min(total_score, 2.0)
        rel_score = min(rel_score, 0.5)

    if relevance == "refusal_no_answer":
        total_score = min(total_score, 1.0)
        rel_score = 0.0

    if correctness == "misconception":
        total_score = min(total_score, 4.0)

    if correctness == "incorrect":
        total_score = min(total_score, 4.0)

    if relevance == "partially_correct_and_relevant" or correctness == "partially_correct":
        total_score = min(total_score, 6.0)

    if relevance != "correct_and_relevant" or correctness != "correct":
        total_score = min(total_score, 6.0)

    total_score = round(total_score, 1)

    result = dict(raw_eval_data)
    result["question"] = latest_question.get("question_text", "")
    result["topic"] = latest_question.get("topic", "")
    result["expected_concepts"] = expected_concepts
    result["required_concepts"] = expected_concepts
    result["candidate_answer"] = candidate_answer_text
    result["relevance"] = relevance
    result["correctness"] = correctness
    result["relevance_to_question"] = rel_score
    result["factual_correctness"] = fact_score
    result["completeness"] = comp_score
    result["technical_depth_reasoning"] = depth_score
    result["technical_accuracy"] = total_score
    result["overall_score"] = total_score

    if relevance == "incorrect_and_off_topic":
        result["strengths"] = []
        result["weaknesses"] = ["Candidate response did not answer the asked question (off-topic)."]
        result["evidence"] = "Candidate provided an answer that was off-topic for the asked question."
    elif correctness == "misconception":
        result["weaknesses"] = result.get("weaknesses", []) or ["Candidate expressed a technical misconception."]
        result["evidence"] = "Candidate stated a technical misconception."
    elif relevance == "correct_and_relevant":
        result["strengths"] = result.get("strengths", []) or ["Accurately answered question concepts."]
        result["evidence"] = "Candidate accurately answered the asked technical question."

    return result

async def evaluator_node(state: InterviewState) -> InterviewState:
    logger.info(f"Running Evaluator Node for session: {state.get('session_id')}")
    llm = LLMProvider()
    
    questions = state.get("questions", [])
    answers = state.get("answers", [])
    
    if not questions or not answers:
        logger.warning("Evaluator node invoked without active question or answer.")
        return state

    latest_question = questions[-1]
    latest_answer = answers[-1]
    logger.info(f"Evaluator evaluating question: {latest_question.get('question_id')}")
    
    question_json = json.dumps(latest_question, indent=2)
    candidate_answer_text = latest_answer.get("answer_text", "")
    expected_concepts_json = json.dumps(latest_question.get("expected_concepts", []), indent=2)
    history_summary = state.get("conversation_summary", "")
    
    prompt = get_evaluator_prompt(
        question_json,
        candidate_answer_text,
        expected_concepts_json,
        history_summary
    )
    
    raw_eval_data = await llm.generate_json(prompt, temperature=0.1)
    eval_data = compute_evaluation_metrics(latest_question, candidate_answer_text, raw_eval_data)
    
    eval_data["evaluation_id"] = f"eval_{uuid.uuid4().hex[:8]}"
    eval_data["question_id"] = latest_question.get("question_id")
    eval_data["session_id"] = state.get("session_id")
    
    state["relevance"] = eval_data.get("relevance", "partially_correct_and_relevant")
    state["topic_alignment"] = eval_data.get("relevance", "partially_correct_and_relevant")

    if "evaluations" not in state or state["evaluations"] is None:
        state["evaluations"] = []
    state["evaluations"].append(eval_data)
    state["answer_evaluations"] = state["evaluations"]
    
    # Update candidate model & state scores
    overall_score = float(eval_data.get("overall_score", 7.0))
    all_scores = [float(e.get("overall_score", 0.0)) for e in state["evaluations"]]
    state["technical_score"] = round(sum(all_scores) / len(all_scores), 2)
    state["overall_score"] = state["technical_score"]

    # Track strengths, weaknesses, and detected gaps
    strengths = state.get("strengths", [])
    for s in eval_data.get("strengths", []):
        if s and s not in strengths:
            strengths.append(s)
    state["strengths"] = strengths

    weaknesses = state.get("weaknesses", [])
    for w in eval_data.get("weaknesses", []):
        if w and w not in weaknesses:
            weaknesses.append(w)
    state["weaknesses"] = weaknesses

    detected_gaps = state.get("detected_gaps", [])
    for gap in eval_data.get("missing_concepts", []):
        if gap and gap not in detected_gaps:
            detected_gaps.append(gap)
    state["detected_gaps"] = detected_gaps

    misconceptions = state.get("misconceptions", [])
    for m in eval_data.get("misconceptions", []):
        m_item = m if isinstance(m, dict) else {"misconception": str(m)}
        if m_item not in misconceptions:
            misconceptions.append(m_item)
    state["misconceptions"] = misconceptions

    current_topic = latest_question.get("topic")
    covered_topics = list(state.get("covered_topics", []))
    if current_topic and current_topic not in covered_topics:
        covered_topics.append(current_topic)
        state["covered_topics"] = covered_topics
        rem = list(state.get("remaining_topics", []))
        if current_topic in rem:
            rem.remove(current_topic)
            state["remaining_topics"] = rem

    state["topics_covered"] = state.get("covered_topics", [])

    current_day = latest_question.get("curriculum_day")
    covered_days = list(state.get("covered_days", []))
    if current_day and current_day not in covered_days:
        covered_days.append(current_day)
        state["covered_days"] = covered_days

    state["last_decision"] = f"Evaluated answer for question {latest_question.get('question_id')}. Correctness: {eval_data.get('correctness', 'evaluated')}, Score: {overall_score}"
    state["next_action"] = "UPDATE_MEMORY"
    return state


