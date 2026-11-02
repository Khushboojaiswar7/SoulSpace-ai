/**
 * components/MoodLogger.jsx
 *
 * A self-contained mood logging widget, completely separate from the
 * journal system.  Users pick an emoji mood + a life-area tag and press
 * "Log Mood" to persist their entry via POST /api/mood.
 *
 * Props:
 *   token       {string}    - JWT token for the authenticated user
 *   onMoodLogged {Function} - Optional callback fired after a successful log
 *                             (used by Dashboard to dismiss the reminder card)
 */

import React, { useState } from "react";
import { logMood } from "../api/mood";

// ── Mood options ─────────────────────────────────────────────────────────────
const MOODS = [
    { value: "happy", emoji: "😊", label: "Happy" },
    { value: "sad", emoji: "😢", label: "Sad" },
    { value: "calm", emoji: "😌", label: "Calm" },
    { value: "angry", emoji: "😠", label: "Angry" },
    { value: "anxious", emoji: "😰", label: "Anxious" },
];

// ── Tag options ───────────────────────────────────────────────────────────────
const TAGS = [
    { value: "work", label: "💼 Work" },
    { value: "stress", label: "😓 Stress" },
    { value: "health", label: "🏃 Health" },
    { value: "relationships", label: "🤝 Relationships" },
    { value: "gratitude", label: "🙏 Gratitude" },
    { value: "goals", label: "🎯 Goals" },
];

// ── Helper: today's date as YYYY-MM-DD ────────────────────────────────────────
function todayStr() {
    return new Date().toISOString().slice(0, 10);
}

// ── Component ─────────────────────────────────────────────────────────────────
export default function MoodLogger({ token, onMoodLogged }) {
    const [selectedMood, setSelectedMood] = useState("");
    const [selectedTag, setSelectedTag] = useState("");
    const [status, setStatus] = useState(null); // { type: "success"|"error", msg }
    const [loading, setLoading] = useState(false);

    // ── Submit ──────────────────────────────────────────────────────────────
    const handleLog = async () => {
        if (!selectedMood) {
            setStatus({ type: "error", msg: "Please select a mood first." });
            return;
        }
        if (!selectedTag) {
            setStatus({ type: "error", msg: "Please choose a tag." });
            return;
        }

        setLoading(true);
        setStatus(null);

        try {
            await logMood(token, selectedMood, selectedTag);

            // Persist today's date so Dashboard knows a mood was logged
            localStorage.setItem("lastMoodDate", todayStr());

            setStatus({ type: "success", msg: "Mood logged! Keep taking care of yourself 💙" });
            setSelectedMood("");
            setSelectedTag("");

            // Notify parent (e.g. dismiss reminder card)
            if (typeof onMoodLogged === "function") onMoodLogged();

        } catch (err) {
            console.error("[MoodLogger] error:", err);
            setStatus({ type: "error", msg: err.message || "Failed to log mood." });
        } finally {
            setLoading(false);
            // Auto-clear status after 4 s
            setTimeout(() => setStatus(null), 4000);
        }
    };

    // ── Render ──────────────────────────────────────────────────────────────
    return (
        <div className="bg-white dark:bg-slate-800 rounded-3xl border border-slate-100
                        dark:border-slate-700 p-6 shadow-sm space-y-5 transition-colors">

            {/* Header */}
            <div>
                <h2 className="text-lg font-bold text-slate-800 dark:text-slate-100">
                    How are you feeling?
                </h2>
                <p className="text-xs text-slate-400 dark:text-slate-500 mt-0.5">
                    Log your mood independently from your journal.
                </p>
            </div>

            {/* Emoji mood selector */}
            <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-500
                               dark:text-slate-400 mb-2">
                    Select mood
                </p>
                <div className="flex flex-wrap gap-2">
                    {MOODS.map(({ value, emoji, label }) => {
                        const isActive = selectedMood === value;
                        return (
                            <button
                                key={value}
                                onClick={() => setSelectedMood(value)}
                                aria-pressed={isActive}
                                title={label}
                                className={`flex flex-col items-center gap-1 px-4 py-3 rounded-2xl
                                            text-sm font-medium border transition-all duration-150
                                            focus:outline-none focus:ring-2 focus:ring-brand-400
                                            ${isActive
                                        ? "bg-brand-100 dark:bg-brand-900/50 border-brand-400 dark:border-brand-500 text-brand-700 dark:text-brand-300 scale-105 shadow-sm"
                                        : "bg-slate-50 dark:bg-slate-700 border-slate-200 dark:border-slate-600 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-600"
                                    }`}
                            >
                                <span className="text-2xl leading-none">{emoji}</span>
                                <span className="text-xs">{label}</span>
                            </button>
                        );
                    })}
                </div>
            </div>

            {/* Tag dropdown */}
            <div>
                <label
                    htmlFor="mood-tag"
                    className="text-xs font-semibold uppercase tracking-wide text-slate-500
                               dark:text-slate-400 mb-2 block"
                >
                    Life area
                </label>
                <select
                    id="mood-tag"
                    value={selectedTag}
                    onChange={(e) => setSelectedTag(e.target.value)}
                    className="w-full rounded-xl border border-slate-200 dark:border-slate-600
                               bg-slate-50 dark:bg-slate-700 text-slate-700 dark:text-slate-200
                               px-4 py-2.5 text-sm focus:outline-none focus:ring-2
                               focus:ring-brand-400 transition-colors"
                >
                    <option value="">Choose a tag…</option>
                    {TAGS.map(({ value, label }) => (
                        <option key={value} value={value}>{label}</option>
                    ))}
                </select>
            </div>

            {/* Submit button */}
            <button
                onClick={handleLog}
                disabled={loading}
                className="w-full py-2.5 rounded-xl bg-brand-500 hover:bg-brand-600
                           disabled:opacity-50 disabled:cursor-not-allowed
                           text-white font-semibold text-sm transition-colors
                           focus:outline-none focus:ring-2 focus:ring-brand-400"
            >
                {loading ? "Logging…" : "Log Mood 💙"}
            </button>

            {/* Inline feedback */}
            {status && (
                <p className={`text-sm font-medium text-center animate-fade-in
                               ${status.type === "success"
                        ? "text-emerald-600 dark:text-emerald-400"
                        : "text-red-500 dark:text-red-400"
                    }`}
                >
                    {status.msg}
                </p>
            )}
        </div>
    );
}
