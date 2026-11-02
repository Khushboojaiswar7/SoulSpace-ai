/**
 * pages/Dashboard.jsx
 * Protected main dashboard. Fetches real data from the backend:
 *   - Streak        from GET /analytics/streak
 *   - Summary       from GET /analytics/summary
 *   - Mood trends   from GET /analytics/mood-trends
 *   - Journal list  from GET /journal/
 *   - Moods list    from GET /journal/moods  (for JournalForm)
 */

import React, { useEffect, useState, useCallback } from 'react';
import Navbar from '../components/Navbar';
import JournalForm from '../components/JournalForm';
import ChartView from '../components/ChartView';
import MoodLogger from '../components/MoodLogger';
import JourneyReportModal from '../components/JourneyReportModal';
import { useAuth } from '../context/AuthContext';
import {
    getMoods,
    getJournalEntries,
    getMoodTrends,
    getAnalyticsSummary,
    getStreak,
    deleteJournalEntry,
    getEmotionalTimeline,
    getPatterns,
    getReflection,
    getUserProfile,
} from '../api/journal';

// ── Small stat card ─────────────────────────────────────────────
function StatCard({ icon, label, value, sub, colorClass }) {
    return (
        <div className={`rounded-3xl p-5 flex flex-col gap-1 ${colorClass} transition-colors`}>
            <span className="text-3xl">{icon}</span>
            <p className="text-xs font-semibold uppercase tracking-wide opacity-70 mt-1">{label}</p>
            <p className="text-2xl font-bold">{value ?? '–'}</p>
            {sub && <p className="text-xs opacity-60">{sub}</p>}
        </div>
    );
}

// ── Recent journal entry card ────────────────────────────────────
function EntryCard({ entry, onDelete }) {
    const [confirming, setConfirming] = useState(false);

    const date = entry.created_at
        ? new Date(entry.created_at).toLocaleDateString('en-US', {
            weekday: 'short', month: 'short', day: 'numeric',
        })
        : '';

    return (
        <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-100 dark:border-slate-700 p-5 shadow-sm flex flex-col gap-2 animate-fade-in transition-colors">
            <div className="flex items-start justify-between gap-2">
                <div>
                    {entry.title && (
                        <h3 className="font-semibold text-slate-800 dark:text-slate-100 text-sm">{entry.title}</h3>
                    )}
                    <p className="text-xs text-slate-400">{date}</p>
                </div>
                {confirming ? (
                    <div className="flex gap-2 shrink-0">
                        <button
                            onClick={() => onDelete(entry.id)}
                            className="text-xs text-red-500 font-semibold hover:underline"
                        >
                            Confirm
                        </button>
                        <button
                            onClick={() => setConfirming(false)}
                            className="text-xs text-slate-400 hover:underline"
                        >
                            Cancel
                        </button>
                    </div>
                ) : (
                    <button
                        onClick={() => setConfirming(true)}
                        aria-label="Delete entry"
                        className="text-slate-300 hover:text-red-400 transition-colors text-lg leading-none shrink-0"
                    >
                        ✕
                    </button>
                )}
            </div>
            <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed line-clamp-3">
                {entry.content}
            </p>
        </div>
    );
}

