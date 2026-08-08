"use client";

import React, { useState, useEffect } from 'react';
import { AppLayout } from '../../components/layout/AppLayout';
import { candidateService } from '../../services/api';
import { Candidate } from '../../types';
import { User, Award, BookOpen, AlertTriangle, CheckCircle2, Zap } from 'lucide-react';

export default function ProfilePage() {
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [selected, setSelected] = useState<Candidate | null>(null);

  useEffect(() => {
    candidateService.list().then((cands) => {
      setCandidates(cands);
      if (cands.length > 0) setSelected(cands[0]);
    });
  }, []);

  return (
    <AppLayout>
      <div className="max-w-4xl mx-auto space-y-8">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Candidate Profiles & Learning Signals</h1>
          <p className="text-xs text-slate-400">View student trajectory across completed, skipped, and candidate models.</p>
        </div>

        <div className="flex gap-2 border-b border-slate-800 pb-2">
          {candidates.map((cand) => (
            <button
              key={cand.id}
              onClick={() => setSelected(cand)}
              className={`px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
                selected?.id === cand.id
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-900 text-slate-400 hover:text-slate-200'
              }`}
            >
              {cand.name}
            </button>
          ))}
        </div>

        {selected && (
          <div className="glass-card rounded-2xl p-6 border border-slate-800 space-y-6">
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 rounded-2xl bg-blue-600/20 text-blue-400 flex items-center justify-center font-bold text-xl border border-blue-500/30">
                {selected.name.split(' ').map((n) => n[0]).join('')}
              </div>
              <div>
                <h2 className="text-xl font-bold text-slate-100">{selected.name}</h2>
                <p className="text-xs text-slate-400">{selected.email || 'Cohort Learner'}</p>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800">
                <span className="text-[10px] text-slate-400 font-bold uppercase block">Completed Modules</span>
                <span className="text-xl font-bold text-emerald-400">{selected.completed_days.length} Days</span>
              </div>
              <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800">
                <span className="text-[10px] text-slate-400 font-bold uppercase block">Skipped Modules</span>
                <span className="text-xl font-bold text-amber-400">{selected.skipped_days.length} Days</span>
              </div>
              <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800">
                <span className="text-[10px] text-slate-400 font-bold uppercase block">Attempts</span>
                <span className="text-xl font-bold text-blue-400">{selected.attempts} Sessions</span>
              </div>
            </div>

            <div className="space-y-3">
              <h3 className="font-bold text-slate-200 text-sm">Learning Signals & Known Knowledge Gaps</h3>
              <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800 space-y-2 text-xs">
                <p><span className="font-semibold text-slate-400">Engineering Maturity: </span>{selected.learning_signals.engineering_maturity}</p>
                <p><span className="font-semibold text-slate-400">Communication Skill: </span>{selected.learning_signals.communication_skill}</p>
                <p><span className="font-semibold text-slate-400">Strong Topics: </span>{selected.learning_signals.strong_topics?.join(', ') || 'None'}</p>
                <p><span className="font-semibold text-slate-400">Weak Topics: </span>{selected.learning_signals.weak_topics?.join(', ') || 'None'}</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </AppLayout>
  );
}
