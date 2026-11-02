/**
 * context/AuthContext.jsx
 * Global authentication state using React Context.
 *
 * Provides:
 *   - token        : JWT string (or null)
 *   - user         : { id, username, email } decoded from JWT (or null)
 *   - isAuthenticated : boolean
 *   - login(token, user) : saves session to state + localStorage
 *   - logout()           : clears session, redirects to /login
 */

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { logoutUser } from '../api/auth';

// ── Context creation ──────────────────────────────────────────────
const AuthContext = createContext(null);

// ── Provider component ────────────────────────────────────────────
export function AuthProvider({ children }) {
    const [token, setToken] = useState(() => localStorage.getItem('mm_token'));
    const [user, setUser] = useState(() => {
        try {
            const u = localStorage.getItem('mm_user');
            return u ? JSON.parse(u) : null;
        } catch {
            return null;
        }
    });

    // Navigate is available inside Router, but AuthProvider wraps Router,
    // so we expose logout via a plain function that components can call.
    // Components that need navigation call useNavigate themselves.

    /**
     * Called after a successful login or signup.
     * Persists the session credentials to localStorage.
     */
    const login = useCallback((newToken, newUser) => {
        localStorage.setItem('mm_token', newToken);
        localStorage.setItem('mm_user', JSON.stringify(newUser));
        setToken(newToken);
        setUser(newUser);
    }, []);

    /**
     * Clears the session. Components should navigate to /login afterwards.
     */
    const logout = useCallback(() => {
        logoutUser(); // clears localStorage
        setToken(null);
        setUser(null);
    }, []);

    // Derived convenience flag
    const isAuthenticated = Boolean(token);

    const value = { token, user, isAuthenticated, login, logout };

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
}

// ── Custom hook ───────────────────────────────────────────────────
/**
 * Convenience hook to consume auth context.
 * @returns {{ token, user, isAuthenticated, login, logout }}
 */
export function useAuth() {
    const ctx = useContext(AuthContext);
    if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>');
    return ctx;
}

export default AuthContext;
