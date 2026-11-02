/**
 * components/JournalForm.jsx
 * Full journal entry form: mood picker + tags + title + content.
 * Submits to /journal/ endpoint with JWT auth.
 *
 * After a successful save the AI suggestion returned by the backend
 * is displayed in a styled, animated suggestion box below the form.
 *
 * Props:
 *   token    {string}          – JWT token from AuthContext
 *   moods    {Array}           – mood list from API
 *   onSaved  {() => void}      – callback after successful save (to refresh list)
 */

import React, { useState } from 'react';
import MoodSelector from './MoodSelector';
import { createJournalEntry } from '../api/journal';

const TAGS = ['stress', 'work', 'health', 'relationships', 'gratitude', 'goals'];

export default function JournalForm({ token, moods, onSaved }) {
    const [selectedMood, setSelectedMood] = useState(null);   // { id, label, emoji }
    const [activeTags, setActiveTags] = useState([]);
    const [title, setTitle] = useState('');
    const [content, setContent] = useState('');
    const [loading, setLoading] = useState(false);
    const [banner, setBanner] = useState(null);   // { type: 'success'|'error', msg }

    // AI suggestion returned by the backend after each successful save
    const [suggestion, setSuggestion] = useState(null);   // string | null
    const [showSuggestion, setShowSuggestion] = useState(false);

    const toggleTag = (tag) =>
        setActiveTags((prev) =>
            prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag]
        );

    /**
     * handleJournalSubmit
     * Submits the journal entry, captures the API response, and surfaces
     * the AI suggestion if the backend returns one.
     */
    const handleJournalSubmit = async (e) => {
        e.preventDefault();
        setBanner(null);
        setSuggestion(null);
        setShowSuggestion(false);

        if (!content.trim()) {
            setBanner({ type: 'error', msg: 'Please write something before saving.' });
            return;
        }

        // Build tags prefix to prepend to content
        const tagPrefix = activeTags.length
            ? `[Tags: ${activeTags.join(', ')}]\n`
            : '';

        setLoading(true);
        try {
            // createJournalEntry now returns the full API response including suggestion
            const data = await createJournalEntry(token, {
                title: title.trim() || undefined,
                content: tagPrefix + content.trim(),
                mood_id: selectedMood?.id ?? undefined,
            });

            setBanner({ type: 'success', msg: '✨ Entry saved successfully!' });

            // Show suggestion box if backend returned one
            if (data.suggestion) {
                setSuggestion(data.suggestion);
                // Small delay so the success banner appears first, then suggestion fades in
                setTimeout(() => setShowSuggestion(true), 300);
            }

            // Reset form fields
            setSelectedMood(null);
            setActiveTags([]);
            setTitle('');
            setContent('');
            onSaved?.();
        } catch (err) {
            setBanner({ type: 'error', msg: err.message || 'Could not save entry.' });
        } finally {
            setLoading(false);
            // Auto-dismiss success banner after 3 s (suggestion box stays)
            setTimeout(() => setBanner(null), 3000);
        }
    };

    return (
        <div>
            {/* ── Journal entry form ───────────────────────────────────────── */}
            <form
                onSubmit={handleJournalSubmit}
                className="bg-white dark:bg-slate-800 rounded-3xl shadow-sm border border-slate-100 dark:border-slate-700 p-6 transition-colors animate-fade-in"
            >
                <h2 className="text-lg font-bold text-slate-800 dark:text-slate-100 mb-5">
                    📝 New Journal Entry
                </h2>

                {/* Mood selector */}
                <div className="mb-5">
                    <MoodSelector
                        selectedMoodId={selectedMood?.id ?? null}
                        onSelect={setSelectedMood}
                        moods={moods}
                    />
                </div>

                {/* Tags */}
                <div className="mb-5">
                    <p className="text-sm font-semibold text-slate-600 dark:text-slate-400 mb-2 uppercase tracking-wide">
                        Topics (optional)
                    </p>
                    <div className="flex flex-wrap gap-2">
                        {TAGS.map((tag) => {
                            const active = activeTags.includes(tag);
                            return (
                                <button
                                    key={tag}
                                    type="button"
                                    onClick={() => toggleTag(tag)}
                                    className={`px-3 py-1 rounded-full text-sm font-medium border transition-all ${active
                                        ? 'bg-brand-500 text-white border-brand-500 shadow-sm'
                                        : 'bg-transparent text-slate-500 dark:text-slate-400 border-slate-300 dark:border-slate-600 hover:border-brand-400'
                                        }`}
                                >
                                    {tag}
                                </button>
                            );
                        })}
                    </div>
                </div>

                {/* Title field */}
                <div className="mb-4">
                    <input
                        type="text"
                        value={title}
                        onChange={(e) => setTitle(e.target.value)}
                        placeholder="Title (optional)"
                        className="w-full rounded-2xl border border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-700 px-4 py-3 text-slate-800 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-400 transition-colors"
                    />
                </div>

                {/* Content textarea */}
                <div className="mb-5">
                    <textarea
                        value={content}
                        onChange={(e) => setContent(e.target.value)}
                        rows={5}
                        placeholder="What's on your mind today? Take your time…"
                        required
                        className="w-full rounded-2xl border border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-700 px-4 py-3 text-slate-800 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-400 resize-none transition-colors"
                    />
                </div>

                {/* Feedback banner */}
                {banner && (
                    <div
                        className={`mb-4 px-4 py-3 rounded-2xl text-sm font-medium animate-slide-up ${banner.type === 'success'
                                ? 'bg-emerald-50 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800'
                                : 'bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-300 border border-red-200 dark:border-red-800'
                            }`}
                    >
                        {banner.msg}
                    </div>
                )}

                {/* Submit */}
                <button
                    type="submit"
                    disabled={loading}
                    className="w-full py-3 rounded-2xl bg-brand-500 hover:bg-brand-600 disabled:opacity-50 text-white font-semibold text-sm transition-all shadow-sm hover:shadow-md active:scale-95"
                >
                    {loading ? 'Saving…' : 'Save Entry ✨'}
                </button>
            </form>

            {/* ── AI Suggestion Box ────────────────────────────────────────── */}
            {/*
                Hidden by default (suggestion = null).
                Fades in with a smooth transition once the backend returns
                a suggestion after a successful journal submission.
            */}
            {suggestion && (
                <div
                    className={`mt-4 transition-all duration-700 ease-out ${showSuggestion
                            ? 'opacity-100 translate-y-0'
                            : 'opacity-0 translate-y-3'
                        }`}
                >
                    <div className="
                        relative overflow-hidden
                        bg-gradient-to-br from-violet-50 to-indigo-50
                        dark:from-violet-900/30 dark:to-indigo-900/30
                        border border-violet-200 dark:border-violet-700/50
                        rounded-3xl p-5 shadow-sm
                    ">
                        {/* Decorative accent bar */}
                        <div className="absolute top-0 left-0 w-1 h-full bg-gradient-to-b from-violet-400 to-indigo-500 rounded-l-3xl" />

                        {/* Header */}
                        <div className="flex items-center gap-2 mb-3 pl-3">
                            <span className="text-xl" aria-hidden="true">🧠</span>
                            <h3 className="text-sm font-bold uppercase tracking-widest text-violet-700 dark:text-violet-300">
                                AI Suggestion
                            </h3>
                        </div>

                        {/* Suggestion text */}
                        <p className="pl-3 text-sm leading-relaxed text-slate-700 dark:text-slate-200">
                            {suggestion}
                        </p>

                        {/* Dismiss button */}
                        <button
                            onClick={() => { setSuggestion(null); setShowSuggestion(false); }}
                            className="mt-4 ml-3 text-xs text-violet-500 dark:text-violet-400 hover:text-violet-700 dark:hover:text-violet-200 transition-colors"
                            aria-label="Dismiss suggestion"
                        >
                            Dismiss ✕
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}
