import json
import uuid
from typing import List
from app.agents.state import InterviewState
from app.prompts.interviewer_prompt import get_interviewer_prompt
from app.prompts.followup_prompt import get_followup_prompt
from app.services.llm_provider import LLMProvider
from app.utils.logger import logger

def normalize_text(text: str) -> str:
    return "".join(c.lower() for c in text if c.isalnum())

def is_substantially_similar(q_text: str, asked_questions: List[str]) -> bool:
    if not q_text or not q_text.strip():
        return True
    
    norm_q = normalize_text(q_text)
    for prev in asked_questions:
        if prev and norm_q == normalize_text(prev):
            return True

    def tokenize(s: str) -> set:
        words = "".join(c.lower() if c.isalnum() else " " for c in s).split()
        # Keep dimension indicator words (why, how, compare, versus) out of stopwords!
        stopwords = {
            "what", "is", "do", "does", "the", "a", "an", "and", "or", 
            "in", "on", "to", "for", "of", "with", "you", "can", "explain", 
            "describe", "your", "could", "would", "please", "are", "were", "been"
        }
        tokens = set()
        for w in words:
            if w not in stopwords and len(w) > 2:
                w_stem = w.rstrip("s").rstrip("e")
                tokens.add(w_stem)
        return tokens

    new_tokens = tokenize(q_text)
    if not new_tokens:
        return False

    def get_dimension(tokens: set) -> str:
        if tokens.intersection({
            "purpose", "use", "purpos", "us", "role", "benefit", "why", "value", 
            "advantage", "goal", "motiv"
        }):
            return "purpose"
        if tokens.intersection({
            "how", "work", "algorithm", "step", "mechanic", "process", "internal", 
            "calculat", "comput", "operat", "under-the-hood", "underneath"
        }):
            return "how_it_works"
        if tokens.intersection({
            "tradeoff", "trade-off", "tradeoffs", "overhead", "memory", "ram", "cost", 
            "latency", "throughput", "qps", "efficiency", "resource", "recal", "precision", 
            "speed", "fast", "vram", "bottleneck", "footprint"
        }):
            return "tradeoff"
        if tokens.intersection({
            "architect", "design", "system", "structure", "pipeline", "compon", 
            "flow", "scal", "integrat", "gateway"
        }):
            return "architecture"
        if tokens.intersection({
            "debug", "diagnos", "fail", "error", "outag", "issue", "troubleshoot", 
            "fix", "repair", "invalid", "exception", "mitigat"
        }):
            return "debugging"
        if tokens.intersection({
            "implement", "code", "configur", "parameter", "setting", "setup", 
            "syntax", "invok", "function", "schema"
        }):
            return "implementation"
        if tokens.intersection({
            "compar", "differ", "versus", " vs ", "contrast", "distinct", "head-to-head"
        }):
            return "comparison"
        if tokens.intersection({
            "scenario", "produc", "deploy", "casework", "situat", "real-world", "workload"
        }):
            return "scenario"
        return "general"

    new_dim = get_dimension(new_tokens)
    tech_concept_keywords = {
        "vector", "database", "databas", "chunk", "token", "rag", "embed", 
        "hnsw", "pydantic", "json", "prompt", "retrieval", "search", "guardrail", 
        "ivf", "rerank", "ann", "bpe", "llm", "agent"
    }

    for prev in asked_questions:
        if not prev or not str(prev).strip():
            continue
        prev_tokens = tokenize(prev)
        if not prev_tokens:
            continue
        
        overlap = new_tokens.intersection(prev_tokens)
        prev_dim = get_dimension(prev_tokens)
        
        concept_overlap = overlap.intersection(tech_concept_keywords)
        
        # If testing different technical dimensions of a technology (e.g. HNSW speed vs HNSW memory trade-off), DO NOT flag as duplicate!
        if new_dim != "general" and prev_dim != "general" and new_dim != prev_dim:
            continue

        jaccard = len(overlap) / max(len(new_tokens.union(prev_tokens)), 1)
        if jaccard >= 0.35:
            return True
        
        if len(concept_overlap) >= 1 and (new_dim == prev_dim or new_dim == "general" or prev_dim == "general"):
            return True

        if len(new_tokens) >= 1 and len(overlap) >= len(new_tokens) and len(prev_tokens) <= len(new_tokens) + 2:
            return True

    return False




