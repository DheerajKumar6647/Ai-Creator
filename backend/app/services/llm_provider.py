import os
import json
import random
from typing import Dict, Any, Optional
from app.config.settings import settings
from app.utils.logger import logger

def normalize_question_text(text: str) -> str:
    return "".join(c.lower() for c in text if c.isalnum())

def is_substantially_similar(q_text: str, asked_questions: list) -> bool:
    if not q_text or not q_text.strip():
        return True
    
    norm_q = normalize_question_text(q_text)
    for prev in asked_questions:
        if prev and norm_q == normalize_question_text(prev):
            return True

    def tokenize(s: str) -> set:
        words = "".join(c.lower() if c.isalnum() else " " for c in s).split()
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






class LLMProvider:
    """
    Unified LLM Provider abstraction supporting Gemini, OpenAI, and Mock Mode.
    """
    def __init__(self, provider_type: Optional[str] = None):
        self.provider_type = provider_type or settings.DEFAULT_LLM_PROVIDER
        if self.provider_type == "gemini" and not settings.GEMINI_API_KEY:
            logger.warning("Gemini API key not found. Falling back to mock provider.")
            self.provider_type = "mock"
        elif self.provider_type == "openai" and not settings.OPENAI_API_KEY:
            logger.warning("OpenAI API key not found. Falling back to mock provider.")
            self.provider_type = "mock"

    async def generate_json(self, prompt: str, schema: Optional[Dict[str, Any]] = None, temperature: float = 0.2) -> Dict[str, Any]:
        """
        Generate structured JSON output from LLM prompt.
        """
        if self.provider_type == "mock":
            return self._generate_mock_json(prompt)
        elif self.provider_type == "gemini":
            return await self._generate_gemini_json(prompt, temperature)
        elif self.provider_type == "openai":
            return await self._generate_openai_json(prompt, temperature)
        else:
            return self._generate_mock_json(prompt)

    async def generate_text(self, prompt: str, temperature: float = 0.4) -> str:
        """
        Generate free-form text response.
        """
        if self.provider_type == "mock":
            return "Mock AI response generated for context."
        elif self.provider_type == "gemini":
            return await self._generate_gemini_text(prompt, temperature)
        elif self.provider_type == "openai":
            return await self._generate_openai_text(prompt, temperature)
        else:
            return "Mock AI response generated for context."

    async def _generate_gemini_json(self, prompt: str, temperature: float) -> Dict[str, Any]:
        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel(
                model_name=settings.GEMINI_MODEL,
                generation_config={"response_mime_type": "application/json", "temperature": temperature}
            )
            response = model.generate_content(prompt)
            return json.loads(response.text)
        except Exception as e:
            logger.error(f"Gemini API error: {e}. Falling back to mock response.")
            return self._generate_mock_json(prompt)

    async def _generate_openai_json(self, prompt: str, temperature: float) -> Dict[str, Any]:
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            response = await client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[{"role": "system", "content": "You are a JSON generator. Output only valid JSON."},
                          {"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=temperature
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"OpenAI API error: {e}. Falling back to mock response.")
            return self._generate_mock_json(prompt)

    async def _generate_gemini_text(self, prompt: str, temperature: float) -> str:
        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel(model_name=settings.GEMINI_MODEL)
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Gemini text error: {e}")
            return "Unable to process text request."

    async def _generate_openai_text(self, prompt: str, temperature: float) -> str:
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            response = await client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI text error: {e}")
            return "Unable to process text request."

    def _generate_mock_json(self, prompt: str) -> Dict[str, Any]:
        """
        Generate realistic, domain-aware mock responses based on key prompt phrases and dynamic topic banks.
        """
        prompt_lower = prompt.lower()

        # 1. Feedback / Hiring Report Node
        if "feedback & hiring recommender" in prompt_lower or "hiring recommendation based" in prompt_lower or "feedback agent" in prompt_lower or "hiring_recommendation" in prompt_lower:
            return {

                "overall_rating": 8.2,
                "overall_score": 8.2,
                "technical_score": 8.2,
                "communication_score": 8.8,
                "reasoning_score": 8.0,
                "technical_summary": "Demonstrated strong foundational AI understanding across embeddings, tokenization, and RAG pipelines.",
                "communication_summary": "Articulate, structured, and used appropriate software engineering vocabulary throughout.",
                "engineering_thinking_summary": "Demonstrated good awareness of trade-offs, with minor gaps in high-scale vector indexing.",
                "interview_summary": "Completed structured adaptive technical interview with 8 questions across 4 curriculum days.",
                "overall_readiness": "Interview Ready",
                "hiring_recommendation": "HIRE",
                "hiring_recommendation_reason": "Candidate demonstrated strong theoretical knowledge, code-level precision, and good system design awareness.",
                "recommendation_confidence": 0.88,
                "recommendation_reasoning": "Candidate showed solid theoretical and practical knowledge in RAG architecture and embeddings.",
                "scores": {
                    "Technical Knowledge": 8.2,
                    "Conceptual Understanding": 8.5,
                    "Engineering Thinking": 7.8,
                    "Problem Solving": 8.0,
                    "Communication": 8.8,
                    "Confidence": 8.0
                },
                "topic_scores": {
                    "day1_tokenization": 8.5,
                    "day7_chunking": 7.5,
                    "day8_vector_databases": 7.2,
                    "day9_rag_pipelines": 8.5
                },
                "strengths": [
                    "Strong foundational understanding of dense vector embeddings",
                    "Clear articulation of cosine similarity vs Euclidean metrics",
                    "Good structured programming approach to RAG pipelines"
                ],
                "weaknesses": [
                    "Incomplete justification of HNSW graph indexing vs IVF inverted file indices",
                    "Uncertainty around context window duplication during large chunk overlaps"
                ],
                "misconceptions": [],
                "misconception_report": [
                    {
                        "misconception": "Believed vector embeddings store raw document text inside the index.",
                        "correct_concept": "Vector embeddings represent numerical coordinates in latent space; text metadata must be retrieved separately.",
                        "impact": "Low",
                        "suggested_practice": "Review vector index metadata architecture."
                    }
                ],
                "topic_breakdown": [
                    {"topic_name": "Embeddings", "score": 8.8, "level": "Applied Engineering"},
                    {"topic_name": "Document Chunking", "score": 7.5, "level": "Intermediate"},
                    {"topic_name": "Vector DBs", "score": 7.2, "level": "Intermediate"},
                    {"topic_name": "RAG Architecture", "score": 8.5, "level": "Applied Engineering"}
                ],
                "topics_to_revise": ["Vector DB Indexing (HNSW)", "RAG Evaluation Metrics"],
                "observed_strengths": [
                    "Strong foundational understanding of RAG architectures and chunking strategies.",
                    "Demonstrated deep knowledge of HNSW indexing and vector similarity search.",
                    "Articulated production trade-offs accurately across multiple curriculum domains."
                ],
                "observed_weaknesses": [
                    "Could expand further on low-latency streaming guardrail optimizations."
                ],
                "detected_gaps": [],
                "misconceptions_verified": [],
                "topics_covered": ["day1_tokenization", "day2_structured_outputs", "day6_vector_embeddings", "day7_chunking", "day8_vector_databases", "day9_rag_pipelines"],
                "recommended_study_plan": [
                    "Deep-dive into vLLM PagedAttention KV cache memory layout",
                    "Explore speculative decoding draft model benchmarking"
                ],
                "summary": "Candidate demonstrated exceptional technical mastery across 6 curriculum days, providing structured trade-off reasoning and precise architectural answers."
            }

        # 2. Turn Planner Node (Per-Turn Strategy)
        elif "decide the exact strategy" in prompt_lower or "decision rules" in prompt_lower or "turn planner agent" in prompt_lower:
            all_curriculum_topics = [
                "day1_tokenization", "day2_structured_outputs", "day6_vector_embeddings", 
                "day7_chunking", "day8_vector_databases", "day9_rag_pipelines", 
                "day13_agent_basics", "day21_rag_evaluation", "day26_production_guardrails"
            ]

            # Extract recent evaluations section specifically
            recent_evals_str = ""
            if "### recent answer evaluations:" in prompt_lower:
                try:
                    recent_evals_str = prompt_lower.split("### recent answer evaluations:")[1].split("###")[0].strip()
                except Exception:
                    recent_evals_str = ""

            logger.info(f"MOCK TURN PLANNER recent_evals_str: {recent_evals_str}")

            is_poor = False
            is_strong = False
            is_misconception = False
            is_off_topic = False
            if recent_evals_str and recent_evals_str != "[]":
                if '"correctness": "off_topic"' in recent_evals_str or "off_topic" in recent_evals_str or "off-topic" in recent_evals_str:
                    is_off_topic = True
                elif '"correctness": "misconception"' in recent_evals_str or "guarantee exact" in recent_evals_str:
                    is_misconception = True
                elif '"correctness": "shallow"' in recent_evals_str or '"correctness": "incorrect"' in recent_evals_str or '"correctness": "partially_correct"' in recent_evals_str:
                    is_poor = True
                elif '"correctness": "correct"' in recent_evals_str or '"technical_depth": "high"' in recent_evals_str or "overall_score\": 8." in recent_evals_str or "overall_score\": 9." in recent_evals_str or "overall_score\": 7." in recent_evals_str:
                    is_strong = True

            curr_topic = "day1_tokenization"
            for t in all_curriculum_topics:
                if f"current topic: {t}" in prompt_lower:
                    curr_topic = t
                    break

            curr_diff = 2
            if "current difficulty level (1-5): 3" in prompt_lower:
                curr_diff = 3
            elif "current difficulty level (1-5): 4" in prompt_lower:
                curr_diff = 4
            elif "current difficulty level (1-5): 5" in prompt_lower:
                curr_diff = 5

            # Parse covered topics specifically from state section
            covered_str = ""
            if "topics covered so far:" in prompt_lower:
                try:
                    covered_str = prompt_lower.split("topics covered so far:")[1].split("\n")[0]
                except Exception:
                    pass

            uncovered = [t for t in all_curriculum_topics if t not in covered_str and t != curr_topic]

            if is_off_topic:
                is_follow_up = True
                target_topic = curr_topic
                q_type = "conceptual"
                off_topic_action = "redirect"
                follow_up_reason = "missing_concept"
                reason = "Candidate response was off-topic; planning explicit redirection back to current curriculum topic."
                target_diff = curr_diff
                target_concept = "core concepts of " + curr_topic
                evidence_from_answer = "Candidate provided an off-topic response."
            elif is_misconception:
                is_follow_up = True
                target_topic = curr_topic
                q_type = "trade_off"
                off_topic_action = "none"
                follow_up_reason = "misconception"
                reason = "Candidate expressed misconception that vector DBs guarantee exact search; planning targeted follow-up on ANN vs exact search."
                target_diff = curr_diff
                target_concept = "ANN indexing vs exact search"
                evidence_from_answer = "Candidate stated vector databases always guarantee exact nearest-neighbor search."
            elif is_poor:
                is_follow_up = True
                target_topic = curr_topic
                q_type = "scenario" if "shallow" in recent_evals_str else "conceptual"
                off_topic_action = "none"
                follow_up_reason = "missing_concept"
                reason = "Candidate answer was shallow/partially correct; probing missing concepts with follow-up scenario."
                target_diff = max(1, curr_diff)
                target_concept = "operational mechanics of " + curr_topic
                evidence_from_answer = "Candidate answer omitted underlying data structures and trade-offs."
            elif is_strong or not recent_evals_str or "[]" in recent_evals_str:
                # Competency progression mapping instead of static array indexing
                competency_graph = {
                    "day1_tokenization": "day6_vector_embeddings",
                    "day1_api_calling": "day2_structured_outputs",
                    "day2_structured_outputs": "day6_vector_embeddings",
                    "day6_vector_embeddings": "day8_vector_databases",
                    "day7_chunking": "day8_vector_databases",
                    "day8_vector_databases": "day9_rag_pipelines",
                    "day9_rag_pipelines": "day13_agent_basics",
                    "day13_agent_basics": "day21_rag_evaluation"
                }
                
                if curr_topic in competency_graph and competency_graph[curr_topic] not in covered_str:
                    target_topic = competency_graph[curr_topic]
                elif uncovered:
                    target_topic = uncovered[0]
                else:
                    target_topic = curr_topic
                
                is_follow_up = False
                target_diff = min(5, curr_diff + (1 if is_strong else 0))
                q_type = "trade_off" if target_diff <= 3 else "architecture"
                off_topic_action = "none"
                follow_up_reason = "none"
                reason = "Candidate demonstrated strong performance; advancing difficulty and transitioning to complementary competency."
                target_concept = "system design of " + target_topic
                evidence_from_answer = "Candidate gave detailed, high-accuracy response with key technical terms."
                topic_sel_reason = f"Candidate demonstrated strong mastery of {curr_topic}; advancing competency to {target_topic}."
                topic_sel_basis = ["strong_current_topic_performance", "prerequisite_satisfied", "new_competency"]
                q_type_reason = f"Candidate demonstrated high technical accuracy; evaluating production {q_type} trade-offs."
            else:
                if uncovered:
                    target_topic = uncovered[0]
                    is_follow_up = False
                else:
                    target_topic = curr_topic
                    is_follow_up = False
                target_diff = curr_diff
                q_type = "trade_off"
                off_topic_action = "none"
                follow_up_reason = "none"
                reason = "Continuing curriculum assessment across topics with trade-off question."
                target_concept = "trade-offs of " + target_topic
                evidence_from_answer = "Candidate performance is baseline."
                topic_sel_reason = f"Evaluating curriculum topic {target_topic} for baseline coverage."
                topic_sel_basis = ["curriculum_coverage"]
                q_type_reason = "Evaluating core design trade-offs."

            if is_off_topic or is_misconception or is_poor:
                topic_sel_reason = f"Retaining topic {target_topic} to address candidate response evidence."
                topic_sel_basis = ["weakness_probing" if is_poor else ("misconception_probing" if is_misconception else "off_topic_redirection")]
                q_type_reason = f"Selected {q_type} question to assess candidate understanding after response evidence."

            return {
                "topic": target_topic,
                "topic_selection_reason": topic_sel_reason,
                "topic_selection_basis": topic_sel_basis,
                "objective": f"Evaluate core concepts and trade-offs of {target_topic}",
                "difficulty": target_diff,
                "question_type": q_type,
                "question_type_reason": q_type_reason,
                "reason": reason,
                "is_follow_up": is_follow_up,
                "follow_up_reason": follow_up_reason,
                "target_concept": target_concept,
                "evidence_from_answer": evidence_from_answer,
                "off_topic_action": off_topic_action
            }


        # 3. Initial Planner Agent (Session Strategy)
        elif "planner strategy" in prompt_lower or "planner agent for interviewai" in prompt_lower or "initial interview strategy" in prompt_lower:
            return {
                "objective": "Evaluate core knowledge in RAG, Chunking, Vector DBs, and Agent state machines.",
                "target_question_count": 8,
                "minimum_days": 4,
                "target_days": [1, 2, 6, 7, 8, 9, 13, 21],
                "topic_priorities": ["day7_chunking", "day8_vector_databases", "day9_rag_pipelines", "day13_agent_basics"],
                "difficulty_curve": [2, 3, 3, 4, 4, 3, 4, 5],
                "follow_up_strategy": "Challenge trade-offs and ask architectural questions after high accuracy.",
                "weak_topic_targets": ["day7_chunking", "day8_vector_databases"],
                "strong_topic_targets": ["day1_tokenization", "day6_vector_embeddings"]
            }

        # 4. Evaluator Agent
        elif "senior technical evaluator" in prompt_lower or "evaluation instructions" in prompt_lower:
            candidate_ans = ""
            if "<candidate_answer>" in prompt_lower:
                try:
                    candidate_ans = prompt_lower.rsplit("<candidate_answer>", 1)[-1].split("</candidate_answer>")[0].strip()
                except Exception:
                    candidate_ans = prompt_lower
            elif "### candidate answer:" in prompt_lower:
                try:
                    candidate_ans = prompt_lower.rsplit("### candidate answer:", 1)[-1].split("###")[0].strip()
                except Exception:
                    candidate_ans = prompt_lower

            logger.info(f"MOCK EVALUATOR candidate_ans: '{candidate_ans}' (words={len(candidate_ans.split())})")

            is_off_topic = "quantum computing" in candidate_ans or "cooking pasta" in candidate_ans or "unrelated topic" in candidate_ans or ("weather" in candidate_ans and "sunny" in candidate_ans)
            is_misconception = "always guarantee exact" in candidate_ans or "exact nearest" in candidate_ans or "guarantee exact nearest-neighbor" in candidate_ans or "exact nearest neighbor" in candidate_ans
            is_shallow = (len(candidate_ans.split()) < 15 or "retrieves relevant documents" in candidate_ans or "basic answer" in candidate_ans) and not is_misconception and not is_off_topic
            is_incorrect = ("don't know" in candidate_ans or "not sure" in candidate_ans or "wrong answer" in candidate_ans) and not is_off_topic
            is_strong = len(candidate_ans.split()) >= 15 or ("hnsw" in candidate_ans or "bpe" in candidate_ans or "cosine" in candidate_ans or "overlap" in candidate_ans or "precision" in candidate_ans or "ast" in candidate_ans or "nemo" in candidate_ans or "ragas" in candidate_ans or "hybrid" in candidate_ans or "vector" in candidate_ans or "chunking" in candidate_ans)

            if is_off_topic:
                return {
                    "correctness": "off_topic",
                    "relevance": "correct_but_off_topic" if "quantum" in candidate_ans else "incorrect_and_off_topic",
                    "technical_depth": "low",
                    "conceptual_understanding": "none",
                    "communication_quality": "low",
                    "confidence": "low",
                    "missing_concepts": ["core topic principles"],
                    "misconceptions": [],
                    "strengths": [],
                    "weaknesses": ["Candidate response was completely off-topic from the question asked."],
                    "recommended_follow_up": "Redirect candidate back to current curriculum topic.",
                    "recommended_difficulty": "medium",
                    "recommended_topic": "day1_tokenization",
                    "technical_accuracy": 2.0,
                    "overall_score": 2.0,
                    "evidence": "Candidate gave an answer unrelated to the asked technical question."
                }
            elif is_misconception:
                return {
                    "correctness": "misconception",
                    "relevance": "incorrect_but_relevant",
                    "technical_depth": "medium",
                    "conceptual_understanding": "partial",
                    "communication_quality": "medium",
                    "confidence": "high",
                    "missing_concepts": ["Approximate Nearest Neighbor (ANN) trade-offs", "HNSW graph probabilistic recall"],
                    "misconceptions": [{
                        "misconception": "Vector databases always guarantee exact nearest-neighbor search.",
                        "correct_concept": "Vector DBs use ANN algorithms (HNSW, IVF-PQ) that trade 100% recall for fast QPS.",
                        "impact": "High"
                    }],
                    "strengths": ["Recognizes role of vector search in AI systems."],
                    "weaknesses": ["Incorrectly assumed exact search guarantees at scale."],
                    "recommended_follow_up": "Probe understanding of ANN graph indexing vs brute-force search.",
                    "recommended_difficulty": "medium",
                    "recommended_topic": "day8_vector_databases",
                    "technical_accuracy": 4.5,
                    "overall_score": 4.5,
                    "evidence": "Candidate stated that vector databases always guarantee exact nearest-neighbor search."
                }

            elif is_incorrect:

                return {
                    "correctness": "incorrect",
                    "technical_depth": "low",
                    "conceptual_understanding": "none",
                    "communication_quality": "low",
                    "confidence": "low",
                    "missing_concepts": ["core definitions", "operational principles"],
                    "misconceptions": [{"misconception": "Candidate lacks fundamental understanding of topic"}],
                    "strengths": [],
                    "weaknesses": ["Candidate gave an incorrect or blank response."],
                    "recommended_follow_up": "ask a simpler diagnostic question to check prerequisite concepts.",
                    "recommended_difficulty": "easy",
                    "recommended_topic": "day1_tokenization",
                    "technical_accuracy": 3.0,
                    "overall_score": 3.0,
                    "evidence": "Candidate explicitly stated lack of knowledge or provided fundamentally incorrect concepts."
                }
            elif is_shallow:
                return {
                    "correctness": "shallow",
                    "technical_depth": "low",
                    "conceptual_understanding": "partial",
                    "communication_quality": "medium",
                    "confidence": "medium",
                    "missing_concepts": ["indexing", "ann search", "distributed retrieval", "scalability trade-offs"],
                    "misconceptions": [],
                    "strengths": ["basic intuitive understanding of high-level concept"],
                    "weaknesses": ["omitted underlying algorithms, data structures, and operational boundaries."],
                    "recommended_follow_up": "ask a targeted scenario question probing missing scalability and indexing concepts.",
                    "recommended_difficulty": "medium",
                    "recommended_topic": "day8_vector_databases",
                    "technical_accuracy": 5.5,
                    "overall_score": 5.5,
                    "evidence": "candidate gave a high-level overview but missed specific engineering details and trade-offs."
                }
            else:
                return {
                    "correctness": "correct",
                    "technical_depth": "high",
                    "conceptual_understanding": "full",
                    "communication_quality": "high",
                    "confidence": "high",
                    "missing_concepts": [],
                    "misconceptions": [],
                    "strengths": ["Strong architectural trade-off analysis", "Clear production considerations"],
                    "weaknesses": [],
                    "recommended_follow_up": "advance to next topic or higher difficulty level.",
                    "recommended_difficulty": "hard",
                    "recommended_topic": "day9_rag_pipelines",
                    "technical_accuracy": 8.8,
                    "overall_score": 8.8,
                    "evidence": "Candidate articulated technical concepts, data structures, and production trade-offs accurately."
                }

        # 5. Question Generator / Interviewer Node (Dynamic Question Selection)
        else:
            return self._select_mock_question(prompt_lower)


    def _select_mock_question(self, prompt_lower: str, asked_question_texts: Optional[list] = None) -> Dict[str, Any]:
        """
        Dynamically selects a topic-relevant, non-repetitive question from the mock question bank.
        Organized into 8 distinct questions per difficulty level (Levels 1 to 5).
        """
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

        # 1. Parse target topic from prompt
        detected_topic = None
        if "target topic details:" in prompt_lower:
            try:
                topic_part = prompt_lower.split("target topic details:")[1].split("###")[0].strip()
                for t_id in sorted(topic_day_map.keys(), key=len, reverse=True):
                    if t_id in topic_part:
                        detected_topic = t_id
                        break
            except Exception:
                pass

        if not detected_topic and "topic:" in prompt_lower:
            try:
                topic_part = prompt_lower.split("topic:")[1].split("\n")[0].strip()
                for t_id in sorted(topic_day_map.keys(), key=len, reverse=True):
                    if t_id in topic_part:
                        detected_topic = t_id
                        break
            except Exception:
                pass

        if not detected_topic:
            for t_id in sorted(topic_day_map.keys(), key=len, reverse=True):
                if f'"{t_id}"' in prompt_lower or f"'{t_id}'" in prompt_lower:
                    detected_topic = t_id
                    break

        if not detected_topic:
            detected_topic = "day1_tokenization"


        # 2. Parse current difficulty level (1 to 5)
        current_difficulty = 2
        if "current difficulty level (1-5):" in prompt_lower:
            try:
                diff_part = prompt_lower.split("current difficulty level (1-5):")[1].split("###")[0].strip()
                diff_digits = ''.join(filter(str.isdigit, diff_part[:10]))
                if diff_digits:
                    val = int(diff_digits)
                    if 1 <= val <= 5:
                        current_difficulty = val
            except Exception:
                pass

        # 3. Extract previously asked question texts from prompt or explicit argument
        asked_questions = list(asked_question_texts or [])
        if "previously asked questions" in prompt_lower:
            try:
                asked_part = prompt_lower.split("previously asked questions")[1].split("###")[0]
                lines = asked_part.split("\n")
                for line in lines:
                    cleaned = line.strip(" -\"'\t\r\n")
                    if len(cleaned) > 10 and cleaned not in asked_questions:
                        asked_questions.append(cleaned)
            except Exception:
                pass

        is_follow_up = "### followup request" in prompt_lower or "\"is_follow_up\": true" in prompt_lower or "is_follow_up: true" in prompt_lower



        # Level-organized question bank (8 questions per level for Levels 1-5)
        level_question_bank = {
            1: [
                {
                    "question_text": "Explain how Subword Tokenization (BPE/WordPiece) handles Out-Of-Vocabulary (OOV) tokens compared to character-level tokenization in Large Language Models.",
                    "topic": "day1_tokenization",
                    "intent": "Evaluate foundational understanding of LLM subword tokenization techniques.",
                    "expected_concepts": ["Subword vocabulary", "BPE merging", "OOV fallback", "Token sequence length"]
                },
                {
                    "question_text": "Why do non-English scripts and code snippets consume significantly more tokens than standard English text in BPE tokenizers like tiktoken?",
                    "topic": "day1_tokenization",
                    "intent": "Assess candidate understanding of byte-level encoding and token efficiency.",
                    "expected_concepts": ["Byte pair encoding", "UTF-8 byte fallback", "Token amplification", "Context window impact"]
                },
                {
                    "question_text": "What happens when an input prompt exceeds an LLM's maximum context window limit (e.g., 8k tokens)? How do you prevent context truncation errors in production?",
                    "topic": "day1_tokenization",
                    "intent": "Evaluate practical handling of context window boundaries and token counting.",
                    "expected_concepts": ["Token counting pre-validation", "Tiktoken estimation", "Sliding window truncation", "Context overflow handling"]
                },
                {
                    "question_text": "How do temperature, top_p, and top_k sampling parameters differ in controlling LLM response randomness and token probability distribution?",
                    "topic": "day1_api_calling",
                    "intent": "Evaluate understanding of LLM generation parameters.",
                    "expected_concepts": ["Probability distribution", "Nucleus sampling", "Temperature scaling", "Determinism"]
                },
                {
                    "question_text": "When building production AI applications, how do you handle API rate limits (HTTP 429), timeouts, and transient provider outages reliably?",
                    "topic": "day1_api_calling",
                    "intent": "Evaluate production error handling, exponential backoff, and provider fallbacks.",
                    "expected_concepts": ["Exponential backoff with jitter", "Circuit breakers", "Provider failover", "Rate limit budget"]
                },
                {
                    "question_text": "How does system prompt design influence LLM persona, instruction following, and guardrail compliance compared to user prompts?",
                    "topic": "day1_api_calling",
                    "intent": "Assess understanding of prompt role separation and instruction adherence.",
                    "expected_concepts": ["System vs User role", "Instruction hierarchy", "Persona framing", "Prompt injection resilience"]
                },
                {
                    "question_text": "Explain the core concept of dense vector embeddings and how text is mapped into a continuous high-dimensional latent space.",
                    "topic": "day6_vector_embeddings",
                    "intent": "Evaluate understanding of vector spaces and semantic representations.",
                    "expected_concepts": ["Latent space", "Dense vectors", "Semantic proximity", "Embedding dimensions"]
                },
                {
                    "question_text": "Compare Cosine Similarity and Euclidean Distance (L2 norm) when measuring semantic similarity between text embeddings.",
                    "topic": "day6_vector_embeddings",
                    "intent": "Assess mathematical understanding of vector distance metrics.",
                    "expected_concepts": ["Normalized vectors", "Angle vs distance", "Magnitude invariance", "Inner product equivalence"]
                }
            ],
            2: [
                {
                    "question_text": "How do Pydantic schemas and JSON Mode guarantee deterministic structured outputs from non-deterministic LLMs?",
                    "topic": "day2_structured_outputs",
                    "intent": "Assess knowledge of structured output enforcement.",
                    "expected_concepts": ["JSON Schema constraint", "Pydantic validation", "Grammar-guided decoding", "Structured parsing"]
                },
                {
                    "question_text": "Describe the architecture of a self-correcting validation loop when an LLM returns invalid JSON or fails Pydantic field constraints.",
                    "topic": "day2_structured_outputs",
                    "intent": "Evaluate self-correction and validation retry patterns.",
                    "expected_concepts": ["Validation error injection", "Auto-retry prompt feedback", "Max attempt boundaries", "Schema repair"]
                },
                {
                    "question_text": "Walk through the full interaction sequence between a user prompt, LLM function call request, client tool execution, and final response generation.",
                    "topic": "day2_function_calling",
                    "intent": "Assess candidate's multi-step tool invocation mechanics.",
                    "expected_concepts": ["Tool definition schema", "Tool call arguments parsing", "Tool response message insertion", "Final generation synthesis"]
                },
                {
                    "question_text": "How do you prevent security risks like command injection or unauthorized API calls when allowing an LLM to invoke backend tools?",
                    "topic": "day2_function_calling",
                    "intent": "Assess understanding of tool sandboxing and argument validation.",
                    "expected_concepts": ["Argument sanitization", "Allowed function whitelisting", "Role-based access control", "Execution sandboxing"]
                },
                {
                    "question_text": "Explain how semantic document chunking differs from fixed-size chunking in RAG pipelines, and what trade-offs exist regarding context coherence.",
                    "topic": "day7_chunking",
                    "intent": "Evaluate candidate's understanding of document processing strategies for RAG.",
                    "expected_concepts": ["Semantic boundaries", "Chunk overlap", "Token limits", "Context fragmentation"]
                },
                {
                    "question_text": "How does setting a large chunk size (e.g., 2000 tokens) vs a small chunk size (e.g., 200 tokens) impact vector search precision and LLM generation quality?",
                    "topic": "day7_chunking",
                    "intent": "Evaluate chunk sizing trade-offs in retrieval pipelines.",
                    "expected_concepts": ["Retrieval precision", "Context dilution", "Token budget", "Sub-document granularity"]
                },
                {
                    "question_text": "How does reducing embedding dimensions (e.g. 1536 to 384) impact retrieval latency, memory usage, and vector similarity recall?",
                    "topic": "day6_vector_embeddings",
                    "intent": "Assess trade-offs in vector dimension reduction.",
                    "expected_concepts": ["Dimensionality reduction", "Memory footprint", "Recall accuracy", "Latency improvement"]
                },
                {
                    "question_text": "What is Matryoshka Representation Learning in modern embedding models, and how does it enable flexible vector truncation?",
                    "topic": "day6_vector_embeddings",
                    "intent": "Evaluate understanding of modern elastic embedding architectures.",
                    "expected_concepts": ["Matryoshka embeddings", "Nested vector representation", "Elastic truncation", "Storage trade-offs"]
                }
            ],
            3: [
                {
                    "question_text": "Compare HNSW (Hierarchical Navigable Small World) graph indexing with IVF (Inverted File Index) in vector databases regarding search latency, recall accuracy, and RAM usage.",
                    "topic": "day8_vector_databases",
                    "intent": "Evaluate understanding of vector index algorithms and resource trade-offs.",
                    "expected_concepts": ["HNSW graph search", "IVF centroids & clusters", "Recall vs QPS trade-off", "RAM footprint"]
                },
                {
                    "question_text": "How does pre-filtering differ from post-filtering when executing vector search with metadata filters in systems like Pinecone or FAISS?",
                    "topic": "day8_vector_databases",
                    "intent": "Assess understanding of metadata filtered ANN queries.",
                    "expected_concepts": ["Single-stage indexing", "Pre-filtering overhead", "Post-filtering recall drop", "Payload filtering"]
                },
                {
                    "question_text": "How do you execute real-time vector deletions and metadata updates in an HNSW graph index without degrading search performance?",
                    "topic": "day8_vector_databases",
                    "intent": "Evaluate dynamic vector index maintenance techniques.",
                    "expected_concepts": ["Tombstone deletion", "Graph repair", "Incremental re-indexing", "Memory fragmentation"]
                },
                {
                    "question_text": "Walk through an Advanced RAG pipeline incorporating Query Rewriting, Hybrid Search (BM25 + Dense Vectors), and Cross-Encoder Reranking.",
                    "topic": "day9_rag_pipelines",
                    "intent": "Evaluate end-to-end advanced RAG pipeline architecture.",
                    "expected_concepts": ["Lexical + Semantic hybrid search", "Reciprocal Rank Fusion (RRF)", "Cross-encoder reranker", "Context assembly"]
                },
                {
                    "question_text": "What is the 'Lost in the Middle' phenomenon in LLM context windows, and how can context compression or reranking mitigate it?",
                    "topic": "day9_rag_pipelines",
                    "intent": "Assess understanding of LLM context window attention bias.",
                    "expected_concepts": ["U-shaped attention curve", "Context positioning", "Key-value cache bias", "Reranker chunk ordering"]
                },
                {
                    "question_text": "How does Reciprocal Rank Fusion (RRF) mathematically combine sparse BM25 keyword ranks with dense vector similarity ranks in hybrid retrieval?",
                    "topic": "day9_rag_pipelines",
                    "intent": "Assess understanding of rank fusion algorithms.",
                    "expected_concepts": ["RRF score formula", "Rank-based normalization", "BM25 score scaling", "Hybrid search synergy"]
                },
                {
                    "question_text": "When chunking code repositories or markdown documentation, what boundary splitting techniques prevent breaking syntax across chunk boundaries?",
                    "topic": "day7_chunking",
                    "intent": "Evaluate structure-aware document processing techniques.",
                    "expected_concepts": ["AST parsing", "Markdown header splitting", "Code block isolation", "Syntax boundary awareness"]
                },
                {
                    "question_text": "In HNSW vector indexing, how do `ef_construction` and `M` parameters control the trade-off between index build time and query throughput?",
                    "topic": "day8_vector_databases",
                    "intent": "Assess practical parameter tuning knowledge for vector databases.",
                    "expected_concepts": ["ef_construction search depth", "M connection edges", "Index construction time", "Query QPS optimization"]
                }
            ],
            4: [
                {
                    "question_text": "Explain stateful multi-step agent architecture using LangGraph. How do state schemas, node functions, and conditional routing edges control agent execution?",
                    "topic": "day13_agent_basics",
                    "intent": "Evaluate mastery of graph-based agent state machines.",
                    "expected_concepts": ["State Graph schema", "Immutable state transitions", "Conditional edge routing", "Cyclic loops"]
                },
                {
                    "question_text": "How do human-in-the-loop interrupts and state checkpoints function within a production LangGraph agent graph?",
                    "topic": "day13_agent_basics",
                    "intent": "Assess human-in-the-loop and persistence knowledge in LangGraph.",
                    "expected_concepts": ["State persistence checkpointers", "Interrupt before/after nodes", "Resume state payload", "Approval workflows"]
                },
                {
                    "question_text": "Compare short-term conversation message history memory with long-term entity/summary memory in autonomous AI agents.",
                    "topic": "day14_agent_memory",
                    "intent": "Evaluate agent memory state management strategies.",
                    "expected_concepts": ["Sliding window buffer", "Incremental summarization", "Entity extraction store", "Token budget preservation"]
                },
                {
                    "question_text": "How do you balance sliding-window context compression with preserving critical facts in multi-turn conversation memory over extended user sessions?",
                    "topic": "day14_agent_memory",
                    "intent": "Evaluate long-term context retention strategies.",
                    "expected_concepts": ["Sliding window summarization", "Fact extraction graph", "Memory decay mitigation", "Token overhead"]
                },
                {
                    "question_text": "Explain the key metrics used in RAGAS evaluation framework: Faithfulness, Answer Relevance, Context Precision, and Context Recall.",
                    "topic": "day21_rag_evaluation",
                    "intent": "Assess understanding of automated RAG quality benchmarking.",
                    "expected_concepts": ["Faithfulness ground truth check", "Context Precision ranking", "Context Recall completeness", "LLM-as-a-Judge rubrics"]
                },
                {
                    "question_text": "How do you design an automated LLM-as-a-Judge evaluation workflow while preventing positional bias and self-enhancement bias?",
                    "topic": "day21_rag_evaluation",
                    "intent": "Evaluate LLM evaluation pipeline calibration and bias mitigation.",
                    "expected_concepts": ["Positional bias swapping", "Self-enhancement bias mitigation", "Structured evaluation rubrics", "Consensus scoring"]
                },
                {
                    "question_text": "How do state persistence checkpointers enable seamless pause, review, and resumption of long-running agent workflows across server restarts?",
                    "topic": "day13_agent_basics",
                    "intent": "Assess persistent state architecture in stateful agent framework design.",
                    "expected_concepts": ["Thread ID checkpointing", "DB state serialization", "Thread state replay", "Interrupt resumption"]
                },
                {
                    "question_text": "How do you generate synthetic evaluation datasets (testsets) to benchmark RAG system performance across complex user queries?",
                    "topic": "day21_rag_evaluation",
                    "intent": "Assess synthetic data generation for RAG benchmarking.",
                    "expected_concepts": ["Synthetic query generation", "Evolutionary prompting", "Ground truth verification", "Testset diversity"]
                }
            ],
            5: [
                {
                    "question_text": "What is Prompt Injection (Direct vs Indirect)? How do XML tag delimiters, system prompt constraints, and input guardrails prevent prompt hijacking?",
                    "topic": "day26_production_guardrails",
                    "intent": "Evaluate security posture and prompt injection defenses.",
                    "expected_concepts": ["Indirect prompt injection", "Delimiter isolation (<user_input>)", "NeMo/Llama Guard sanitization", "Output validation"]
                },
                {
                    "question_text": "How do output guardrails like NeMo Guardrails or Llama Guard verify that generated text does not leak system instructions, internal keys, or PII?",
                    "topic": "day26_production_guardrails",
                    "intent": "Evaluate output validation and leakage prevention mechanisms.",
                    "expected_concepts": ["Secret leak detection", "PII redaction", "Llama Guard classification", "Real-time stream filtering"]
                },
                {
                    "question_text": "Describe the architecture of serving LLMs at high throughput using continuous batching and PagedAttention in engines like vLLM.",
                    "topic": "day26_production_guardrails",
                    "intent": "Evaluate production LLM inference acceleration and memory management.",
                    "expected_concepts": ["Continuous batching", "PagedAttention KV cache", "VRAM fragmentation reduction", "Throughput scaling"]
                },
                {
                    "question_text": "How do speculative decoding and prompt caching reduce time-to-first-token (TTFT) and inference latency in production AI microservices?",
                    "topic": "day26_production_guardrails",
                    "intent": "Assess latency optimization techniques for real-time AI backends.",
                    "expected_concepts": ["Draft model speculative decoding", "KV prompt caching", "TTFT reduction", "Token generation throughput"]
                },
                {
                    "question_text": "How do you design a resilient multi-provider LLM gateway that routes requests dynamically between OpenAI, Gemini, and local open-weight models based on latency and cost?",
                    "topic": "day26_production_guardrails",
                    "intent": "Evaluate multi-cloud LLM gateway design and fallback routing.",
                    "expected_concepts": ["Dynamic fallback routing", "Circuit breaker pattern", "Provider health checks", "Latency-cost optimization"]
                },
                {
                    "question_text": "How do you defend against data exfiltration attacks where an attacker injects malicious instructions inside retrieved RAG document chunks to trigger unauthorized tool calls?",
                    "topic": "day26_production_guardrails",
                    "intent": "Assess defense against RAG data exfiltration and indirect injection.",
                    "expected_concepts": ["Retrieved chunk sanitization", "Tool execution policy", "Untrusted data markup", "Sandboxed tool evaluation"]
                },
                {
                    "question_text": "How do you implement distributed tracing (OpenTelemetry/LangSmith) and token cost tracking across multi-tenant production AI applications?",
                    "topic": "day26_production_guardrails",
                    "intent": "Assess production observability, telemetry, and cost attribution.",
                    "expected_concepts": ["Span tracing", "Token usage telemetry", "Tenant cost allocation", "Latency bottleneck isolation"]
                },
                {
                    "question_text": "What strategies do you employ for model version migration and handling silent API behavior changes in mission-critical LLM pipelines?",
                    "topic": "day26_production_guardrails",
                    "intent": "Assess regression testing and lifecycle management in production LLM pipelines.",
                    "expected_concepts": ["Shadow deployment", "Regression test suite", "Model drift monitoring", "Prompt versioning"]
                }
            ]
        }

        # Follow-up pool with 20 distinct senior-level follow-ups
        followup_pool = [
            {
                "question_text": "You explained subword tokenization mechanisms well. How does byte-level BPE fallback prevent OOV errors when processing code or non-English text?",
                "topic": "day1_tokenization",
                "difficulty": current_difficulty
            },
            {
                "question_text": "You covered sampling parameters. If a production pipeline requires strictly deterministic JSON responses, what sampling parameters and seed options would you configure?",
                "topic": "day2_structured_outputs",
                "difficulty": current_difficulty
            },
            {
                "question_text": "In your answer on tool calling, how would you handle a situation where the model returns invalid function arguments or non-existent parameter names?",
                "topic": "day2_function_calling",
                "difficulty": current_difficulty
            },
            {
                "question_text": "You compared Cosine Similarity and L2 distance. If all vectors are normalized to unit length (L2 norm = 1), how does Cosine Similarity mathematically relate to Dot Product?",
                "topic": "day6_vector_embeddings",
                "difficulty": current_difficulty
            },
            {
                "question_text": "In high-dimensional embedding spaces, how does approximate nearest neighbor (ANN) search trade off recall accuracy against query throughput compared to exact KNN search?",
                "topic": "day6_vector_embeddings",
                "difficulty": current_difficulty
            },
            {
                "question_text": "You mentioned vector search precision. How do dimensionality reduction techniques like PCA or Matryoshka embeddings impact vector recall and storage memory?",
                "topic": "day6_vector_embeddings",
                "difficulty": current_difficulty
            },


            {
                "question_text": "You explained chunking with overlap. How does increasing overlap from 10% to 50% affect retrieval precision, context duplication, and vector DB storage overhead?",
                "topic": "day7_chunking",
                "difficulty": current_difficulty
            },
            {
                "question_text": "In your explanation of HNSW graphs, how do `ef_construction` and `M` parameters affect index build time versus query throughput?",
                "topic": "day8_vector_databases",
                "difficulty": current_difficulty
            },
            {
                "question_text": "You described LangGraph state graphs. How do you implement fallback nodes or retry loops when a tool node raises an exception?",
                "topic": "day13_agent_basics",
                "difficulty": current_difficulty
            },
            {
                "question_text": "How do you calculate Faithfulness metric in RAGAS using an LLM evaluator without introducing model bias?",
                "topic": "day21_rag_evaluation",
                "difficulty": current_difficulty
            },
            {
                "question_text": "When deploying Llama Guard or NeMo output guardrails, how do you minimize added latency on streaming token responses?",
                "topic": "day26_production_guardrails",
                "difficulty": current_difficulty
            },
            {
                "question_text": "In high-throughput vLLM serving, how does PagedAttention eliminate KV cache memory fragmentation compared to contiguous memory allocation?",
                "topic": "day26_production_guardrails",
                "difficulty": current_difficulty
            },
            {
                "question_text": "How do you handle schema validation for deeply nested JSON structures when LLM output token limits are tightly constrained?",
                "topic": "day2_structured_outputs",
                "difficulty": current_difficulty
            },
            {
                "question_text": "When executing parallel tool calls returned by an LLM, how do you handle partial failures where one tool succeeds and another throws a backend error?",
                "topic": "day2_function_calling",
                "difficulty": current_difficulty
            },
            {
                "question_text": "Why can't Cross-Encoder rerankers be used as the primary search algorithm for millions of documents instead of bi-encoder vector search?",
                "topic": "day9_rag_pipelines",
                "difficulty": current_difficulty
            },
            {
                "question_text": "In hybrid search combining BM25 and dense vectors, how do you handle out-of-vocabulary technical jargon that standard dense models fail to capture?",
                "topic": "day9_rag_pipelines",
                "difficulty": current_difficulty
            },
            {
                "question_text": "How do persistent checkpoints in LangGraph allow human operators to review and modify state before an agent executes a high-risk tool call?",
                "topic": "day13_agent_basics",
                "difficulty": current_difficulty
            },
            {
                "question_text": "How do you mitigate context window 'Lost in the Middle' degradation when stuffing multiple long document chunks into an LLM prompt?",
                "topic": "day9_rag_pipelines",
                "difficulty": current_difficulty
            },
            {
                "question_text": "What diagnostic steps do you take when RAGAS Context Precision is high (90%+) but Answer Relevance remains low (<60%)?",
                "topic": "day21_rag_evaluation",
                "difficulty": current_difficulty
            },
            {
                "question_text": "How do you prevent indirect prompt injection attacks where an attacker embeds malicious instructions inside retrieved PDF document chunks?",
                "topic": "day26_production_guardrails",
                "difficulty": current_difficulty
            },
            {
                "question_text": "How do speculative decoding draft models achieve 2-3x speedups without degrading original LLM output quality?",
                "topic": "day1_tokenization",
                "difficulty": current_difficulty
            }
        ]

        # Alphanumeric set for zero-tolerance duplicate check
        asked_normalized = set(normalize_question_text(q) for q in asked_questions if q.strip())

        if is_follow_up:
            topic_followups = [f for f in followup_pool if f.get("topic") == detected_topic]
            concept_target = ""
            if "followup request target concept:" in prompt_lower:
                concept_target = prompt_lower.split("followup request target concept:")[1].split("###")[0].strip().lower()
            
            if concept_target:
                concept_words = [w for w in "".join(c if c.isalnum() else " " for c in concept_target).split() if len(w) > 3 and w not in {"operational", "mechanics", "system", "design", "core", "search", "precision", "recall"} and not w.startswith("day")]
                concept_matched = [f for f in topic_followups if any(w in f["question_text"].lower() for w in concept_words)]
                if concept_matched:
                    topic_followups = concept_matched


            unasked_followups = [f for f in topic_followups if not is_substantially_similar(f["question_text"], asked_questions)]


            if unasked_followups:
                selected_f = random.choice(unasked_followups)
            else:
                fallback_followups = [
                    f"Based on your explanation of {detected_topic}, what specific operational trade-offs and edge cases affect retrieval precision under production load at Level {current_difficulty}?",
                    f"How would you debug a production degradation or accuracy issue specifically within {detected_topic} implementations at Level {current_difficulty}?",
                    f"What architectural changes or guardrails would you introduce to scale {detected_topic} under high-concurrency Level {current_difficulty} workloads?",
                    f"Comparing {detected_topic} with alternative technical approaches, what are the primary engineering trade-offs at Level {current_difficulty}?"
                ]
                chosen_f_text = fallback_followups[0]
                for ff in fallback_followups:
                    if not is_substantially_similar(ff, asked_questions):
                        chosen_f_text = ff
                        break
                selected_f = {
                    "question_text": chosen_f_text,
                    "topic": detected_topic,
                    "difficulty": current_difficulty
                }

            return {
                "question_text": selected_f["question_text"],
                "curriculum_day": topic_day_map.get(detected_topic, 1),
                "topic": detected_topic,
                "difficulty": current_difficulty,
                "question_type": "Follow-up",
                "intent": f"Follow up on candidate's understanding of {detected_topic} at Level {current_difficulty}.",
                "expected_concepts": ["Trade-off analysis", "Practical implementation", "Production resilience"],
                "is_follow_up": True
            }

        # Priority 1: Match target_topic across ALL difficulty levels AND unasked
        matching_topic_unasked = []
        for lvl, q_list in level_question_bank.items():
            for q in q_list:
                if q.get("topic") == detected_topic and not is_substantially_similar(q["question_text"], asked_questions):
                    matching_topic_unasked.append(q)

        # Priority 2: Match any topic in same domain (e.g. vector/embeddings/chunking/rag)
        domain_unasked = []
        if not matching_topic_unasked:
            for lvl, q_list in level_question_bank.items():
                for q in q_list:
                    q_t = q.get("topic", "")
                    if ("vector" in detected_topic and "vector" in q_t) or ("chunk" in detected_topic and "chunk" in q_t) or ("token" in detected_topic and "token" in q_t):
                        if not is_substantially_similar(q["question_text"], asked_questions):
                            domain_unasked.append(q)

        # Priority 3: Match ANY unasked question from the entire question bank
        all_unasked = []
        if not matching_topic_unasked and not domain_unasked:
            for lvl, q_list in level_question_bank.items():
                for q in q_list:
                    if not is_substantially_similar(q["question_text"], asked_questions):
                        all_unasked.append(q)

        if matching_topic_unasked:
            selected = random.choice(matching_topic_unasked)
        elif domain_unasked:
            selected = random.choice(domain_unasked)
        elif all_unasked:
            selected = random.choice(all_unasked)
        else:
            fallback_templates = [
                f"In production deployments of {detected_topic}, how do you architect the system to balance latency, memory overhead, and retrieval precision at Level {current_difficulty} load?",
                f"What specific debugging and telemetry strategies would you implement to diagnose failure modes in {detected_topic} at Level {current_difficulty}?",
                f"How do parameter choices and schema configurations for {detected_topic} impact operational performance at Level {current_difficulty}?",
                f"In a high-throughput production scenario involving {detected_topic}, how do you mitigate sudden query latency spikes at Level {current_difficulty}?",
                f"How does the core mechanism of {detected_topic} compare with alternative design patterns regarding long-term maintainability at Level {current_difficulty}?"
            ]
            chosen_text = fallback_templates[0]
            for ft in fallback_templates:
                if not is_substantially_similar(ft, asked_questions):
                    chosen_text = ft
                    break

            selected = {
                "question_text": chosen_text,
                "topic": detected_topic,
                "intent": f"Evaluate advanced concepts and trade-offs of {detected_topic}.",
                "expected_concepts": ["Latency optimization", "Memory management", "Precision trade-offs"]
            }

        q_topic = selected.get("topic", detected_topic)
        return {
            "question_text": selected["question_text"],
            "curriculum_day": topic_day_map.get(q_topic, 1),
            "topic": q_topic,
            "difficulty": current_difficulty,
            "question_type": "Conceptual" if current_difficulty <= 2 else ("Trade-off" if current_difficulty <= 4 else "Architecture"),
            "intent": selected.get("intent", f"Evaluate understanding of {q_topic} at Level {current_difficulty}."),
            "expected_concepts": selected.get("expected_concepts", ["Core concepts", "Trade-offs"]),
            "is_follow_up": is_follow_up
        }


