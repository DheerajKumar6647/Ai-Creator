"use client";

import React from 'react';
import { CurriculumDay } from '../../types';
import { BookOpen, CheckCircle2, Circle, AlertCircle } from 'lucide-react';

interface CurriculumProgressCardProps {
  days: CurriculumDay[];
  completedDays: number[];
  skippedDays: number[];
}

export const CurriculumProgressCard: React.FC<CurriculumProgressCardProps> = ({
  days,
  completedDays,
  skippedDays
}) => {
  return (
    <div className="glass-card rounded-2xl p-6 border border-slate-800 space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <BookOpen className="w-5 h-5 text-blue-400" />
          <h3 className="font-bold text-slate-100 text-lg">31-Day AI Cohort Syllabus</h3>
        </div>
        <span className="text-xs text-slate-400 font-medium">
          {completedDays.length} / {days.length} Modules Completed
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-h-72 overflow-y-auto custom-scrollbar pr-1">
        {days.map((day) => {
          const isCompleted = completedDays.includes(day.day_number);
          const isSkipped = skippedDays.includes(day.day_number);

          return (
            <div
              key={day.day_number}
              className={`p-3.5 rounded-xl border transition-all flex items-start justify-between gap-3 ${
                isCompleted
                  ? 'bg-emerald-500/5 border-emerald-500/20 text-emerald-300'
                  : isSkipped
                  ? 'bg-amber-500/5 border-amber-500/20 text-amber-300'
                  : 'bg-slate-900/60 border-slate-800/80 text-slate-300'
              }`}
            >
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="font-bold text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-200">
                    Day {day.day_number}
                  </span>
                  <h4 className="font-semibold text-sm truncate">{day.title}</h4>
                </div>
                <p className="text-xs text-slate-400 line-clamp-1">{day.description}</p>
              </div>

              {isCompleted ? (
                <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-1" />
              ) : isSkipped ? (
                <AlertCircle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-1" />
              ) : (
                <Circle className="w-4 h-4 text-slate-600 flex-shrink-0 mt-1" />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
