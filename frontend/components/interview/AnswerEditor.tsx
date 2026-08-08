"use client";

import React, { useState } from 'react';
import { Send, CornerDownLeft, Sparkles } from 'lucide-react';

interface AnswerEditorProps {
  onSubmit: (answerText: string) => void;
  isSubmitting: boolean;
}

export const AnswerEditor: React.FC<AnswerEditorProps> = ({ onSubmit, isSubmitting }) => {
  const [text, setText] = useState('');

  const wordCount = text.trim() ? text.trim().split(/\s+/).length : 0;
  const charCount = text.length;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!text.trim() || isSubmitting) return;
    onSubmit(text.trim());
    setText('');
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      if (text.trim() && !isSubmitting) {
        onSubmit(text.trim());
        setText('');
      }
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <div className="glass-card rounded-2xl p-4 border border-slate-800 focus-within:border-blue-500/50 transition-all shadow-lg">
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isSubmitting}
          placeholder="Explain your technical reasoning, trade-offs, and architecture decisions..."
          className="w-full h-44 bg-transparent text-slate-100 placeholder-slate-500 focus:outline-none resize-none text-sm leading-relaxed custom-scrollbar"
        />

        <div className="flex flex-wrap items-center justify-between gap-4 pt-3 border-t border-slate-800/80 text-xs text-slate-400">
          <div className="flex items-center gap-4">
            <span>{wordCount} words</span>
            <span>·</span>
            <span>{charCount} characters</span>
            <span className="hidden sm:inline-block text-slate-500">
              (Press <kbd className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 font-mono text-[10px]">Ctrl + Enter</kbd> to submit)
            </span>
          </div>

          <button
            type="submit"
            disabled={!text.trim() || isSubmitting}
            className={`px-5 py-2.5 rounded-xl font-semibold text-sm flex items-center gap-2 transition-all shadow-md ${
              !text.trim() || isSubmitting
                ? 'bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700/50'
                : 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white hover:from-blue-500 hover:to-indigo-500 shadow-blue-500/25 active:scale-95'
            }`}
          >
            {isSubmitting ? (
              <>
                <div className="w-4 h-4 rounded-full border-2 border-white/20 border-t-white animate-spin" />
                <span>Evaluating...</span>
              </>
            ) : (
              <>
                <span>Submit Answer</span>
                <Send className="w-4 h-4" />
              </>
            )}
          </button>
        </div>
      </div>
    </form>
  );
};