def validate_question_grounding(q_data: dict, turn_plan: dict, asked_questions: List[str]) -> dict:
    target_topic = (turn_plan.get("topic") or "").lower()
    q_topic = (q_data.get("topic") or "").lower()
    q_text = (q_data.get("question_text") or "").lower()
    is_follow_up = bool(turn_plan.get("is_follow_up", False))
    target_concept = (turn_plan.get("target_concept") or "").lower()
    req_q_type = (turn_plan.get("question_type") or "conceptual").lower()
    actual_q_type = (q_data.get("question_type") or "").lower()

    # 1. Topic Alignment
    topic_keywords_map = {
        "day1_tokenization": ["token", "bpe", "wordpiece", "vocab", "tokenizer", "subword", "oov"],
        "day1_api_calling": ["api", "rate limit", "temperature", "top_p", "system prompt"],
        "day2_structured_outputs": ["json", "pydantic", "schema", "structured", "seed", "sampling"],
        "day2_function_calling": ["tool", "function", "function call", "sandbox"],
        "day6_vector_embeddings": ["embedding", "vector", "latent", "space", "cosine", "distance", "similarity"],
        "day7_chunking": ["chunk", "overlap", "sliding", "window", "semantic chunking", "splitting"],
        "day8_vector_databases": ["hnsw", "ivf", "ann", "vector db", "pinecone", "milvus", "qdrant", "faiss", "index"],
        "day9_rag_pipelines": ["rag", "retrieval", "rerank", "cross-encoder", "bi-encoder", "context"],
        "day13_agent_basics": ["agent", "tool", "state machine", "langgraph", "react", "action"],
        "day21_rag_evaluation": ["ragas", "faithfulness", "answer relevance", "context precision", "evaluation"],
        "day26_production_guardrails": ["guardrail", "nemo", "llama guard", "prompt injection", "jailbreak", "pagedattention", "vllm"]
    }

    t_words = topic_keywords_map.get(target_topic, [target_topic])
    topic_aligned = (q_topic == target_topic) or any(w in q_text for w in t_words)

    # Critical check: reject speculative decoding when asking about vector embeddings / vector DBs / chunking / RAG
    if any(k in target_topic for k in ["embedding", "vector", "chunk", "rag"]):
        if "speculative decoding" in q_text or "draft model" in q_text:
            topic_aligned = False

    # 2. Stronger Target-Concept Validation (Do NOT allow generic topic words to automatically satisfy target_concept)
    target_concept_aligned = True
    if is_follow_up and target_concept:
        concept_term_map = {
            "ann indexing vs exact search": ["ann", "hnsw", "ivf", "approximate", "exact", "nearest neighbor", "index", "search", "vector", "recall"],
            "ann indexing": ["ann", "hnsw", "ivf", "approximate", "nearest neighbor", "index"],
            "chunk overlap": ["overlap", "sliding window", "chunk size", "boundary", "context"],
            "pydantic validation": ["pydantic", "validation", "schema", "field"],
            "prompt injection": ["injection", "jailbreak", "nemo", "llama guard"],
            "rerank": ["rerank", "cross-encoder", "bi-encoder", "re-score"],
            "cosine similarity": ["cosine", "dot product", "l2 distance", "norm"]
        }
        
        c_keywords = None
        for key, terms in sorted(concept_term_map.items(), key=lambda x: len(x[0]), reverse=True):
            if key in target_concept:
                c_keywords = terms
                break
        
        if not c_keywords:
            concept_words = [w for w in "".join(c.lower() if c.isalnum() else " " for c in target_concept).split() if len(w) > 3]
            c_keywords = [
                w for w in concept_words 
                if w not in {"core", "mechanics", "operational", "system", "design", "concept", "understanding", "topic", "vector", "embeddings", "tokenization", "chunking", "databases", "pipelines", "evaluation", "guardrails"} 
                and not w.startswith("day")
            ]

        if c_keywords:
            target_concept_aligned = any(term in q_text or term.rstrip("s") in q_text for term in c_keywords)
        elif target_topic in topic_keywords_map:
            target_concept_aligned = any(w in q_text or w.rstrip("s") in q_text for w in topic_keywords_map[target_topic])
        else:
            target_concept_aligned = True



    # 3. Question Type Validation
    question_type_aligned = True
    if req_q_type:
        type_keywords = {
            "trade_off": ["trade-off", "tradeoff", "versus", " vs ", "compare", "overhead", "latency", "recall", "build time", "query throughput", "cost"],
            "trade-off": ["trade-off", "tradeoff", "versus", " vs ", "compare", "overhead", "latency", "recall", "build time", "query throughput", "cost"],
            "scenario": ["how would you", "what happens when", "how do you handle", "how do you calculate", "situation", "if a production", "when deploying"],
            "architecture": ["architect", "design", "production deployment", "high-throughput", "scaling", "system", "components"],
            "system_design": ["architect", "design", "production deployment", "high-throughput", "scaling", "system", "100m", "large-scale"],
            "debugging": ["diagnose", "debug", "failure", "retry", "repair", "invalid", "error", "outage", "broken"],
            "implementation": ["implement", "configure", "parameters", "code", "sequence", "how do you set"],
            "comparison": ["compare", "difference", "versus", " vs ", "differ", "handles"],
            "best_practice": ["prevent", "best practice", "guarantee", "sanitize", "secure", "reliability"]
        }
        
        req_type_clean = req_q_type.replace("_", "-").replace(" ", "-")
        actual_type_clean = actual_q_type.replace("_", "-").replace(" ", "-")
        
        if actual_type_clean == req_type_clean:
            question_type_aligned = True
        else:
            k_list = type_keywords.get(req_q_type, type_keywords.get(req_type_clean, []))
            if k_list:
                question_type_aligned = any(k in q_text for k in k_list)
            else:
                question_type_aligned = True

        # Specific rejection: if trade_off or system_design or debugging is requested, simple generic definitions fail
        if req_q_type in ["trade_off", "trade-off", "system_design", "architecture", "debugging"]:
            if (q_text.startswith("what is ") or q_text.startswith("explain the core concept")) and not any(k in q_text for k in ["trade-off", "tradeoff", "versus", " vs ", "compare", "overhead", "design", "diagnose", "debug"]):
                question_type_aligned = False

    curriculum_aligned = topic_aligned

    grounding_valid = topic_aligned and target_concept_aligned and question_type_aligned and curriculum_aligned
    reason = "Question is fully grounded and validated." if grounding_valid else f"Question violates grounding: topic_aligned={topic_aligned}, target_concept_aligned={target_concept_aligned}, question_type_aligned={question_type_aligned}."

    return {
        "grounding_valid": grounding_valid,
        "topic_aligned": topic_aligned,
        "target_concept_aligned": target_concept_aligned,
        "question_type_aligned": question_type_aligned,
        "curriculum_aligned": curriculum_aligned,
        "reason": reason
    }


