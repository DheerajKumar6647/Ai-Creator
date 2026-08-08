export interface Candidate {
  id: string;
  name: string;
  email?: string;
  target_role?: string;
  experience_level?: string;
  years_of_experience?: number;
  primary_skills?: string[];
  resume_summary?: string;
  completed_days: number[];
  skipped_days: number[];
  attempts: number;
  completion_percentage: number;
  learning_signals: {
    average_score?: number;
    strong_topics?: string[];
    weak_topics?: string[];
    likely_knowledge_gaps?: string[];
    preferred_difficulty?: number;
    communication_skill?: string;
    engineering_maturity?: string;
  };
}


export interface CurriculumTopic {
  topic_id: string;
  day_number: number;
  name: string;
  description: string;
  learning_objectives: string[];
  prerequisites: string[];
  tools_used: string[];
  difficulty: number;
}

export interface CurriculumDay {
  day_number: number;
  title: string;
  description: string;
  tools: string[];
  difficulty: number;
  topics: CurriculumTopic[];
}

export interface Question {
  question_id: string;
  session_id: string;
  curriculum_day: number;
  topic: string;
  difficulty: number;
  question_text: string;
  question_type: string;
  intent: string;
  expected_concepts: string[];
  is_follow_up?: boolean;
}

export interface Evaluation {
  evaluation_id: string;
  question_id: string;
  technical_accuracy: number;
  conceptual_understanding: number;
  knowledge_depth: number;
  reasoning_quality: number;
  engineering_thinking: number;
  communication: number;
  confidence: number;
  overall_score: number;
  strengths: string[];
  weaknesses: string[];
  evidence: string;
  recommended_follow_up: boolean;
}

export interface InterviewSession {
  session_id: string;
  candidate_id: string;
  status: 'created' | 'in_progress' | 'completed' | 'failed' | 'terminated_by_candidate';
  termination_requested?: boolean;
  termination_reason?: string;
  started_at: string;
  completed_at?: string;
  current_question_index: number;
  questions_answered: number;
  difficulty_level: number;
  coverage_percentage: number;
  overall_score: number;
  technical_score: number;
  communication_score: number;
  covered_days: number[];
  covered_topics: string[];
  current_question?: Question;
  last_evaluation?: Evaluation;
  final_feedback?: FeedbackReport;
}

export interface FeedbackReport {
  feedback_id: string;
  session_id: string;
  overall_rating: number;
  technical_summary: string;
  communication_summary: string;
  engineering_thinking_summary: string;
  overall_readiness: string;
  hiring_recommendation: 'STRONG_HIRE' | 'HIRE' | 'LEAN_HIRE' | 'BORDERLINE' | 'NEEDS_IMPROVEMENT' | 'NOT_READY';
  recommendation_confidence: number;
  recommendation_reasoning: string;
  scores: Record<string, number>;
  strengths: string[];
  weaknesses: string[];
  misconception_report: Array<{
    misconception: string;
    correct_concept: string;
    impact: string;
    suggested_practice: string;
  }>;
  topic_breakdown: Array<{
    topic_name: string;
    score: number;
    level: string;
  }>;
  learning_roadmap: Array<{
    priority: number;
    topic: string;
    action: string;
  }>;
}
