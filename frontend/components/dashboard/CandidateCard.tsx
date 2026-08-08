import React from 'react';
import { Candidate } from '../../types';
import { User, Award, Zap, AlertTriangle, Briefcase, Star, Trash2 } from 'lucide-react';

interface CandidateCardProps {
  candidate: Candidate;
  isSelected: boolean;
  onSelect: () => void;
  onDelete?: (e: React.MouseEvent) => void;
}

export const CandidateCard: React.FC<CandidateCardProps> = ({ candidate, isSelected, onSelect, onDelete }) => {
  const signals = candidate.learning_signals || {};

  return (
    <div
      onClick={onSelect}
      className={`cursor-pointer rounded-2xl p-6 transition-all border ${
        isSelected
          ? 'bg-blue-600/10 border-blue-500 shadow-lg shadow-blue-500/10 scale-[1.02]'
          : 'glass-card hover:bg-slate-900/90 border-slate-800'
      }`}
    >
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="w-11 h-11 rounded-xl bg-slate-800 border border-slate-700/60 flex items-center justify-center font-bold text-lg text-blue-400">
            {candidate.name.split(' ').map(n => n[0]).join('')}
          </div>
          <div>
            <h3 className="font-semibold text-slate-100 text-base">{candidate.name}</h3>
            <p className="text-xs text-slate-400 flex items-center gap-1">
              <Briefcase className="w-3 h-3 text-slate-500" />
              <span>{candidate.target_role || 'AI Engineer'}</span>
              <span>·</span>
              <span>{candidate.years_of_experience || 3} yrs exp</span>
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className={`px-2.5 py-1 rounded-full text-xs font-semibold border ${
            isSelected
              ? 'bg-blue-500 text-white border-blue-400'
              : 'bg-slate-800 text-slate-400 border-slate-700'
          }`}>
            {isSelected ? 'Active Candidate' : 'Select'}
          </span>
          {onDelete && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onDelete(e);
              }}
              title="Delete Candidate Profile"
              className="p-1.5 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/20 transition-all"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      <div className="space-y-3">
        <div>
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1.5">
            <span>Curriculum Progress</span>
            <span className="font-bold text-slate-200">{candidate.completion_percentage.toFixed(0)}%</span>
          </div>
          <div className="w-full h-2 rounded-full bg-slate-800 overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-blue-600 to-indigo-500 rounded-full transition-all duration-500"
              style={{ width: `${candidate.completion_percentage}%` }}
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-2 text-xs pt-1">
          <div className="bg-slate-900/60 rounded-xl p-2.5 border border-slate-800/80">
            <span className="text-slate-400 block text-[10px] uppercase font-bold">Level</span>
            <span className={`font-semibold ${
              (candidate.experience_level || candidate.target_role || '').toLowerCase().includes('junior')
                ? 'text-emerald-400'
                : (candidate.experience_level || candidate.target_role || '').toLowerCase().includes('principal') || (candidate.experience_level || candidate.target_role || '').toLowerCase().includes('staff') || (candidate.experience_level || candidate.target_role || '').toLowerCase().includes('senior') || (candidate.experience_level || candidate.target_role || '').toLowerCase().includes('architect')
                ? 'text-purple-400'
                : 'text-blue-400'
            }`}>
              {candidate.experience_level || 'Mid-Senior'}
            </span>
          </div>
          <div className="bg-slate-900/60 rounded-xl p-2.5 border border-slate-800/80">
            <span className="text-slate-400 block text-[10px] uppercase font-bold">Avg Score</span>
            <span className="font-semibold text-blue-400">{signals.average_score ? `${signals.average_score.toFixed(1)} / 10` : 'N/A'}</span>
          </div>
        </div>


        {candidate.primary_skills && candidate.primary_skills.length > 0 && (
          <div className="flex flex-wrap items-center gap-1.5 pt-1">
            {candidate.primary_skills.slice(0, 3).map((skill, idx) => (
              <span key={idx} className="px-2 py-0.5 rounded-md bg-slate-800/80 text-slate-300 text-[10px] font-mono border border-slate-700/50">
                {skill}
              </span>
            ))}
          </div>
        )}

        {signals.weak_topics && signals.weak_topics.length > 0 && (
          <div className="flex items-center gap-1.5 text-xs text-amber-400/90 pt-1">
            <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0" />
            <span className="truncate">Weak areas: {signals.weak_topics.join(', ')}</span>
          </div>
        )}
      </div>
    </div>
  );
};

