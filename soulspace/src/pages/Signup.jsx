/**
 * pages/Signup.jsx
 * Signup form page. Calls /auth/signup, stores JWT, redirects to /dashboard.
 */

import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { signupUser } from '../api/auth';
import { useAuth } from '../context/AuthContext';

export default function Signup() {
    const navigate = useNavigate();
    const { login } = useAuth();

    const [username, setUsername] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [confirm, setConfirm] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');

        // Client-side validations
        if (!username.trim() || !email.trim() || !password) {
            setError('All fields are required.');
            return;
        }
        if (password.length < 6) {
            setError('Password must be at least 6 characters.');
            return;
        }
        if (password !== confirm) {
            setError('Passwords do not match.');
            return;
        }

        setLoading(true);
        try {
            const data = await signupUser(username.trim(), email.trim().toLowerCase(), password);
            login(data.token, data.user);  // save session
            navigate('/dashboard');
        } catch (err) {
            setError(err.message || 'Signup failed. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-brand-50 via-white to-pastel-lavender/40 dark:from-slate-950 dark:via-slate-900 dark:to-slate-800 px-4 transition-colors">
            <div className="w-full max-w-md animate-slide-up">

                {/* Card */}
                <div className="bg-white dark:bg-slate-800 rounded-4xl shadow-xl border border-slate-100 dark:border-slate-700 p-8">

                    {/* Branding */}
                    <div className="text-center mb-8">
                        <div className="text-5xl mb-3">🌱</div>
                        <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100">
                            Start your journey
                        </h1>
                        <p className="text-slate-500 dark:text-slate-400 text-sm mt-1">
                            Create your free SoulSpace account
                        </p>
                    </div>

                    {/* Error banner */}
                    {error && (
                        <div className="mb-5 px-4 py-3 rounded-2xl bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-300 text-sm font-medium animate-fade-in">
                            {error}
                        </div>
                    )}

                    {/* Form */}
                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div>
                            <label className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide block mb-1">
                                Username
                            </label>
                            <input
                                id="signup-username"
                                type="text"
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                placeholder="e.g. mindful_alice"
                                autoComplete="username"
                                required
                                className="w-full rounded-2xl border border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-700 px-4 py-3 text-slate-800 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-400 transition-colors"
                            />
                        </div>

                        <div>
                            <label className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide block mb-1">
                                Email
                            </label>
                            <input
                                id="signup-email"
                                type="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                placeholder="you@example.com"
                                autoComplete="email"
                                required
                                className="w-full rounded-2xl border border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-700 px-4 py-3 text-slate-800 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-400 transition-colors"
                            />
                        </div>

                        <div>
                            <label className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide block mb-1">
                                Password
                            </label>
                            <input
                                id="signup-password"
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                placeholder="Min. 6 characters"
                                autoComplete="new-password"
                                required
                                className="w-full rounded-2xl border border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-700 px-4 py-3 text-slate-800 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-400 transition-colors"
                            />
                        </div>

                        <div>
                            <label className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide block mb-1">
                                Confirm Password
                            </label>
                            <input
                                id="signup-confirm"
                                type="password"
                                value={confirm}
                                onChange={(e) => setConfirm(e.target.value)}
                                placeholder="••••••••"
                                autoComplete="new-password"
                                required
                                className="w-full rounded-2xl border border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-700 px-4 py-3 text-slate-800 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-400 transition-colors"
                            />
                        </div>

                        <button
                            type="submit"
                            id="signup-submit"
                            disabled={loading}
                            className="w-full py-3 mt-2 rounded-2xl bg-brand-500 hover:bg-brand-600 disabled:opacity-60 text-white font-semibold transition-all shadow-sm hover:shadow-md active:scale-95"
                        >
                            {loading ? 'Creating account…' : 'Create Account 🌱'}
                        </button>
                    </form>

                    {/* Footer link */}
                    <p className="text-center text-sm text-slate-500 dark:text-slate-400 mt-6">
                        Already have an account?{' '}
                        <Link
                            to="/login"
                            className="text-brand-600 dark:text-brand-400 font-semibold hover:underline"
                        >
                            Sign in
                        </Link>
                    </p>
                </div>

                <p className="text-center text-xs text-slate-400 mt-4">
                    Your thoughts, safely journalled. 💜
                </p>
            </div>
        </div>
    );
}
