"use client";

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { AppLayout } from '../../components/layout/AppLayout';
import { CandidateCard } from '../../components/dashboard/CandidateCard';
import { CurriculumProgressCard } from '../../components/dashboard/CurriculumProgressCard';
import { candidateService, curriculumService, interviewService } from '../../services/api';
import { Candidate, CurriculumDay } from '../../types';
import { Play, Sparkles, Trophy, BookOpen, AlertCircle, RefreshCw, UserPlus, X, Check } from 'lucide-react';

export default function DashboardPage() {
  const router = useRouter();
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [selectedCandidate, setSelectedCandidate] = useState<Candidate | null>(null);
  const [curriculumDays, setCurriculumDays] = useState<CurriculumDay[]>([]);
  const [loading, setLoading] = useState(true);
  const [startingInterview, setStartingInterview] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // New Candidate Modal state
  const [showModal, setShowModal] = useState(false);
  const [creatingCandidate, setCreatingCandidate] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    target_role: 'Senior AI Engineer',
    experience_level: 'Mid-Senior',
    years_of_experience: 4,
    primary_skills: 'Python, RAG, LangGraph, Vector Databases',
    resume_summary: 'Built production RAG pipelines with hybrid search and vector databases.'
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [cands, days] = await Promise.all([
        candidateService.list(),
        curriculumService.getDays()
      ]);
      setCandidates(cands);
      if (cands.length > 0) {
        setSelectedCandidate(cands[0]);
      }
      setCurriculumDays(days);
    } catch (err: any) {
      console.error("Dashboard error:", err);
      setError("Failed to load dashboard data. Ensure backend service is running.");
    } finally {
      setLoading(false);
    }
  };

  const handleStartInterview = async () => {
    if (!selectedCandidate) return;
    try {
      setStartingInterview(true);
      const session = await interviewService.start(selectedCandidate.id);
      router.push(`/interview/${session.session_id}`);
    } catch (err: any) {
      console.error("Start interview error:", err);
      alert("Error starting interview session: " + (err.response?.data?.detail || err.message));
      setStartingInterview(false);
    }
  };

  const handleCreateCandidate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name.trim()) return;
    try {
      setCreatingCandidate(true);
      const skills = formData.primary_skills.split(',').map(s => s.trim()).filter(Boolean);
      const created = await candidateService.create({
        name: formData.name.trim(),
        email: formData.email.trim() || undefined,
        target_role: formData.target_role,
        experience_level: formData.experience_level,
        years_of_experience: Number(formData.years_of_experience),
        primary_skills: skills,
        resume_summary: formData.resume_summary
      });
      setCandidates(prev => [created, ...prev]);
      setSelectedCandidate(created);
      setShowModal(false);
      setFormData({
        name: '',
        email: '',
        target_role: 'Senior AI Engineer',
        experience_level: 'Mid-Senior',
        years_of_experience: 4,
        primary_skills: 'Python, RAG, LangGraph, Vector Databases',
        resume_summary: 'Built production RAG pipelines with hybrid search and vector databases.'
      });
    } catch (err: any) {
      console.error('Error creating candidate:', err);
      alert('Failed to create candidate: ' + (err.response?.data?.detail || err.message));
    } finally {
      setCreatingCandidate(false);
    }
  };

  const handleDeleteCandidate = async (candidate: Candidate, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!window.confirm(`Are you sure you want to delete profile for "${candidate.name}"?`)) {
      return;
    }
    try {
      await candidateService.delete(candidate.id);
      const updated = candidates.filter(c => c.id !== candidate.id);
      setCandidates(updated);
      if (selectedCandidate?.id === candidate.id) {
        setSelectedCandidate(updated.length > 0 ? updated[0] : null);
      }
    } catch (err: any) {
      console.error('Error deleting candidate:', err);
      alert('Failed to delete candidate: ' + (err.response?.data?.detail || err.message));
    }
  };

  return (
    <AppLayout>
      <div className="space-y-8">
        {/* Banner */}
        <div className="glass-card rounded-3xl p-8 border border-blue-500/20 bg-gradient-to-r from-blue-950/40 via-slate-900 to-indigo-950/40 relative overflow-hidden shadow-2xl">
          <div className="absolute top-0 right-0 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl pointer-events-none" />
          
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 relative z-10">
            <div className="space-y-2 max-w-2xl">
              <div className="flex items-center gap-2">
                <span className="px-3 py-1 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20 text-xs font-semibold flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5" />
                  Reasoning AI Interview Engine
                </span>
              </div>
              <h1 className="text-3xl md:text-4xl font-extrabold text-slate-100 tracking-tight">
                Evaluate AI Engineering Understanding
              </h1>
              <p className="text-slate-400 text-sm leading-relaxed">
                InterviewAI conducts dynamic, multi-turn technical interviews tailored to candidate history across RAG, Vector Databases, Embeddings, Agents, and Guardrails.
              </p>
            </div>

            <button
              onClick={handleStartInterview}
              disabled={!selectedCandidate || startingInterview}
              className="px-8 py-4 rounded-2xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-bold text-base flex items-center justify-center gap-3 transition-all shadow-xl shadow-blue-500/25 active:scale-95 disabled:opacity-50"
            >
              {startingInterview ? (
                <>
                  <RefreshCw className="w-5 h-5 animate-spin" />
                  <span>Preparing Engine...</span>
                </>
              ) : (
                <>
                  <Play className="w-5 h-5 fill-current" />
                  <span>Start Technical Interview</span>
                </>
              )}
            </button>
          </div>
        </div>

        {error && (
          <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-4 h-4" />
              <span>{error}</span>
            </div>
            <button onClick={loadData} className="px-3 py-1 rounded bg-rose-500/20 text-xs font-bold hover:bg-rose-500/30">
              Retry
            </button>
          </div>
        )}

        {/* Candidate Selection Header */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold text-slate-100">Select Candidate Profile</h2>
            <button
              onClick={() => setShowModal(true)}
              className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-blue-400 text-xs font-semibold flex items-center gap-2 transition-all"
            >
              <UserPlus className="w-4 h-4" />
              <span>Create Candidate</span>
            </button>
          </div>

          {loading ? (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-44 glass-card rounded-2xl animate-pulse" />
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {candidates.map((cand) => (
                <CandidateCard
                  key={cand.id}
                  candidate={cand}
                  isSelected={selectedCandidate?.id === cand.id}
                  onSelect={() => setSelectedCandidate(cand)}
                  onDelete={(e) => handleDeleteCandidate(cand, e)}
                />
              ))}
            </div>
          )}
        </div>

        {/* Syllabus Progress */}
        {selectedCandidate && (
          <CurriculumProgressCard
            days={curriculumDays}
            completedDays={selectedCandidate.completed_days || []}
            skippedDays={selectedCandidate.skipped_days || []}
          />
        )}
      </div>

      {/* Create Candidate Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="glass-card max-w-lg w-full rounded-3xl p-6 md:p-8 border border-slate-800 space-y-6 shadow-2xl relative">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <h3 className="text-xl font-bold text-slate-100 flex items-center gap-2">
                <UserPlus className="w-5 h-5 text-blue-400" />
                <span>Create Candidate Profile</span>
              </h3>
              <button
                onClick={() => setShowModal(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreateCandidate} className="space-y-4 text-sm">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Full Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Sarah Jenkins"
                  value={formData.name}
                  onChange={e => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Email</label>
                  <input
                    type="email"
                    placeholder="sarah@example.com"
                    value={formData.email}
                    onChange={e => setFormData({ ...formData, email: e.target.value })}
                    className="w-full px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Target Role (Position)</label>
                  <select
                    value={formData.target_role}
                    onChange={e => {
                      const role = e.target.value;
                      let expLevel = formData.experience_level;
                      let yrs = formData.years_of_experience;
                      if (role === 'Junior AI Developer') { expLevel = 'Junior'; yrs = 1; }
                      else if (role === 'AI Engineer') { expLevel = 'Mid-Senior'; yrs = 3; }
                      else if (role === 'Senior AI Engineer') { expLevel = 'Senior'; yrs = 5; }
                      else if (role === 'AI Architect') { expLevel = 'Staff / Principal'; yrs = 8; }
                      setFormData({ ...formData, target_role: role, experience_level: expLevel, years_of_experience: yrs });
                    }}
                    className="w-full px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-100 focus:outline-none focus:border-blue-500"
                  >
                    <option value="Senior AI Engineer">Senior AI Engineer</option>
                    <option value="AI Engineer">AI Engineer</option>
                    <option value="AI Architect">AI Architect</option>
                    <option value="Junior AI Developer">Junior AI Developer</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Experience Level</label>
                  <select
                    value={formData.experience_level}
                    onChange={e => setFormData({ ...formData, experience_level: e.target.value })}
                    className="w-full px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-100 focus:outline-none focus:border-blue-500"
                  >
                    <option value="Junior">Junior (0-2 yrs)</option>
                    <option value="Mid-Senior">Mid-Senior (3-5 yrs)</option>
                    <option value="Senior">Senior (5-8 yrs)</option>
                    <option value="Staff / Principal">Staff / Principal (8+ yrs)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Years of Experience</label>
                  <input
                    type="number"
                    min="0"
                    max="30"
                    value={formData.years_of_experience}
                    onChange={e => setFormData({ ...formData, years_of_experience: Number(e.target.value) })}
                    className="w-full px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-100 focus:outline-none focus:border-blue-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Primary Skills (comma-separated)</label>
                <input
                  type="text"
                  placeholder="Python, PyTorch, RAG, LangGraph, FAISS"
                  value={formData.primary_skills}
                  onChange={e => setFormData({ ...formData, primary_skills: e.target.value })}
                  className="w-full px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Resume / Profile Summary</label>
                <textarea
                  rows={2}
                  placeholder="Brief summary of candidate technical background..."
                  value={formData.resume_summary}
                  onChange={e => setFormData({ ...formData, resume_summary: e.target.value })}
                  className="w-full px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold text-xs"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creatingCandidate}
                  className="px-6 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs flex items-center gap-2 disabled:opacity-50"
                >
                  {creatingCandidate ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
                  <span>Save Candidate Profile</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </AppLayout>
  );
}

