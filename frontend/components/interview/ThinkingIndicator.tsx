"use client";

import React, { useState, useEffect } from 'react';
import { Brain, Sparkles, Cpu, Layers } from 'lucide-react';

export const ThinkingIndicator: React.FC = () => {
  const messages = [
    'Analyzing candidate response...',
    'Evaluating technical accuracy & depth...',
    'Updating Candidate Understanding Model...',
    'Adjusting dynamic interview difficulty...',
    'Selecting optimal curriculum topic...',
    'Formulating next targeted question...'
  ];

  const [currentIdx, setCurrentIdx] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentIdx((prev) => (prev + 1) % messages.length);
    }, 1800);
    return () => clearInterval(interval);
  }, [messages.length]);

  return (
    <div className="glass-card rounded-2xl p-6 border border-blue-500/20 bg-blue-500/5 shadow-xl flex items-center gap-4 animate-pulse">
      <div className="w-12 h-12 rounded-xl bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-blue-400">
        <Brain className="w-6 h-6 animate-bounce" />
      </div>
      <div>
        <div className="flex items-center gap-2">
          <span className="font-bold text-slate-100 text-sm">InterviewAI Reasoning Engine</span>
          <Sparkles className="w-3.5 h-3.5 text-blue-400" />
        </div>
        <p className="text-xs text-blue-400 font-medium mt-0.5">{messages[currentIdx]}</p>
      </div>
    </div>
  );
};