async def question_generator_node(state: InterviewState) -> InterviewState:
    logger.info(f"Running Question Generator Node for session: {state.get('session_id')}")
    llm = LLMProvider()
    
    evaluations = state.get("evaluations", [])
    questions = state.get("questions", [])
    answers = state.get("answers", [])
    turn_plan = state.get("turn_plan") or {}
    
    asked_question_texts = [q.get("question_text", "").strip() for q in questions if q.get("question_text")]
    asked_questions_json = json.dumps(asked_question_texts, indent=2)

    strategy_json = json.dumps(state.get("interview_plan", {}), indent=2)
    turn_plan_json = json.dumps(turn_plan, indent=2)
    candidate_profile_json = json.dumps(state.get("candidate_profile", {}), indent=2)
    
    current_topic = turn_plan.get("topic") or state.get("current_topic") or "day1_tokenization"
    current_difficulty = turn_plan.get("difficulty") or state.get("current_difficulty", 2)
    target_topic_json = json.dumps({"topic_id": current_topic})
    
    history_summary = state.get("conversation_summary", "")
    last_answer_json = json.dumps(answers[-1] if answers else {}, indent=2)
    last_eval_json = json.dumps(evaluations[-1] if evaluations else {}, indent=2)
    detected_gaps_json = json.dumps(state.get("detected_gaps", []), indent=2)
    topics_covered_json = json.dumps(state.get("covered_topics", []), indent=2)
    question_types_used_json = json.dumps(state.get("question_types_used", []), indent=2)
    questions_remaining = max(0, 8 - len(questions))

    is_follow_up = turn_plan.get("is_follow_up", False)
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

    learning_obj = f"Master core engineering concepts, operational mechanics, and trade-offs of {current_topic}"
    assessment_obj = f"Evaluate technical depth, candidate reasoning, and design maturity at difficulty level {current_difficulty}"

    MAX_DUPLICATE_RETRIES = 5
    attempts = 0
    q_data = None
    dimensions_cycle = ["purpose", "how_it_works", "tradeoff", "architecture", "debugging", "implementation", "scenario", "comparison"]

    while attempts < MAX_DUPLICATE_RETRIES:
        attempts += 1
        
        if attempts == 1:
            if is_follow_up and len(questions) > 0 and len(answers) > 0:
                logger.info("Generating follow-up question based on turn plan and latest response...")
                prev_q = questions[-1].get("question_text", "")
                prev_ans = answers[-1].get("answer_text", "")
                prompt = get_followup_prompt(
                    prev_q, 
                    prev_ans, 
                    last_eval_json, 
                    history_summary, 
                    asked_questions_json,
                    target_topic=current_topic,
                    target_concept=turn_plan.get("target_concept", ""),
                    follow_up_reason=turn_plan.get("follow_up_reason", "")
                )
                cand_q_data = await llm.generate_json(prompt, temperature=0.4)
                cand_q_data["is_follow_up"] = True
                cand_q_data["parent_question_id"] = questions[-1].get("question_id")
            else:
                prompt = get_interviewer_prompt(
                    strategy_json=strategy_json,
                    turn_plan_json=turn_plan_json,
                    candidate_profile_json=candidate_profile_json,
                    target_topic_json=target_topic_json,
                    current_difficulty=current_difficulty,
                    history_summary=history_summary,
                    asked_questions_json=asked_questions_json,
                    last_answer_json=last_answer_json,
                    last_evaluation_json=last_eval_json,
                    detected_gaps_json=detected_gaps_json,
                    topics_covered_json=topics_covered_json,
                    question_types_used_json=question_types_used_json,
                    questions_remaining=questions_remaining
                )
                cand_q_data = await llm.generate_json(prompt, temperature=0.5)
                cand_q_data["is_follow_up"] = False
        else:
            suggested_dim = dimensions_cycle[(attempts - 2) % len(dimensions_cycle)]
            retry_prompt = (
                f"Generate a NEW, DISTINCT technical question for topic '{current_topic}' at difficulty level {current_difficulty}.\n"
                f"Question Type: {turn_plan.get('question_type', 'Conceptual')}\n"
                f"Focus on the '{suggested_dim}' technical dimension of {current_topic}.\n"
                f"CRITICAL REQUIREMENT: Do NOT generate a question similar to any of these previously asked questions:\n"
                + "\n".join([f"- {q}" for q in asked_question_texts]) + "\n"
                f"Return valid JSON with keys: question_text, question_type, intent, expected_concepts."
            )
            cand_q_data = await llm.generate_json(retry_prompt, temperature=0.6)
            cand_q_data["is_follow_up"] = is_follow_up

        cand_q_data["curriculum_day"] = topic_day_map.get(current_topic, cand_q_data.get("curriculum_day", 1))
        cand_q_data["topic"] = current_topic
        cand_q_data["difficulty"] = current_difficulty
        cand_q_data["question_type"] = turn_plan.get("question_type", cand_q_data.get("question_type", "Conceptual"))

        curr_text = (cand_q_data.get("question_text") or "").strip()
        is_dup = is_substantially_similar(curr_text, asked_question_texts)
        grounding_val = validate_question_grounding(cand_q_data, turn_plan, asked_question_texts)

        if curr_text and not is_dup and grounding_val["grounding_valid"] and "explainthecoreengineeringconcepts" not in normalize_text(curr_text):
            q_data = cand_q_data
            break
        else:
            logger.warning(f"Attempt {attempts}: Question rejected (is_dup={is_dup}, grounding={grounding_val['grounding_valid']}): '{curr_text}'")

    if not q_data:
        logger.warning(f"All LLM attempts rejected or provider in mock mode. Fetching guaranteed non-duplicate question for topic '{current_topic}'.")
        prompt_with_asked = f"TARGET TOPIC DETAILS: {current_topic} ### CURRENT DIFFICULTY LEVEL (1-5): {current_difficulty} ### QUESTION TYPE: {turn_plan.get('question_type')} ### PREVIOUSLY ASKED QUESTIONS:\n" + "\n".join(asked_question_texts)
        if is_follow_up:
            prompt_with_asked += f"\n### FOLLOWUP REQUEST TARGET CONCEPT: {turn_plan.get('target_concept', current_topic)}"
        
        q_data = llm._select_mock_question(prompt_with_asked, asked_question_texts=asked_question_texts)
        q_data["topic"] = current_topic
        q_data["is_follow_up"] = is_follow_up

    q_data["question_id"] = f"q_{uuid.uuid4().hex[:8]}"
    q_data["session_id"] = state.get("session_id")
    q_data["learning_objective"] = learning_obj
    q_data["assessment_objective"] = assessment_obj
    if is_follow_up:
        state["follow_up_count"] = state.get("follow_up_count", 0) + 1

    final_grounding = validate_question_grounding(q_data, turn_plan, asked_question_texts)
    q_data["grounding_validation"] = final_grounding

    state["learning_objective"] = learning_obj
    state["assessment_objective"] = assessment_obj
    state["current_question"] = q_data
    state["questions"].append(q_data)

    state["questions_asked"] = state["questions"]
    state["current_question_index"] = len(state["questions"]) - 1
    state["question_number"] = len(state["questions"])
    state["recent_question_texts"] = [q.get("question_text", "") for q in state["questions"][-4:]]

    # Track questions by topic
    q_by_topic = dict(state.get("questions_by_topic", {}))
    t_key = q_data.get("topic", current_topic)
    q_by_topic[t_key] = q_by_topic.get(t_key, 0) + 1
    state["questions_by_topic"] = q_by_topic

    state["last_decision"] = f"Generated question {q_data['question_id']} ({q_data.get('question_type')}) for topic {q_data.get('topic')} at difficulty level {q_data.get('difficulty', current_difficulty)}"
    return state



