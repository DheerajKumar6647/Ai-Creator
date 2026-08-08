"use client";

import React, { useState } from 'react';
import { AppLayout } from '../../components/layout/AppLayout';
import { Settings, Cpu, ShieldCheck, Key, RefreshCw, Check } from 'lucide-react';

export default function SettingsPage() {
  const [provider, setProvider] = useState('mock');
  const [geminiKey, setGeminiKey] = useState('');
  const [openaiKey, setOpenaiKey] = useState('');
  const [saved, setSaved] = useState(false);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  return (
    <AppLayout>
      <div className="max-w-3xl mx-auto space-y-8">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">LLM Provider & Engine Configuration</h1>
          <p className="text-xs text-slate-400">Configure AI provider options, API keys, and mock execution mode.</p>
        </div>

        <form onSubmit={handleSave} className="glass-card rounded-2xl p-6 border border-slate-800 space-y-6">
          <div className="space-y-3">
            <label className="font-bold text-slate-200 text-sm block">Active LLM Provider</label>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {[
                { id: 'mock', label: 'Mock Provider', desc: 'Instant local execution for testing & demo' },
                { id: 'gemini', label: 'Google Gemini', desc: 'Gemini 1.5 Flash / Pro reasoning models' },
                { id: 'openai', label: 'OpenAI GPT', desc: 'GPT-4o & GPT-4o-mini structured models' },
              ].map((item) => (
                <div
                  key={item.id}
                  onClick={() => setProvider(item.id)}
                  className={`cursor-pointer p-4 rounded-xl border transition-all ${
                    provider === item.id
                      ? 'bg-blue-600/10 border-blue-500 text-slate-100 shadow-lg'
                      : 'bg-slate-900/60 border-slate-800 text-slate-400 hover:border-slate-700'
                  }`}
                >
                  <h4 className="font-bold text-sm text-slate-200">{item.label}</h4>
                  <p className="text-[11px] text-slate-400 mt-1">{item.desc}</p>
                </div>
              ))}
            </div>
          </div>

          {provider === 'gemini' && (
            <div className="space-y-2">
              <label className="text-xs font-bold text-slate-300 flex items-center gap-1.5">
                <Key className="w-3.5 h-3.5 text-blue-400" />
                <span>Google Gemini API Key</span>
              </label>
              <input
                type="password"
                value={geminiKey}
                onChange={(e) => setGeminiKey(e.target.value)}
                placeholder="AIzaSy..."
                className="w-full px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-100 text-xs focus:outline-none focus:border-blue-500"
              />
            </div>
          )}

          {provider === 'openai' && (
            <div className="space-y-2">
              <label className="text-xs font-bold text-slate-300 flex items-center gap-1.5">
                <Key className="w-3.5 h-3.5 text-blue-400" />
                <span>OpenAI API Key</span>
              </label>
              <input
                type="password"
                value={openaiKey}
                onChange={(e) => setOpenaiKey(e.target.value)}
                placeholder="sk-proj-..."
                className="w-full px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-100 text-xs focus:outline-none focus:border-blue-500"
              />
            </div>
          )}

          <div className="pt-2 flex items-center justify-between">
            <span className="text-xs text-slate-400">
              {saved && <span className="text-emerald-400 font-bold flex items-center gap-1"><Check className="w-4 h-4" /> Settings updated successfully</span>}
            </span>

            <button
              type="submit"
              className="px-6 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs transition-all shadow-lg"
            >
              Save Configuration
            </button>
          </div>
        </form>
      </div>
    </AppLayout>
  );
}
