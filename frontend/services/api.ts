import axios from 'axios';
import { Candidate, CurriculumDay, InterviewSession, FeedbackReport } from '../types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || (typeof window !== 'undefined' ? '/api/v1' : 'http://localhost:8000/api/v1');

const apiClient = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (!error.response && error.message === 'Network Error') {
      error.message = `Backend server is unreachable at ${API_BASE}. Please ensure backend is running.`;
    }
    return Promise.reject(error);
  }
);

export const candidateService = {
  list: async (): Promise<Candidate[]> => {
    const res = await apiClient.get<Candidate[]>('/candidates');
    return res.data;
  },
  getById: async (id: string): Promise<Candidate> => {
    const res = await apiClient.get<Candidate>(`/candidates/${id}`);
    return res.data;
  },
  create: async (data: {
    name: string;
    email?: string;
    target_role?: string;
    experience_level?: string;
    years_of_experience?: number;
    primary_skills?: string[];
    resume_summary?: string;
  }): Promise<Candidate> => {
    const res = await apiClient.post<Candidate>('/candidates', data);
    return res.data;
  },
  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/candidates/${id}`);
  },
};


export const curriculumService = {
  getDays: async (): Promise<CurriculumDay[]> => {
    const res = await apiClient.get<CurriculumDay[]>('/curriculum');
    return res.data;
  },
};

export const interviewService = {
  start: async (candidateId: string): Promise<InterviewSession> => {
    const res = await apiClient.post<InterviewSession>('/interviews/start', {
      candidate_id: candidateId,
    });
    return res.data;
  },
  getSession: async (sessionId: string): Promise<InterviewSession> => {
    const res = await apiClient.get<InterviewSession>(`/interviews/${sessionId}`);
    return res.data;
  },
  submitAnswer: async (sessionId: string, answerText: string): Promise<InterviewSession> => {
    const res = await apiClient.post<InterviewSession>(`/interviews/${sessionId}/answers`, {
      answer_text: answerText,
    });
    return res.data;
  },
};

export const feedbackService = {
  getBySessionId: async (sessionId: string): Promise<FeedbackReport> => {
    const res = await apiClient.get<FeedbackReport>(`/feedback/${sessionId}`);
    return res.data;
  },
};
