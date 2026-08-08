"use client";

import React, { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { AppLayout } from '../../../components/layout/AppLayout';
import { HiringDecisionCard } from '../../../components/feedback/HiringDecisionCard';
import { ScoreRadarChart } from '../../../components/feedback/ScoreRadarChart';
import { feedbackService, candidateService, interviewService } from '../../../services/api';

import { FeedbackReport } from '../../../types';
import { Award, CheckCircle2, AlertTriangle, BookOpen, ArrowLeft, Download, Share2, Sparkles, Layers } from 'lucide-react';

export default function FeedbackReportPage() {
  const router = useRouter();
  const params = useParams();
  const sessionId = params.sessionId as string;

  const [report, setReport] = useState<FeedbackReport | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadFeedback();
  }, [sessionId]);

  const loadFeedback = async () => {
    try {
      setLoading(true);
      const data = await feedbackService.getBySessionId(sessionId);
      setReport(data);
    } catch (err) {
      console.error("Error loading feedback report:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleExport = (format: string) => {
    if (!report) return;
    const content = JSON.stringify(report, null, 2);
    const blob = new Blob([content], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `InterviewAI_Report_${sessionId}.${format}`;
    a.click();
  };

  if (loading) {
    return (
      <AppLayout>
        <div className="max-w-5xl mx-auto py-12 space-y-6">
          <div className="h-44 glass-card rounded-2xl animate-pulse" />
          <div className="h-72 glass-card rounded-2xl animate-pulse" />
        </div>
      </AppLayout>
    );
  }

  if (!report) {
    return (
      <AppLayout>
        <div className="max-w-md mx-auto py-16 text-center space-y-4">
          <AlertTriangle className="w-12 h-12 text-amber-400 mx-auto" />
          <h2 className="text-xl font-bold text-slate-100">Feedback Report Not Found</h2>
          <p className="text-xs text-slate-400">Unable to retrieve interview report for session {sessionId}.</p>
          <button onClick={() => router.push('/dashboard')} className="px-4 py-2 rounded-xl bg-blue-600 text-white font-semibold text-xs">
            Return to Dashboard
          </button>
        </div>
      </AppLayout>
    );
  }

  return (
    <AppLayout>
      <div className="max-w-5xl mx-auto space-y-8 pb-12">
        {/* Navigation Header */}
        <div className="flex items-center justify-between">
          <button onClick={() => router.push('/dashboard')} className="flex items-center gap-2 text-xs font-semibold text-slate-400 hover:text-slate-200">
            <ArrowLeft className="w-4 h-4" />
            <span>Back to Dashboard</span>
          </button>

          <div className="flex items-center gap-3">
            <button
              onClick={async () => {
                try {
                  const cands = await candidateService.list();
                  const candId = cands[0]?.id || 'cand_alex_chen';
                  const newSession = await interviewService.start(candId);
                  router.push(`/interview/${newSession.session_id}`);
                } catch (err: any) {
                  alert('Error starting new interview: ' + (err.response?.data?.detail || err.message));
                }
              }}
              className="px-4 py-2 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-bold text-xs flex items-center gap-2 shadow-lg transition-all"
            >
              <Sparkles className="w-4 h-4" />
              <span>Start New Interview</span>
            </button>

            <button onClick={() => handleExport('json')} className="px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-300 hover:bg-slate-800 text-xs font-medium flex items-center gap-1.5">
              <Download className="w-3.5 h-3.5" />
              <span>Export JSON</span>
            </button>
            <button onClick={() => window.print()} className="px-3 py-1.5 rounded-xl bg-blue-600 text-white hover:bg-blue-500 text-xs font-medium flex items-center gap-1.5">
              <Share2 className="w-3.5 h-3.5" />
              <span>Print Report</span>
            </button>
          </div>
        </div>


        {/* Hiring Decision Header Card */}
        <HiringDecisionCard
          decision={report.hiring_recommendation}
          confidence={report.recommendation_confidence}
          reasoning={report.recommendation_reasoning}
          overallRating={report.overall_rating}
        />

        {/* Radar & Executive Summaries Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <ScoreRadarChart scores={report.scores || {}} />

          <div className="glass-card rounded-2xl p-6 border border-slate-800 space-y-4">
            <h3 className="font-bold text-slate-100 text-base">Executive Technical Summary</h3>
            <p className="text-xs text-slate-300 leading-relaxed bg-slate-900/60 p-3.5 rounded-xl border border-slate-800/80">
              {report.technical_summary}
            </p>

            <h4 className="font-bold text-slate-100 text-xs uppercase tracking-wider text-slate-400">Communication & Reasoning</h4>
            <p className="text-xs text-slate-300 leading-relaxed bg-slate-900/60 p-3.5 rounded-xl border border-slate-800/80">
              {report.communication_summary}
            </p>
          </div>
        </div>

        {/* Strengths & Weaknesses Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="glass-card rounded-2xl p-6 border border-emerald-500/20 bg-emerald-500/5 space-y-4">
            <div className="flex items-center gap-2 text-emerald-400 font-bold text-base">
              <CheckCircle2 className="w-5 h-5" />
              <span>Demonstrated Strengths</span>
            </div>
            <ul className="space-y-2">
              {report.strengths.map((str, idx) => (
                <li key={idx} className="text-xs text-slate-200 flex items-start gap-2 bg-slate-900/60 p-3 rounded-xl border border-emerald-500/10">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mt-1.5 flex-shrink-0" />
                  <span>{str}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="glass-card rounded-2xl p-6 border border-amber-500/20 bg-amber-500/5 space-y-4">
            <div className="flex items-center gap-2 text-amber-400 font-bold text-base">
              <AlertTriangle className="w-5 h-5" />
              <span>Targeted Growth Areas</span>
            </div>
            <ul className="space-y-2">
              {report.weaknesses.map((wk, idx) => (
                <li key={idx} className="text-xs text-slate-200 flex items-start gap-2 bg-slate-900/60 p-3 rounded-xl border border-amber-500/10">
                  <span className="w-1.5 h-1.5 rounded-full bg-amber-400 mt-1.5 flex-shrink-0" />
                  <span>{wk}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Misconception Report */}
        {report.misconception_report && report.misconception_report.length > 0 && (
          <div className="glass-card rounded-2xl p-6 border border-slate-800 space-y-4">
            <h3 className="font-bold text-slate-100 text-base">Discovered Technical Misconceptions</h3>
            <div className="space-y-3">
              {report.misconception_report.map((m, idx) => (
                <div key={idx} className="bg-slate-900/70 p-4 rounded-xl border border-slate-800 space-y-2 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-amber-400">Misconception: {m.misconception}</span>
                    <span className="px-2 py-0.5 rounded bg-slate-800 text-[10px] font-bold uppercase text-slate-400">{m.impact} Impact</span>
                  </div>
                  <p className="text-slate-300"><span className="font-bold text-slate-400">Correct Concept: </span>{m.correct_concept}</p>
                  <p className="text-blue-400"><span className="font-bold text-slate-400">Suggested Action: </span>{m.suggested_practice}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Learning Roadmap */}
        {report.learning_roadmap && report.learning_roadmap.length > 0 && (
          <div className="glass-card rounded-2xl p-6 border border-blue-500/20 bg-blue-500/5 space-y-4">
            <div className="flex items-center gap-2 text-blue-400 font-bold text-base">
              <BookOpen className="w-5 h-5" />
              <span>Personalized Learning Roadmap</span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {report.learning_roadmap.map((item, idx) => (
                <div key={idx} className="bg-slate-900/80 p-4 rounded-xl border border-slate-800 space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="w-5 h-5 rounded-full bg-blue-600/20 text-blue-400 flex items-center justify-center font-bold text-xs">
                      P{item.priority}
                    </span>
                    <h4 className="font-bold text-slate-200 text-xs">{item.topic}</h4>
                  </div>
                  <p className="text-xs text-slate-400 pl-7">{item.action}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </AppLayout>
  );
}
