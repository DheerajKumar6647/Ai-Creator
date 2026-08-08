"use client";

import React from 'react';
import { Question } from '../../types';
import { HelpCircle, Sparkles, Layers, Gauge, Clock } from 'lucide-react';

interface QuestionCardProps {
  question: Question;
  questionNumber: number;
  totalQuestions: number;
}

export const QuestionCard: React.FC<QuestionCardProps> = ({
  question,
  questionNumber,
  totalQuestions
}) => {
  const getDifficultyBadge = (level: number) => {
    switch (level) {
      case 1: return { label: 'Level 1 · Fundamentals', color: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' };
      case 2: return { label: 'Level 2 · Intermediate', color: 'bg-blue-500/10 text-blue-400 border-blue-500/20' };
      case 3: return { label: 'Level 3 · Applied Engineering', color: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20' };
      case 4: return { label: 'Level 4 · System Design', color: 'bg-amber-500/10 text-amber-400 border-amber-500/20' };
      case 5: return { label: 'Level 5 · Production', color: 'bg-rose-500/10 text-rose-400 border-rose-500/20' };
      default: return { label: 'Level 2', color: 'bg-blue-500/10 text-blue-400 border-blue-500/20' };
    }
  };

  const badge = getDifficultyBadge(question.difficulty);

  return (
    <div className="glass-card rounded-2xl p-6 md:p-8 border border-slate-800 shadow-xl relative overflow-hidden">
      <div className="absolute top-0 right-0 w-64 h-64 bg-blue-500/5 rounded-full blur-3xl pointer-events-none" />

      <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
        <div className="flex items-center gap-3">
          <span className="flex items-center justify-center w-8 h-8 rounded-lg bg-blue-600/20 text-blue-400 font-bold text-sm border border-blue-500/30">
            Q{questionNumber}
          </span>
          <div className="flex items-center gap-2 text-xs font-semibold text-slate-400">
            <Layers className="w-3.5 h-3.5 text-blue-400" />
            <span>Day {question.curriculum_day}</span>
            <span>·</span>
            <span className="text-slate-200">{question.topic}</span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {question.is_follow_up && (
            <span className="px-3 py-1 rounded-full text-xs font-semibold bg-purple-500/10 text-purple-400 border border-purple-500/20 flex items-center gap-1.5 animate-pulse">
              <Sparkles className="w-3 h-3" />
              Follow-up Question
            </span>
          )}
          <span className={`px-3 py-1 rounded-full text-xs font-semibold border ${badge.color}`}>
            {badge.label}
          </span>
        </div>
      </div>

      <div className="space-y-4">
        <div className="flex items-start gap-3">
          <HelpCircle className="w-6 h-6 text-blue-400 flex-shrink-0 mt-1" />
          <h2 className="text-xl md:text-2xl font-semibold text-slate-100 leading-relaxed tracking-tight">
            {question.question_text}
          </h2>
        </div>

        {question.intent && (
          <div className="bg-slate-900/60 rounded-xl p-4 border border-slate-800/80 text-xs text-slate-400">
            <span className="font-semibold text-slate-300">Interviewer Intent: </span>
            {question.intent}
          </div>
        )}

        {question.expected_concepts && question.expected_concepts.length > 0 && (
          <div className="flex flex-wrap items-center gap-2 pt-2">
            <span className="text-xs font-medium text-slate-400">Key Concepts:</span>
            {question.expected_concepts.map((concept, idx) => (
              <span key={idx} className="px-2.5 py-1 rounded-lg bg-slate-800/60 text-slate-300 text-xs font-mono border border-slate-700/50">
                {concept}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
