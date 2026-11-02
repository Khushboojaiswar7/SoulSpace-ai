/**
 * components/MoodSelector.jsx
 * Emoji-based mood picker. Controlled component.
 *
 * Props:
 *   selectedMoodId  {number|null}  – currently selected mood id
 *   onSelect        {(mood) => void} – called with { id, label, emoji }
 *   moods           {Array}         – [{ id, label }] from API, optional
 */

import React from 'react';

// Default mood set (used if backend moods haven't loaded yet)
const DEFAULT_MOODS = [
    { id: 1, label: 'Happy', emoji: '😊' },
    { id: 2, label: 'Calm', emoji: '😌' },
    { id: 3, label: 'Anxious', emoji: '😟' },
    { id: 4, label: 'Sad', emoji: '😢' },
    { id: 5, label: 'Angry', emoji: '😤' },
    { id: 6, label: 'Excited', emoji: '🤩' },
];

// Maps mood labels → emojis (for backend-provided labels)
const EMOJI_MAP = {
    Happy: '😊',
    Calm: '😌',
    Anxious: '😟',
    Sad: '😢',
    Angry: '😤',
    Excited: '🤩',
};

export default function MoodSelector({ selectedMoodId, onSelect, moods }) {
    // Merge API moods (which have id+label) with emoji mapping
    const resolvedMoods = moods?.length
        ? moods.map((m) => ({ ...m, emoji: EMOJI_MAP[m.label] || '💭' }))
        : DEFAULT_MOODS;

    return (
        <div>
            <p className="text-sm font-semibold text-slate-600 dark:text-slate-400 mb-3 uppercase tracking-wide">
                How are you feeling?
            </p>
            <div className="flex flex-wrap gap-3">
                {resolvedMoods.map((mood) => {
                    const isActive = selectedMoodId === mood.id;
                    return (
                        <button
                            key={mood.id}
                            type="button"
                            onClick={() => onSelect(mood)}
                            aria-pressed={isActive}
                            className={`
                flex flex-col items-center gap-1 px-4 py-3 rounded-2xl border-2 font-medium text-sm
                transition-all duration-200 select-none focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500
                ${isActive
                                    ? 'border-brand-500 bg-brand-50 dark:bg-brand-900/40 text-brand-700 dark:text-brand-300 scale-105 shadow-md'
                                    : 'border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:border-brand-300 hover:scale-105 hover:shadow-sm'
                                }
              `}
                        >
                            <span className="text-2xl">{mood.emoji}</span>
                            <span>{mood.label}</span>
                        </button>
                    );
                })}
            </div>
        </div>
    );
}
