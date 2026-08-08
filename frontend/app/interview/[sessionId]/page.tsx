"use client";

import React, { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { AppLayout } from '../../../components/layout/AppLayout';
import { QuestionCard } from '../../../components/interview/QuestionCard';
import { AnswerEditor } from '../../../components/interview/AnswerEditor';
import { ThinkingIndicator } from '../../../components/interview/ThinkingIndicator';
import { interviewService } from '../../../services/api';
import { InterviewSession, Question } from '../../../types';
import { Clock, AlertCircle, RefreshCw, Home, Play, LogOut } from 'lucide-react';

export default function InterviewRoomPage() {
  const router = useRouter();
  const params = useParams();
  const sessionId = params.sessionId as string;

  const [session, setSession] = useState<InterviewSession | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [seconds, setSeconds] = useState(0);

  useEffect(() => {
    setSession(null);
    setError(null);
    setSeconds(0);
    loadSession();
    const interval = setInterval(() => setSeconds((s) => s + 1), 1000);
    return () => clearInterval(interval);
  }, [sessionId]);

  const loadSession = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await interviewService.getSession(sessionId);
      setSession(data);
      if (data.status === 'completed') {
        router.push(`/feedback/${sessionId}`);
      }
    } catch (err: any) {
      console.error('Error loading interview session:', err);
      setError('Unable to generate or load interview question. Please retry.');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitAnswer = async (answerText: string) => {
    try {
      setSubmitting(true);
      setError(null);
      const updatedState = await interviewService.submitAnswer(sessionId, answerText);
      setSession(updatedState);
      if (updatedState.status === 'completed') {
        router.push(`/feedback/${sessionId}`);
      } else if (updatedState.status !== 'terminated_by_candidate') {
        await loadSession();
      }
    } catch (err: any) {
      console.error('Error submitting answer:', err);
      setError('Error submitting answer: ' + (err.response?.data?.detail || err.message));
    } finally {
      setSubmitting(false);
    }
  };

  const handleStartNewInterview = async () => {
    if (!session?.candidate_id) {
      router.push('/dashboard');
      return;
    }
    try {
      setLoading(true);
      setError(null);
      const newSession = await interviewService.start(session.candidate_id);
      router.push(`/interview/${newSession.session_id}`);
    } catch (err: any) {
      console.error('Error starting new interview session:', err);
      setError('Failed to start new interview session. Please retry.');
      setLoading(false);
    }
  };

  const formatTimer = (totalSeconds: number) => {
    const mins = Math.floor(totalSeconds / 60);
    const secs = totalSeconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  if (loading && !session) {
    return (
      <AppLayout>
        <div className="max-w-4xl mx-auto py-12 space-y-6">
          <div className="glass-card rounded-2xl p-8 text-center space-y-4">
            <RefreshCw className="w-8 h-8 text-blue-400 animate-spin mx-auto" />
            <p className="text-slate-200 font-semibold text-lg">Generating your interview question...</p>
            <p className="text-slate-400 text-sm">Reasoning AI engine is initializing candidate context and turn plan.</p>
          </div>
        </div>
      </AppLayout>
    );
  }

  const currentQ = session?.current_question;
  const qNum = (session?.questions_answered || 0) + 1;
  const isTerminated = session?.status === 'terminated_by_candidate';

  return (
    <AppLayout>
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Top Header */}
        <div className="glass-card rounded-2xl p-4 md:p-6 border border-slate-800 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <button onClick={() => router.push('/dashboard')} className="p-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-400 hover:text-slate-200" title="Dashboard">
              <Home className="w-4 h-4" />
            </button>
            <div>
              <h1 className="font-bold text-slate-100 text-base">Adaptive AI Technical Interview</h1>
              <p className="text-xs text-slate-400">Session ID: {sessionId}</p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <button
              onClick={handleStartNewInterview}
              className="px-3.5 py-1.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold flex items-center gap-1.5 transition-all shadow-md"
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              <span>Start New Interview</span>
            </button>

            <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-xs font-mono text-blue-400">
              <Clock className="w-3.5 h-3.5" />
              <span>{formatTimer(seconds)}</span>
            </div>

            <div className="flex items-center gap-2 text-xs">
              <span className="text-slate-400">Progress:</span>
              <span className="font-bold text-slate-200">{session?.questions_answered || 0} / 8 Qs</span>
            </div>
          </div>
        </div>

        {error && (
          <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
            <button onClick={loadSession} className="px-3 py-1 rounded bg-rose-500/20 text-xs font-bold hover:bg-rose-500/30">
              Retry
            </button>
          </div>
        )}

        {isTerminated ? (
          <div className="glass-card rounded-3xl p-8 md:p-12 border border-amber-500/30 bg-gradient-to-br from-slate-900 via-amber-950/20 to-slate-900 space-y-6 text-center shadow-2xl">
            <div className="w-16 h-16 rounded-2xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center mx-auto text-amber-400 shadow-inner">
              <LogOut className="w-8 h-8" />
            </div>
            <div className="space-y-2 max-w-md mx-auto">
              <h2 className="text-2xl md:text-3xl font-extrabold text-slate-100 tracking-tight">Interview Ended</h2>
              <p className="text-base font-medium text-amber-300">Candidate chose to end the interview.</p>
              <p className="text-xs text-slate-400 pt-2 leading-relaxed">
                The interview was terminated immediately upon candidate withdrawal request. Submitted answers and history have been saved. No further questions will be generated.
              </p>
            </div>

            <div className="flex flex-wrap items-center justify-center gap-4 pt-4 border-t border-slate-800">
              <button
                onClick={() => router.push('/dashboard')}
                className="px-6 py-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold text-xs flex items-center gap-2 border border-slate-700 transition-all shadow-md active:scale-95"
              >
                <Home className="w-4 h-4" />
                <span>Back to Dashboard</span>
              </button>
              <button
                onClick={handleStartNewInterview}
                className="px-6 py-3 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs flex items-center gap-2 transition-all shadow-lg shadow-blue-500/25 active:scale-95"
              >
                <Play className="w-4 h-4 fill-current" />
                <span>Start New Interview</span>
              </button>
            </div>
          </div>
        ) : submitting ? (
          <ThinkingIndicator />
        ) : currentQ ? (
          <QuestionCard
            question={currentQ}
            questionNumber={qNum}
            totalQuestions={8}
          />
        ) : (
          <div className="glass-card rounded-2xl p-8 text-center space-y-4">
            <AlertCircle className="w-8 h-8 text-amber-400 mx-auto" />
            <p className="text-slate-200 font-semibold">Unable to display current question.</p>
            <button
              onClick={loadSession}
              className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs"
            >
              Retry Loading Session
            </button>
          </div>
        )}

        {/* Answer Box */}
        {currentQ && !submitting && !isTerminated && (
          <AnswerEditor
            onSubmit={handleSubmitAnswer}
            isSubmitting={submitting}
          />
        )}
      </div>
    </AppLayout>
  );
}

