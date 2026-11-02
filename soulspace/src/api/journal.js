/**
 * api/journal.js
 * Journal, Mood, and Analytics API calls (all require JWT token)
 * Base URL: http://127.0.0.1:5000
 */

const BASE_URL = 'http://localhost:5000';

/** Helper: builds authenticated headers */
const authHeaders = (token) => ({
    'Content-Type': 'application/json',
    Authorization: `Bearer ${token}`,
});

// ──────────────────────────────────────────────────────────────────
// MOODS
// ──────────────────────────────────────────────────────────────────

/**
 * Fetches the list of available mood options from the backend.
 * @param {string} token  JWT access token
 * @returns {Promise<Array<{id: number, label: string}>>}
 */
export async function getMoods(token) {
    const res = await fetch(`${BASE_URL}/journal/moods`, {
        headers: authHeaders(token),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Could not fetch moods');
    return data.moods; // [{ id, label }, ...]
}

// ──────────────────────────────────────────────────────────────────
// JOURNAL ENTRIES
// ──────────────────────────────────────────────────────────────────

/**
 * Creates a new journal entry.
 * @param {string} token
 * @param {{ title?: string, content: string, mood_id?: number }} payload
 * @returns {Promise<{message: string, entry: object}>}
 */
export async function createJournalEntry(token, payload) {
    const res = await fetch(`${BASE_URL}/journal/`, {
        method: 'POST',
        headers: authHeaders(token),
        body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Could not save entry');
    return data; // { message, entry }
}

/**
 * Retrieves all journal entries for the logged-in user (newest first).
 * @param {string} token
 * @returns {Promise<Array>}
 */
export async function getJournalEntries(token) {
    const res = await fetch(`${BASE_URL}/journal/`, {
        headers: authHeaders(token),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Could not fetch entries');
    return data.entries; // [{ id, title, content, mood_id, created_at }, ...]
}

/**
 * Deletes a journal entry by ID.
 * @param {string} token
 * @param {number} entryId
 * @returns {Promise<{message: string}>}
 */
export async function deleteJournalEntry(token, entryId) {
    const res = await fetch(`${BASE_URL}/journal/${entryId}`, {
        method: 'DELETE',
        headers: authHeaders(token),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Could not delete entry');
    return data;
}

// ──────────────────────────────────────────────────────────────────
// ANALYTICS
// ──────────────────────────────────────────────────────────────────

/**
 * Fetches mood trend data for charts.
 * @param {string} token
 * @param {7|30} days  Period to analyse
 * @returns {Promise<{period_days, mood_counts, daily_trend, source}>}
 */
export async function getMoodTrends(token, days = 7) {
    const res = await fetch(`${BASE_URL}/analytics/mood-trends?days=${days}`, {
        headers: authHeaders(token),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Could not fetch mood trends');
    return data;
}

/**
 * Fetches weekly + monthly summary and motivational tip.
 * @param {string} token
 * @returns {Promise<{weekly, monthly, tip}>}
 */
export async function getAnalyticsSummary(token) {
    const res = await fetch(`${BASE_URL}/analytics/summary`, {
        headers: authHeaders(token),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Could not fetch summary');
    return data;
}

/**
 * Fetches the user's current journalling streak.
 * @param {string} token
 * @returns {Promise<{streak_days: number, message: string}>}
 */
export async function getStreak(token) {
    const res = await fetch(`${BASE_URL}/analytics/streak`, {
        headers: authHeaders(token),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Could not fetch streak');
    return data;
}

// ──────────────────────────────────────────────────────────────────
// AI INSIGHTS (new endpoints from the agentic AI pipeline)
// ──────────────────────────────────────────────────────────────────

/**
 * Fetches the emotional timeline — time-series of AI-analyzed emotions.
 * @param {string} token
 * @param {number} limit  Number of data points (default: 30)
 * @returns {Promise<{timeline: Array}>}
 */
export async function getEmotionalTimeline(token, limit = 30) {
    const res = await fetch(`${BASE_URL}/insights/timeline?limit=${limit}`, {
        headers: authHeaders(token),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Could not fetch timeline');
    return data;
}

/**
 * Fetches approved emotional patterns from the Memory Agent.
 * @param {string} token
 * @returns {Promise<{patterns: object, has_patterns: boolean}>}
 */
export async function getPatterns(token) {
    const res = await fetch(`${BASE_URL}/insights/patterns`, {
        headers: authHeaders(token),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Could not fetch patterns');
    return data;
}

/**
 * Fetches the latest AI-generated reflection (Disclosure Agent output).
 * @param {string} token
 * @returns {Promise<{reflection: object, has_reflection: boolean}>}
 */
export async function getReflection(token) {
    const res = await fetch(`${BASE_URL}/insights/reflection`, {
        headers: authHeaders(token),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Could not fetch reflection');
    return data;
}

/**
 * Fetches the Comprehensive Emotional Journey Report (analyzes all history).
 * @param {string} token
 * @returns {Promise<{report: object}>}
 */
export async function getJourneyReport(token) {
    const res = await fetch(`${BASE_URL}/insights/journey-report`, {
        headers: authHeaders(token),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Could not fetch journey report');
    return data;
}

/**
 * Fetches the current user's profile flags (e.g. is_study_participant).
 * Used to gate features that are excluded from the research study's safety claims.
 * @param {string} token
 * @returns {Promise<{is_study_participant: boolean}>}
 */
export async function getUserProfile(token) {
    const res = await fetch(`${BASE_URL}/insights/me`, {
        headers: authHeaders(token),
    });
    const data = await res.json();
    // Default to false on error — never block the UI unexpectedly
    if (!res.ok) return { is_study_participant: false };
    return data;
}
