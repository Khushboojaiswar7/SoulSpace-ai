// src/api/mood.js
// API helper for standalone mood logging.
// Calls POST /api/mood – completely separate from the journal API.

const API_BASE_URL = "http://localhost:5000";

/**
 * Log a mood + tag for the currently authenticated user.
 *
 * @param {string} token - JWT from localStorage
 * @param {string} mood  - One of: happy, sad, calm, angry, anxious
 * @param {string} tag   - One of: work, stress, health, relationships, gratitude, goals
 * @returns {Promise<object>} The created mood_log object from the server
 * @throws {Error} If the request fails or the server returns an error
 */
export async function logMood(token, mood, tag) {
    const response = await fetch(`${API_BASE_URL}/api/mood`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ mood, tag }),
    });

    const result = await response.json();

    if (!response.ok) {
        throw new Error(result.error || "Failed to log mood");
    }

    return result;
}
