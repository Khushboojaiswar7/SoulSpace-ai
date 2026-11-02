import React, { useState, useEffect } from 'react';
import { getJourneyReport } from '../api/journal';

export default function JourneyReportModal({ token, onClose }) {
    const [loading, setLoading] = useState(true);
    const [report, setReport] = useState(null);
    const [error, setError] = useState(null);

    useEffect(() => {
        async function fetchReport() {
            try {
                const data = await getJourneyReport(token);
                setReport(data.report);
            } catch (err) {
                setError(err.message);
            } finally {
                setLoading(false);
            }
        }
        fetchReport();
    }, [token]);

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-sm p-4 animate-fade-in">
            <div className="bg-white dark:bg-slate-900 rounded-3xl w-full max-w-2xl max-h-[90vh] overflow-y-auto shadow-xl border border-slate-200 dark:border-slate-700">
                
                {/* Header */}
                <div className="sticky top-0 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md px-6 py-4 border-b border-slate-100 dark:border-slate-800 flex justify-between items-center z-10">
                    <h2 className="text-xl font-bold text-slate-800 dark:text-slate-100">
                        🗺️ Your Emotional Journey
                    </h2>
                    <button 
                        onClick={onClose}
                        className="p-2 bg-slate-100 dark:bg-slate-800 rounded-full text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 transition-colors"
                    >
                        ✕
                    </button>
                </div>

                {/* Content */}
                <div className="p-6 space-y-8">
                    {loading ? (
                        <div className="animate-pulse space-y-4">
                            <div className="h-4 bg-slate-200 dark:bg-slate-800 rounded w-3/4"></div>
                            <div className="h-4 bg-slate-200 dark:bg-slate-800 rounded w-full"></div>
                            <div className="h-4 bg-slate-200 dark:bg-slate-800 rounded w-5/6"></div>
                            <div className="mt-8 h-32 bg-slate-100 dark:bg-slate-800 rounded-2xl"></div>
                        </div>
                    ) : error ? (
                        <div className="text-center text-red-500 py-8 font-medium">
                            {error}
                        </div>
                    ) : !report?.has_data ? (
                        <div className="text-center text-slate-500 py-8">
                            <p className="text-4xl mb-4">🌱</p>
                            <p>{report?.message || "Keep journaling to generate your journey report!"}</p>
                        </div>
                    ) : (
                        <div className="space-y-8 animate-slide-up">
                            {/* Summary */}
                            <section>
                                <h3 className="text-sm font-bold uppercase tracking-wider text-brand-500 mb-3">
                                    The Journey So Far
                                </h3>
                                <p className="text-slate-700 dark:text-slate-300 leading-relaxed text-sm">
                                    {report.journey_summary}
                                </p>
                            </section>

                            {/* Major Emotions Grid */}
                            <section className="grid sm:grid-cols-2 gap-4">
                                <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-2xl border border-blue-100 dark:border-blue-800/50">
                                    <p className="text-xs font-semibold text-blue-600 dark:text-blue-400 uppercase">Emotion of the Week</p>
                                    <p className="text-xl font-bold text-slate-800 dark:text-slate-100 mt-1 capitalize">{report.major_emotion_week}</p>
                                </div>
                                <div className="bg-purple-50 dark:bg-purple-900/20 p-4 rounded-2xl border border-purple-100 dark:border-purple-800/50">
                                    <p className="text-xs font-semibold text-purple-600 dark:text-purple-400 uppercase">Emotion of the Month</p>
                                    <p className="text-xl font-bold text-slate-800 dark:text-slate-100 mt-1 capitalize">{report.major_emotion_month}</p>
                                </div>
                            </section>

                            {/* Behavioral Trends */}
                            {report.behavioral_trends && report.behavioral_trends.length > 0 && (
                                <section>
                                    <h3 className="text-sm font-bold uppercase tracking-wider text-slate-500 mb-3">
                                        Observed Patterns
                                    </h3>
                                    <ul className="space-y-3">
                                        {report.behavioral_trends.map((trend, i) => (
                                            <li key={i} className="flex gap-3 text-sm text-slate-600 dark:text-slate-300">
                                                <span className="text-brand-500 shrink-0">❖</span>
                                                <span>{trend}</span>
                                            </li>
                                        ))}
                                    </ul>
                                </section>
                            )}

                            {/* Remedies */}
                            {report.remedies && report.remedies.length > 0 && (
                                <section className="bg-emerald-50 dark:bg-emerald-900/10 p-5 rounded-3xl border border-emerald-100 dark:border-emerald-800/30">
                                    <h3 className="text-sm font-bold uppercase tracking-wider text-emerald-600 dark:text-emerald-400 mb-3 flex items-center gap-2">
                                        <span>💡</span> Recommended Coping Strategies
                                    </h3>
                                    <ul className="space-y-3">
                                        {report.remedies.map((remedy, i) => (
                                            <li key={i} className="flex gap-3 text-sm text-slate-700 dark:text-slate-300">
                                                <span className="text-emerald-500 shrink-0 mt-0.5">✓</span>
                                                <span>{remedy}</span>
                                            </li>
                                        ))}
                                    </ul>
                                </section>
                            )}

                            {/* Support Statement */}
                            <section className="text-center pt-4 border-t border-slate-100 dark:border-slate-800">
                                <p className="italic text-slate-500 text-sm">
                                    "{report.system_support}"
                                </p>
                            </section>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
