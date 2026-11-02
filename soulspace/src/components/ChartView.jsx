/**
 * components/ChartView.jsx
 * Mood visualization using Recharts.
 * Renders a BarChart (mood frequency counts) and
 * a LineChart (7-day mood score trend).
 *
 * Props:
 *   moodCounts  {object}  – e.g. { Happy: 3, Calm: 2, Anxious: 1 }
 *   dailyTrend  {Array}   – [{ date, mood, mood_score }]
 *   loading     {boolean}
 */

import React, { useState } from 'react';
import {
    BarChart, Bar, LineChart, Line, AreaChart, Area,
    XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
} from 'recharts';

// Colour palette keyed by mood label
const MOOD_COLORS = {
    Happy: '#a78bfa',
    Calm: '#67e8f9',
    Anxious: '#fcd34d',
    Sad: '#93c5fd',
    Angry: '#f87171',
    Excited: '#86efac',
};
const FALLBACK_COLOR = '#c4b5fd';

// Formats YYYY-MM-DD → "Mon 15"
function shortDate(dateStr) {
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-US', { weekday: 'short', day: 'numeric' });
}

export default function ChartView({ moodCounts = {}, dailyTrend = [], emotionalTimeline = [], loading }) {
    const [view, setView] = useState('bar'); // 'bar' | 'line' | 'emotion'

    // Prepare BarChart dataset
    const barData = Object.entries(moodCounts).map(([label, count]) => ({
        label, count,
    }));

    // Prepare LineChart dataset
    const lineData = dailyTrend.map((d) => ({
        date: shortDate(d.date),
        score: d.mood_score,
        mood: d.mood,
    }));

    // Prepare Emotional Timeline dataset from AI pipeline
    const emotionData = emotionalTimeline.map((d) => ({
        date: shortDate(d.date),
        intensity: d.emotion_intensity ?? 0,
        emotion: d.primary_emotion ?? 'unknown',
        sentiment: d.sentiment ?? 'neutral',
        stress: d.stress_level ?? 'none',
    }));

    if (loading) {
        return (
            <div className="animate-pulse bg-slate-100 dark:bg-slate-800 rounded-3xl h-64 flex items-center justify-center text-slate-400">
                Loading chart…
            </div>
        );
    }

    return (
        <div className="bg-white dark:bg-slate-800 rounded-3xl shadow-sm border border-slate-100 dark:border-slate-700 p-6 transition-colors">
            {/* Header + toggle */}
            <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-bold text-slate-800 dark:text-slate-100">
                    Mood Insights 📊
                </h2>
                <div className="flex gap-2 bg-slate-100 dark:bg-slate-700 rounded-full p-1">
                    {[{key:'bar', label:'📊 Frequency'}, {key:'line', label:'📈 Trend'}, {key:'emotion', label:'🧠 AI Timeline'}].map((v) => (
                        <button
                            key={v.key}
                            onClick={() => setView(v.key)}
                            className={`px-3 py-1.5 rounded-full text-xs font-medium transition-all ${view === v.key
                                    ? 'bg-white dark:bg-slate-900 text-brand-600 dark:text-brand-400 shadow-sm'
                                    : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200'
                                }`}
                        >
                            {v.label}
                        </button>
                    ))}
                </div>
            </div>

            {/* Bar chart – mood frequency */}
            {view === 'bar' && (
                barData.length === 0 ? (
                    <p className="text-center text-slate-400 py-12">No mood data yet. Write your first entry!</p>
                ) : (
                    <ResponsiveContainer width="100%" height={260}>
                        <BarChart data={barData} barCategoryGap="30%">
                            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                            <XAxis dataKey="label" tick={{ fontSize: 13, fill: '#64748b' }} />
                            <YAxis allowDecimals={false} tick={{ fontSize: 12, fill: '#94a3b8' }} />
                            <Tooltip
                                contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 20px rgba(0,0,0,.1)' }}
                                cursor={{ fill: '#f1f5f9' }}
                            />
                            <Bar dataKey="count" name="Times logged" radius={[8, 8, 0, 0]}>
                                {barData.map((entry) => (
                                    <Cell
                                        key={entry.label}
                                        fill={MOOD_COLORS[entry.label] || FALLBACK_COLOR}
                                    />
                                ))}
                            </Bar>
                        </BarChart>
                    </ResponsiveContainer>
                )
            )}

            {/* Line chart – daily mood score */}
            {view === 'line' && (
                lineData.length === 0 ? (
                    <p className="text-center text-slate-400 py-12">No trend data available yet.</p>
                ) : (
                    <ResponsiveContainer width="100%" height={260}>
                        <LineChart data={lineData}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                            <XAxis dataKey="date" tick={{ fontSize: 12, fill: '#64748b' }} />
                            <YAxis domain={[0, 5]} ticks={[1, 2, 3, 4, 5]} tick={{ fontSize: 12, fill: '#94a3b8' }} />
                            <Tooltip
                                contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 20px rgba(0,0,0,.1)' }}
                                formatter={(val, _, props) => [`${val}/5 – ${props.payload.mood}`, 'Mood score']}
                            />
                            <Line
                                type="monotone"
                                dataKey="score"
                                stroke="#8b5cf6"
                                strokeWidth={3}
                                dot={{ r: 5, fill: '#8b5cf6', strokeWidth: 2, stroke: '#fff' }}
                                activeDot={{ r: 7 }}
                            />
                        </LineChart>
                    </ResponsiveContainer>
                )
            )}

            {/* Emotional Timeline – AI-analyzed emotion intensity */}
            {view === 'emotion' && (
                emotionData.length === 0 ? (
                    <p className="text-center text-slate-400 py-12">No AI analysis data yet. Write a few journal entries!</p>
                ) : (
                    <ResponsiveContainer width="100%" height={260}>
                        <AreaChart data={emotionData}>
                            <defs>
                                <linearGradient id="emotionGradient" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.4} />
                                    <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                            <XAxis dataKey="date" tick={{ fontSize: 12, fill: '#64748b' }} />
                            <YAxis domain={[0, 1]} ticks={[0, 0.25, 0.5, 0.75, 1.0]} tick={{ fontSize: 12, fill: '#94a3b8' }} />
                            <Tooltip
                                contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 20px rgba(0,0,0,.1)' }}
                                formatter={(val, _, props) => [
                                    `${(val * 100).toFixed(0)}%`,
                                    `${props.payload.emotion} (${props.payload.sentiment})`
                                ]}
                                labelFormatter={(label) => `Date: ${label}`}
                            />
                            <Area
                                type="monotone"
                                dataKey="intensity"
                                stroke="#8b5cf6"
                                strokeWidth={3}
                                fill="url(#emotionGradient)"
                                dot={{ r: 4, fill: '#8b5cf6', strokeWidth: 2, stroke: '#fff' }}
                                activeDot={{ r: 7 }}
                            />
                        </AreaChart>
                    </ResponsiveContainer>
                )
            )}
        </div>
    );
}