// ── Main Dashboard ───────────────────────────────────────────────
export default function Dashboard() {
    const { token, user } = useAuth();

    // Data state
    const [moods, setMoods] = useState([]);
    const [entries, setEntries] = useState([]);
    const [trends, setTrends] = useState(null);
    const [summary, setSummary] = useState(null);
    const [streak, setStreak] = useState(null);

    // AI Insights state
    const [timeline, setTimeline] = useState([]);
    const [patterns, setPatterns] = useState(null);
    const [reflection, setReflection] = useState(null);

    // UI state
    const [loadingData, setLoadingData] = useState(true);
    const [loadChart, setLoadChart] = useState(true);
    const [banner, setBanner] = useState(null); // { type, msg }

    // ── Reminder state (Part 2) ──────────────────────────────────────────
    // showReminder: true when user hasn't logged mood today
    const [showReminder, setShowReminder] = useState(false);
    
    // Journey Report state
    const [showReport, setShowReport] = useState(false);
    
    // Study-participant gate: if true, hide Journey Report button (supplementary to server-side 403).
    const [isStudyParticipant, setIsStudyParticipant] = useState(false);

    // ── Fetch everything ────────────────────────────────────────────
    const fetchAll = useCallback(async () => {
        if (!token) return;
        setLoadingData(true);
        setLoadChart(true);
        setBanner(null);

        try {
            const [moodsData, entriesData, trendsData, summaryData, streakData,
                   timelineData, patternsData, reflectionData, profileData] =
                await Promise.allSettled([
                    getMoods(token),
                    getJournalEntries(token),
                    getMoodTrends(token, 7),
                    getAnalyticsSummary(token),
                    getStreak(token),
                    getEmotionalTimeline(token),
                    getPatterns(token),
                    getReflection(token),
                    getUserProfile(token),   // ← study-participant flag
                ]);

            if (moodsData.status === 'fulfilled') { setMoods(moodsData.value || []); }
            else { console.error('Moods error:', moodsData.reason); }
            if (entriesData.status === 'fulfilled') { setEntries(entriesData.value || []); }
            else { console.error('Entries error:', entriesData.reason); }
            if (trendsData.status === 'fulfilled') { setTrends(trendsData.value || {}); }
            else { console.error('Trends error:', trendsData.reason); }
            if (summaryData.status === 'fulfilled') { setSummary(summaryData.value || {}); }
            else { console.error('Summary error:', summaryData.reason); }
            if (streakData.status === 'fulfilled') { setStreak(streakData.value || {}); }
            else { console.error('Streak error:', streakData.reason); }
            if (timelineData.status === 'fulfilled') { setTimeline(timelineData.value?.timeline || []); }
            else { console.error('Timeline error:', timelineData.reason); }
            if (patternsData.status === 'fulfilled') { setPatterns(patternsData.value || null); }
            else { console.error('Patterns error:', patternsData.reason); }
            if (reflectionData.status === 'fulfilled') { setReflection(reflectionData.value || null); }
            else { console.error('Reflection error:', reflectionData.reason); }
            // Study-participant flag — defaults to false on error to avoid blocking the UI
            if (profileData.status === 'fulfilled') {
                setIsStudyParticipant(profileData.value?.is_study_participant ?? false);
            }
        } catch (error) {
            console.error('Unexpected fetch error:', error);
            setBanner({ type: 'error', msg: 'Failed to load dashboard data.' });
        } finally {
            setLoadingData(false);
            setLoadChart(false);
        }
    }, [token]);

    useEffect(() => { fetchAll(); }, [fetchAll]);
    useEffect(() => {
        if (!token) {
            setEntries([]);
            setMoods([]);
            setTrends(null);
            setSummary(null);
            setStreak(null);
        }
    }, [token]);

    // ── Mood reminder effect (Part 2) ────────────────────────────────────
    // Runs once on mount.  If the user hasn't logged mood today:
    //   - shows the reminder card immediately
    //   - after 5 s fires a browser Notification (if permission granted)
    useEffect(() => {
        const todayStr = () => new Date().toISOString().slice(0, 10);
        const lastDate = localStorage.getItem('lastMoodDate');

        if (lastDate === todayStr()) return;  // Already logged today – nothing to do

        // Show the in-page reminder card
        setShowReminder(true);

        // Schedule browser notification after 5 seconds
        const timerId = setTimeout(() => {
            if (!('Notification' in window)) return;  // Browser doesn't support it

            const fire = () => {
                // eslint-disable-next-line no-new
                new Notification('SoulSpace Reminder 💙', {
                    body: "Don't forget to log your mood today!",
                    icon: '/favicon.ico',
                });
            };

            if (Notification.permission === 'granted') {
                fire();
            } else if (Notification.permission !== 'denied') {
                Notification.requestPermission().then((perm) => {
                    if (perm === 'granted') fire();
                });
            }
        }, 5000);

        return () => clearTimeout(timerId);  // Cleanup if component unmounts early
    }, []); // Run only once on mount

    // ── Delete entry ────────────────────────────────────────────────
    const handleDelete = async (id) => {
        try {
            await deleteJournalEntry(token, id);
            setEntries((prev) => prev.filter((e) => e.id !== id));
            setBanner({ type: 'success', msg: 'Entry deleted successfully.' });
            setTimeout(() => setBanner(null), 3000);
        } catch (err) {
            console.error('Delete failed:', err);
            setBanner({ type: 'error', msg: err.message || 'Failed to delete entry.', });
            setTimeout(() => setBanner(null), 4000);
        }
    };

    // Derived values from summary
    const weeklyEntries = summary?.weekly?.entries ?? 0;
    const monthlyEntries = summary?.monthly?.entries ?? 0;
    const topMood = summary?.weekly?.top_mood ?? '–';
    const avgScore = summary?.weekly?.avg_mood_score ?? null;
    const tip = summary?.tip ?? null;
    const streakDays = streak?.streak_days ?? null;

    // AI-enriched derived values
    const primaryEmotion = summary?.weekly?.primary_emotion ?? null;
    const stressTrend = summary?.weekly?.stress_trend ?? null;
    const recurringThemes = summary?.recurring_themes ?? [];
    const emotionalGrowth = summary?.emotional_growth ?? [];

    return (
        <div className="min-h-screen bg-slate-50 dark:bg-slate-950 transition-colors">
            <Navbar />

            <main className="max-w-5xl mx-auto px-4 sm:px-6 py-8 space-y-8">

                {/* Welcome header */}
                <section className="animate-fade-in">
                    <h1 className="text-3xl font-bold text-slate-800 dark:text-slate-100">
                        Hey, {user?.username || 'there'} 👋
                    </h1>
                    <p className="text-slate-500 dark:text-slate-400 mt-1">
                        {new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })}
                    </p>
                </section>

                {/* ── Part 2: Reminder card ─────────────────────────────── */}
                {showReminder && (
                    <div className="flex items-start gap-4 px-5 py-4 rounded-2xl
                                   bg-blue-50 dark:bg-blue-900/30
                                   border border-blue-200 dark:border-blue-700
                                   text-blue-700 dark:text-blue-300
                                   animate-slide-up">
                        <span className="text-2xl shrink-0" aria-hidden="true">🔔</span>
                        <div className="flex-1">
                            <p className="font-semibold text-sm">SoulSpace Reminder</p>
                            <p className="text-xs mt-0.5 opacity-80">
                                You haven’t logged your mood yet today. Log it below!
                            </p>
                        </div>
                        <button
                            onClick={() => setShowReminder(false)}
                            aria-label="Dismiss reminder"
                            className="text-blue-400 hover:text-blue-600 dark:hover:text-blue-200
                                       transition-colors text-lg leading-none shrink-0"
                        >
                            ✕
                        </button>
                    </div>
                )}

                {/* Global feedback banner */}
                {banner && (
                    <div className={`px-4 py-3 rounded-2xl text-sm font-medium animate-slide-up ${banner.type === 'success'
                        ? 'bg-emerald-50 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800'
                        : 'bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-300 border border-red-200 dark:border-red-800'
                        }`}>
                        {banner.msg}
                    </div>
                )}

                {/* Motivational tip */}
                {tip && (
                    <div className="bg-brand-50 dark:bg-brand-950/40 border border-brand-200 dark:border-brand-800 rounded-2xl px-5 py-4 text-brand-700 dark:text-brand-300 text-sm font-medium animate-fade-in">
                        💜 {tip}
                    </div>
                )}

                {/* Stat cards — enhanced with AI pipeline data */}
                <section className="grid grid-cols-2 sm:grid-cols-4 gap-4 animate-fade-in">
                    <StatCard icon="🔥" label="Streak" value={streakDays ? `${streakDays}d` : '-'} colorClass="bg-pastel-pink dark:bg-red-900/30 text-slate-800 dark:text-slate-100" />
                    <StatCard icon="📔" label="This week" value={weeklyEntries} colorClass="bg-pastel-yellow dark:bg-amber-900/30 text-slate-800 dark:text-slate-100" />
                    <StatCard icon="🎯" label="Primary Emotion" value={primaryEmotion || topMood} sub={primaryEmotion ? 'AI detected' : ''} colorClass="bg-pastel-green dark:bg-emerald-900/30 text-slate-800 dark:text-slate-100" />
                    <StatCard icon="📈" label="Stress Trend" value={stressTrend || '–'} sub="this week" colorClass="bg-pastel-lavender dark:bg-brand-900/30 text-slate-800 dark:text-slate-100" />
                </section>

                {/* MoodLogger */}
                <section>
                    <MoodLogger
                        token={token}
                        onMoodLogged={() => setShowReminder(false)}
                    />
                </section>

                {/* Journal form + Chart */}
                <section className="grid lg:grid-cols-2 gap-6">
                    <JournalForm
                        token={token}
                        moods={moods}
                        onSaved={fetchAll}
                    />
                    <ChartView
                        moodCounts={trends?.mood_counts ?? {}}
                        dailyTrend={trends?.daily_trend ?? []}
                        emotionalTimeline={timeline}
                        loading={loadChart}
                    />
                </section>

                {/* ── AI Insights Section ─────────────────────────────── */}
                <section className="space-y-6 animate-fade-in mt-8">
                    <div className="flex items-center justify-between">
                        <h2 className="text-lg font-bold text-slate-800 dark:text-slate-100 flex items-center gap-2">
                            🧠 AI Insights
                        </h2>
                        {/* Generate Journey Report button — hidden for study participants.
                            NOTE: This is a UX convenience only. The authoritative enforcement
                            is the server-side 403 check in GET /insights/journey-report. */}
                        {!isStudyParticipant && (
                            <button
                                onClick={() => setShowReport(true)}
                                className="text-sm font-semibold text-brand-600 bg-brand-50 hover:bg-brand-100 dark:text-brand-300 dark:bg-brand-900/30 dark:hover:bg-brand-900/50 px-4 py-2 rounded-full transition-colors flex items-center gap-2"
                            >
                                🗺️ Generate Journey Report
                            </button>
                        )}
                    </div>

                    {(recurringThemes.length > 0 || emotionalGrowth.length > 0 || patterns?.has_patterns) && (
                        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
                            {/* Recurring Themes */}
                            {recurringThemes.length > 0 && (
                                <div className="bg-white dark:bg-slate-800 rounded-3xl border border-slate-100 dark:border-slate-700 p-5 shadow-sm">
                                    <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-200 mb-3 flex items-center gap-2">
                                        🔄 Recurring Themes
                                    </h3>
                                    <div className="flex flex-wrap gap-2">
                                        {recurringThemes.map((theme, i) => (
                                            <span key={i} className="px-3 py-1 bg-brand-50 dark:bg-brand-900/30 text-brand-700 dark:text-brand-300 rounded-full text-xs font-medium">
                                                {theme}
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Emotional Growth */}
                            {emotionalGrowth.length > 0 && (
                                <div className="bg-white dark:bg-slate-800 rounded-3xl border border-slate-100 dark:border-slate-700 p-5 shadow-sm">
                                    <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-200 mb-3 flex items-center gap-2">
                                        🌱 Emotional Growth
                                    </h3>
                                    <ul className="space-y-2">
                                        {emotionalGrowth.map((item, i) => (
                                            <li key={i} className="flex items-start gap-2 text-xs text-slate-600 dark:text-slate-300">
                                                <span className="text-emerald-500 mt-0.5">✓</span>
                                                {item}
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            )}

                            {/* Common Triggers (from patterns) */}
                            {patterns?.has_patterns && patterns?.patterns?.recurring_stressors?.length > 0 && (
                                <div className="bg-white dark:bg-slate-800 rounded-3xl border border-slate-100 dark:border-slate-700 p-5 shadow-sm">
                                    <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-200 mb-3 flex items-center gap-2">
                                        ⚡ Common Triggers
                                    </h3>
                                    <div className="flex flex-wrap gap-2">
                                        {patterns.patterns.recurring_stressors.map((trigger, i) => (
                                            <span key={i} className="px-3 py-1 bg-amber-50 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300 rounded-full text-xs font-medium">
                                                {trigger}
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    )}

                    {/* AI Reflection Summary */}
                    {reflection?.has_reflection && reflection?.reflection?.text && (
                        <div className="bg-gradient-to-r from-brand-50 via-white to-pastel-lavender/40 dark:from-brand-950/40 dark:via-slate-800 dark:to-brand-900/20 rounded-3xl border border-brand-200 dark:border-brand-800 p-6 shadow-sm">
                            <h3 className="text-sm font-semibold text-brand-700 dark:text-brand-300 mb-3 flex items-center gap-2">
                                🪞 AI Reflection
                            </h3>
                            <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed">
                                {reflection.reflection.text}
                            </p>
                            <p className="text-xs text-slate-400 mt-3">
                                Based on your recent journal entries • AI-generated with uncertainty
                            </p>
                        </div>
                    )}
                </section>

                {/* Recent journal entries */}
                <section>
                    <div className="flex items-center justify-between mb-4">
                        <h2 className="text-lg font-bold text-slate-800 dark:text-slate-100">
                            Recent Entries
                        </h2>
                        <span className="text-sm text-slate-400">
                            {entries.length} total • {monthlyEntries} this month
                        </span>
                    </div>

                    {loadingData ? (
                        <div className="grid sm:grid-cols-2 gap-4">
                            {[1, 2].map((i) => (
                                <div key={i} className="animate-pulse bg-slate-100 dark:bg-slate-800 rounded-2xl h-28" />
                            ))}
                        </div>
                    ) : entries.length === 0 ? (
                        <div className="text-center py-16 text-slate-400 dark:text-slate-500">
                            <p className="text-4xl mb-3">📖</p>
                            <p className="font-medium">No entries yet.</p>
                            <p className="text-sm mt-1">Write your first journal entry above!</p>
                        </div>
                    ) : (
                        <div className="grid sm:grid-cols-2 gap-4">
                            {entries.slice(0, 10).map((entry) => (
                                <EntryCard
                                    key={entry.id}
                                    entry={entry}
                                    onDelete={handleDelete}
                                />
                            ))}
                        </div>
                    )}
                </section>

            </main>

            {/* Journey Report Modal */}
            {showReport && (
                <JourneyReportModal
                    token={token}
                    onClose={() => setShowReport(false)}
                />
            )}

            {/* Footer */}
            <footer className="text-center py-6 text-xs text-slate-400 dark:text-slate-600 border-t border-slate-100 dark:border-slate-800 mt-8">
                © 2025 SoulSpace — Made with 💜
            </footer>
        </div>
    );
}
