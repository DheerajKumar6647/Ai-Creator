"use client";

import React from 'react';
import { Award, CheckCircle2, AlertCircle, ShieldAlert, Sparkles } from 'lucide-react';

interface HiringDecisionCardProps {
  decision: string;
  confidence: number;
  reasoning: string;
  overallRating: number;
}

export const HiringDecisionCard: React.FC<HiringDecisionCardProps> = ({
  decision,
  confidence,
  reasoning,
  overallRating
}) => {
  const getBadgeStyle = (dec: string) => {
    switch (dec) {
      case 'STRONG_HIRE': return { label: 'Strong Hire', bg: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' };
      case 'HIRE': return { label: 'Hire', bg: 'bg-blue-500/10 text-blue-400 border-blue-500/30' };
      case 'LEAN_HIRE': return { label: 'Lean Hire', bg: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/30' };
      case 'BORDERLINE': return { label: 'Borderline', bg: 'bg-amber-500/10 text-amber-400 border-amber-500/30' };
      case 'NEEDS_IMPROVEMENT': return { label: 'Needs Improvement', bg: 'bg-orange-500/10 text-orange-400 border-orange-500/30' };
      default: return { label: 'Not Ready', bg: 'bg-rose-500/10 text-rose-400 border-rose-500/30' };
    }
  };

  const badge = getBadgeStyle(decision);

  return (
    <div className="glass-card rounded-2xl p-6 md:p-8 border border-slate-800 space-y-5 relative overflow-hidden">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-xl bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-blue-400">
            <Award className="w-6 h-6" />
          </div>
          <div>
            <h3 className="font-bold text-slate-100 text-lg">Senior Engineering Hiring Recommendation</h3>
            <p className="text-xs text-slate-400">Evidence-based recommendation calculated from full interview trajectory.</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="text-right">
            <span className="text-[10px] text-slate-400 font-bold uppercase block">Overall Rating</span>
            <span className="text-xl font-bold text-blue-400">{overallRating.toFixed(1)} / 10</span>
          </div>
          <span className={`px-4 py-2 rounded-xl text-sm font-bold border shadow-lg ${badge.bg}`}>
            {badge.label}
          </span>
        </div>
      </div>

      <div className="bg-slate-900/70 rounded-xl p-5 border border-slate-800/80 space-y-2">
        <div className="flex items-center justify-between text-xs text-slate-400">
          <span className="font-bold text-slate-300">Agent Recommendation Reasoning:</span>
          <span>Confidence: {(confidence * 100).toFixed(0)}%</span>
        </div>
        <p className="text-sm text-slate-200 leading-relaxed">{reasoning}</p>
      </div>
    </div>
  );
};
