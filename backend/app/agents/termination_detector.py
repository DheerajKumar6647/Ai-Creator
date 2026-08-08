import re
import json
from typing import Dict, Any, Optional
from app.utils.logger import logger
from app.services.llm_provider import LLMProvider

def detect_termination_intent_heuristic(answer_text: str, question_text: str = "") -> Dict[str, Any]:
    text = (answer_text or "").strip().lower()
    q_text = (question_text or "").strip().lower()
    
    if not text:
        return {
            "termination_requested": False,
            "termination_reason": None,
            "confidence": 1.0,
            "explanation": "Empty answer text."
        }

    # --------------------------------------------------------------------------
    # STEP 1: Check Explicit Candidate Interview / Test Withdrawal Patterns
    # Candidate explicitly communicates: "I want to stop participating in this interview/test."
    # --------------------------------------------------------------------------
    explicit_withdrawal_patterns = [
        # Explicit English candidate withdrawal
        r"(don't|dont|do not|can't|cant|cannot)\s+(want|wish|like)\s+to\s+(continue|proceed|do|give|take|participate|answer)",
        r"(want|wish|like|prefer)\s+to\s+(quit|leave|exit|stop|cancel|end|withdraw|discontinue|abort)\s+(the|this|my)?\s*(interview|test|assessment|exam)",
        r"\b(please|kindly)?\s*(stop|end|cancel|terminate|exit|abort)\b\s+(the|this|my)?\s*(interview|test|assessment|exam|session)\b",
        r"done with (this|the)?\s*(interview|test|assessment)",
        r"stop asking (me|questions)",
        r"stop the (interview|test|assessment)",
        r"end (the|my|this) (interview|test|assessment)",
        r"cancel (the|my|this) (interview|test|assessment)",
        r"terminate (the|my|this) (interview|test|assessment)",
        r"quit (the|this) (interview|test|assessment)",
        r"i don't want to continue",
        r"i do not want to continue",
        r"i am done with this interview",
        r"i'm done with this interview",
        r"i am done with the test",
        r"i'm done with the test",
        r"i want to stop the test",
        r"i want to stop the interview",
        r"i want to quit\b",
        r"i want to leave\b",
        r"i want to exit\b",
        r"i would like to withdraw",
        r"would rather not (continue|proceed|answer)",
        r"rather not (continue|proceed|answer)",
        r"refuse to continue",
        r"not interested in taking this test",
        r"changed my mind",
        r"let's stop here",
        r"no more questions",
        r"don't think i want to",
        r"think i'?m done",
        r"call it a day",
        r"(don't|dont|do not)\s+feel\s+like\s+(continuing|proceeding|doing|answering)",
        r"would like to stop",

        # Hinglish & Hindi explicit candidate withdrawal
        r"(mujhe|main|mera)?\s*(interview|test|assessment)?\s*(nahi|nhi|ni)\s*(dena|karna|chahiye|dunga|dungi)",
        r"(interview|test|assessment)\s*(ko|se|ko bhi)?\s*(band|rok|stop|cancel|exit|chhod|chod)\s*(kar|kardo|kar do|kar dijiye|dijiye|do)?",
        r"continue (nahi|nhi|ni)\s*(karna|chahta|chahti)",
        r"aur (questions|question|sawaal|sawal) (nahi|nhi|ni)",
        r"interview yahin stop",
        r"test band kar",
        r"(nhi|nahi|ni)\s+dena\b",
        r"mana kar",
        r"chhodna chahta",
        r"aur answer nahi karne",
        r"khata?m kar",
        r"नहीं देना",
        r"जारी नहीं",
        r"इंटरव्यू बंद",
        r"टेस्ट बंद",
        r"टेस्ट (रोक|बंद)",
        r"छोड़ना चाहता",
        r"जवाब नहीं देना",
        r"खत्म कर"
    ]

    is_explicit_withdrawal = False
    matched_withdrawal_pat = None
    for pat in explicit_withdrawal_patterns:
        if re.search(pat, text):
            is_explicit_withdrawal = True
            matched_withdrawal_pat = pat
            break

    # --------------------------------------------------------------------------
    # STEP 2: Check Technical Non-Termination Contexts (Negative Safety Filter)
    # If the message describes a SYSTEM, AGENT, NODE, GRAPH, LOOP, REQUEST, PROCESS,
    # EXECUTION, ROUTING, WORKFLOW, or END STATE, return False unless there is ALSO
    # explicit personal candidate withdrawal intent regarding the INTERVIEW / TEST.
    # --------------------------------------------------------------------------
    technical_stop_patterns = [
        r"whether to stop",
        r"stop \((end|exit|terminate)\)",
        r"stop \(end\)",
        r"stop at (end|exit)",
        r"(node|graph|agent|workflow|state|execution|process|routing|condition|loop|server|system|request|task|job|function)\s+.*(stop|end|terminate|exit)",
        r"(stop|end|terminate|exit)\s+.*(when|if|where)\s+(the|a)?\s*(node|graph|agent|workflow|state|condition|end|execution|process|loop|server|request|system|task|job|function)",
        r"reaches (end|exit)",
        r"terminates (when|if|execution|process)",
        r"stop condition",
        r"termination condition",
        r"stop hallucinations",
        r"stop hallucinating",
        r"stop an infinite",
        r"stop the graph",
        r"stop the loop",
        r"stop execution",
        r"terminate a failed request",
        r"terminate failed request",
        r"process stops",
        r"until the process stops",
        r"how (do|can|to|we|you) (stop|quit|exit|cancel|terminate|kill)",
        r"why (does|did|is) (the|a|system|server|loop|token|generation|model) (stop|quit|exit|cancel)",
        r"stop (generating|hallucinating|hallucinations|retry|retrying|loop|looping|process|container|tokens|server|responding|execution|stream)",
        r"stopped (responding|generating|working|running|processing|serving)",
        r"infinite (retry )?loop",
        r"retry loop",
        r"kill (the )?process",
        r"cancel (a )?task",
        r"exit (code|status)",
        r"graceful (shutdown|exit|termination)"
    ]

    has_technical_stop_pattern = any(re.search(pat, text) for pat in technical_stop_patterns)

    # Broad technical context keywords check
    tech_context_words = {
        "node", "nodes", "graph", "agent", "workflow", "state", "execution", 
        "process", "routing", "condition", "loop", "server", "request", "requests", 
        "hallucination", "hallucinations", "end", "end)", "schema", "architecture", 
        "bpe", "hnsw", "rag", "vector", "token", "tokens", "pydantic", "json", 
        "python", "function", "functions", "validation", "endpoint", "pipeline"
    }
    has_tech_context = any(w in text for w in tech_context_words)

    # If the answer contains technical stopping concepts or technical context and does NOT
    # explicitly express personal candidate withdrawal from the interview/test, DO NOT TERMINATE.
    if (has_technical_stop_pattern or has_tech_context) and not is_explicit_withdrawal:
        return {
            "termination_requested": False,
            "termination_reason": None,
            "confidence": 1.0,
            "explanation": "Technical concept usage detected describing a system, node, workflow, or process."
        }

    # --------------------------------------------------------------------------
    # STEP 3: Return Positive Result if Explicit Personal Withdrawal Matched
    # --------------------------------------------------------------------------
    if is_explicit_withdrawal:
        logger.info(f"Candidate withdrawal intent detected via pattern match: '{matched_withdrawal_pat}' in text: '{answer_text}'")
        return {
            "termination_requested": True,
            "termination_reason": "candidate_withdrawal",
            "confidence": 0.99,
            "explanation": f"Matched explicit withdrawal pattern: {matched_withdrawal_pat}"
        }

    # --------------------------------------------------------------------------
    # STEP 4: Check Technical Struggle / Uncertainty (Negative Filter)
    # Expressing lack of knowledge, confusion, or difficulty WITHOUT withdrawal intent.
    # --------------------------------------------------------------------------
    struggle_patterns = [
        r"^(i )?(don't|dont|do not|can't|cant|cannot) know",
        r"^(i'm|im|i am) not sure",
        r"^(i )?don't know how",
        r"^(i )?don't know this",
        r"^idk$",
        r"^no idea$",
        r"i forgot",
        r"this (question )?is (difficult|hard|tough|confusing)",
        r"can you repeat",
        r"i need (some )?time",
        r"i am confused",
        r"i don't understand"
    ]

    for pat in struggle_patterns:
        if re.search(pat, text):
            return {
                "termination_requested": False,
                "termination_reason": None,
                "confidence": 0.95,
                "explanation": "Technical struggle or uncertainty detected without withdrawal intent."
            }

    # If trigger words exist but no pattern matched, use lower confidence to allow LLM evaluation
    trigger_words = ["stop", "quit", "leave", "exit", "cancel", "end", "terminate", "dena", "continue", "karna", "chahiye", "band", "rok", "withdraw"]
    if any(w in text for w in trigger_words):
        return {
            "termination_requested": False,
            "termination_reason": None,
            "confidence": 0.70,
            "explanation": "Ambiguous stop keyword detected without explicit candidate withdrawal pattern."
        }

    return {
        "termination_requested": False,
        "termination_reason": None,
        "confidence": 0.95,
        "explanation": "No explicit candidate termination intent detected by heuristics."
    }


