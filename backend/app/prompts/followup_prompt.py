def get_followup_prompt(
    previous_question_text: str,
    candidate_answer_text: str,
    evaluation_json: str,
    history_summary: str,
    asked_questions_json: str = "[]",
    target_topic: str = "",
    target_concept: str = "",
    follow_up_reason: str = ""
) -> str:
    return f"""
You are the Follow-up Intelligence Agent for InterviewAI.
Generate EXACTLY ONE targeted follow-up question based on the candidate's response.

### TARGET TOPIC & CONCEPT:
- Topic: {target_topic}
- Target Concept: {target_concept}
- Follow-up Reason: {follow_up_reason}

### PREVIOUS QUESTION:
{previous_question_text}

### CANDIDATE ANSWER:
<candidate_answer>
{candidate_answer_text}
</candidate_answer>

### EVALUATION SUMMARY:
{evaluation_json}

### PREVIOUSLY ASKED QUESTIONS IN THIS SESSION (DO NOT REPEAT):
{asked_questions_json}

### CONVERSATION SUMMARY:
{history_summary}

### INSTRUCTIONS:
- Directly reference specific details mentioned by the candidate in their answer.
- CRITICAL: The follow-up question MUST directly probe target_concept '{target_concept}' within topic '{target_topic}'.
- Challenge assumptions, ask about edge cases, trade-offs, or production architectural implications.
- CRITICAL: Do NOT generate a question that is identical or substantially similar to any question listed in PREVIOUSLY ASKED QUESTIONS.
- NEVER ask generic questions like "Can you elaborate?" or "Anything else?".
- Return ONLY JSON:

{{
  "question_text": "Follow-up question string",
  "curriculum_day": 7,
  "topic": "{target_topic or 'day7_chunking'}",
  "difficulty": 3,
  "question_type": "Trade-off",
  "intent": "Follow-up purpose",
  "expected_concepts": ["concept1"],
  "is_follow_up": true
}}
"""


