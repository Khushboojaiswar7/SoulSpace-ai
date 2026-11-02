/**
 * api/chat.js
 * Provides the sendChatMessage() helper for the SoulSpace wellness chatbot.
 *
 * Endpoint: POST /api/chat
 * No JWT required for the chatbot (public endpoint).
 */

const BASE_URL = 'http://localhost:5000';

/**
 * Sends a user message to the backend chatbot and returns the bot reply.
 *
 * @param {string} message  The user's plain-text message.
 * @param {string} [token]  Optional JWT token (if backend requires auth in future).
 * @returns {Promise<string>} The bot's reply string.
 *
 * @example
 *   const reply = await sendChatMessage("I feel stressed today");
 *   // → "Sounds like you're carrying a lot right now. 🫧 ..."
 */
export async function sendChatMessage(message, token = null) {
    const headers = { 'Content-Type': 'application/json' };

    // Include Authorization header if a token is provided
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const res = await fetch(`${BASE_URL}/api/chat`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ message }),
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Chatbot is unavailable. Please try again.');
    return data.reply;  // string
}
