/**
 * api/auth.js
 * Authentication API calls: login, signup, logout
 * Base URL: http://127.0.0.1:5000/auth/<endpoint>
 */

const BASE_URL = 'http://localhost:5000';

/**
 * Registers a new user account.
 * @param {string} username
 * @param {string} email
 * @param {string} password
 * @returns {Promise<{token?: string, user?: object, error?: string}>}
 */
export async function signupUser(username, email, password) {
    const res = await fetch(`${BASE_URL}/auth/signup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, email, password }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Signup failed');
    return data; // { message, token, user }
}

/**
 * Logs in an existing user.
 * @param {string} email
 * @param {string} password
 * @returns {Promise<{token: string, user: object, message: string}>}
 */
export async function loginUser(email, password) {
    const res = await fetch(`${BASE_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Login failed');
    return data; // { message, token, user }
}

/**
 * Clears the local session. (Backend is stateless JWT, so just clear storage.)
 */
export function logoutUser() {
    localStorage.removeItem('mm_token');
    localStorage.removeItem('mm_user');
}