async def detect_termination_intent(answer_text: str, question_text: str = "") -> Dict[str, Any]:
    """
    Main entry point for candidate termination intent detection.
    Combines rule-based heuristics with LLM provider evaluation when needed.
    """
    heuristic_res = detect_termination_intent_heuristic(answer_text, question_text)
    
    # If heuristic result is high confidence (>= 0.85), return immediately
    if heuristic_res["confidence"] >= 0.85:
        return heuristic_res

    # For edge cases or ambiguous phrasing, consult LLM if available
    llm = LLMProvider()
    if getattr(llm, "provider_type", "mock") != "mock":
        try:
            prompt = f"""
System Role: You are a strict intent classifier for an AI technical interview engine.
Your task is to determine whether the candidate wants to TERMINATE / QUIT / CANCEL / STOP their interview session.

CRITICAL INSTRUCTIONS:
- Return JSON with:
  "termination_requested": boolean,
  "termination_reason": "candidate_withdrawal" or null,
  "explanation": "short reason"

RULES:
1. Candidate Withdrawal (termination_requested = true):
   - Candidate states in ANY language (English, Hindi, Hinglish, indirect, polite) that they explicitly want to stop, quit, exit, cancel, leave, or not continue participating in the interview/test/assessment.
   - Examples: "I don't want to give this test", "Mujhe test nahi dena", "I want to quit", "Please stop the interview", "I am done with the test", "I want to leave", "Mujhe continue nahi karna".

2. Technical Concepts & Workflow Termination Conditions (termination_requested = false):
   - Candidate is discussing technical stopping concepts, state machine nodes, graph routing, process execution, or workflow control:
     "Conditional routing edges decide whether to stop (END)", "Node terminates execution when END is reached", "How do we stop an infinite loop?", "How can we stop hallucinations?", "Why does token generation stop?", "The server stopped responding", "The process terminates on failure".
   - CRITICAL: References to stopping, ending, or terminating INSIDE technical answers (e.g. stopping loops, ending nodes, agent END states) MUST NEVER terminate the interview.

Current Question: "{question_text}"
Candidate Response: "{answer_text}"
"""
            llm_res = await llm.generate_json(prompt, temperature=0.0)
            if isinstance(llm_res, dict) and "termination_requested" in llm_res:
                term_req = bool(llm_res["termination_requested"])
                return {
                    "termination_requested": term_req,
                    "termination_reason": "candidate_withdrawal" if term_req else None,
                    "confidence": 0.95,
                    "explanation": llm_res.get("explanation", "LLM semantic intent detection")
                }
        except Exception as err:
            logger.warning(f"LLM termination detection failed fallback to heuristic: {err}")

    return heuristic_res
