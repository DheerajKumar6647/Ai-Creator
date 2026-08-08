import asyncio
import json
from app.services.llm_provider import LLMProvider

async def verify_all_levels():
    provider = LLMProvider(provider_type="mock")
    all_questions_generated = []

    print("=== VERIFYING QUESTIONS ACROSS ALL 5 LEVELS ===")
    
    topics_per_level = {
        1: ["day1_tokenization", "day1_api_calling", "day6_vector_embeddings"],
        2: ["day2_structured_outputs", "day2_function_calling", "day7_chunking"],
        3: ["day8_vector_databases", "day9_rag_pipelines"],
        4: ["day13_agent_basics", "day14_agent_memory", "day21_rag_evaluation"],
        5: ["day26_production_guardrails"]
    }

    total_generated = 0
    duplicates_found = 0

    for level in range(1, 6):
        print(f"\n--- LEVEL {level} QUESTIONS ---")
        level_questions = []
        topics = topics_per_level[level]
        
        for i in range(8):
            topic = topics[i % len(topics)]
            prompt = f"TARGET TOPIC DETAILS: {topic} ### CURRENT DIFFICULTY LEVEL (1-5): {level} ### PREVIOUSLY ASKED QUESTIONS:\n" + "\n".join(all_questions_generated)
            if i % 3 == 2:
                prompt += "\n### FOLLOWUP REQUEST"

            q_data = provider._select_mock_question(prompt.lower())
            q_text = q_data["question_text"]
            
            is_dup = q_text in all_questions_generated
            if is_dup:
                duplicates_found += 1
                status = "[DUPLICATE DETECTED!]"
            else:
                status = "[OK - UNIQUE]"

            all_questions_generated.append(q_text)
            level_questions.append(q_text)
            total_generated += 1

            print(f"L{level} Q{i+1} [{q_data.get('question_type')} - {q_data.get('topic')}]: {q_text[:90]}... {status}")

    print("\n================ VERIFICATION SUMMARY ================")
    print(f"Total Questions Generated: {total_generated}")
    print(f"Total Unique Questions: {len(set(all_questions_generated))}")
    print(f"Duplicates Found: {duplicates_found}")

    assert duplicates_found == 0, f"Found {duplicates_found} duplicates!"
    assert len(set(all_questions_generated)) == total_generated
    print("SUCCESS: All 5 levels verified! 100% unique questions generated across all levels.")

if __name__ == "__main__":
    asyncio.run(verify_all_levels())
