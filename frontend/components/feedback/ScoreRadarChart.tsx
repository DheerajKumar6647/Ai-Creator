"use client";

import React from 'react';
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer } from 'recharts';

interface ScoreRadarChartProps {
  scores: Record<string, number>;
}

export const ScoreRadarChart: React.FC<ScoreRadarChartProps> = ({ scores }) => {
  const data = Object.entries(scores).map(([key, val]) => ({
    dimension: key,
    score: val,
    fullMark: 10,
  }));

  return (
    <div className="glass-card rounded-2xl p-6 border border-slate-800 space-y-3">
      <h3 className="font-bold text-slate-100 text-base">Multi-Dimensional Capability Radar</h3>
      <p className="text-xs text-slate-400">Evaluation across technical depth, engineering thinking, and communication.</p>

      <div className="w-full h-72">
        <ResponsiveContainer width="100%" height="100%">
          <RadarChart cx="50%" cy="50%" outerRadius="80%" data={data}>
            <PolarGrid stroke="#334155" />
            <PolarAngleAxis dataKey="dimension" stroke="#94a3b8" tick={{ fontSize: 11 }} />
            <PolarRadiusAxis angle={30} domain={[0, 10]} stroke="#475569" />
            <Radar name="Candidate" dataKey="score" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.35} />
          </RadarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
