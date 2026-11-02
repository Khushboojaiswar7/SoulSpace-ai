/**
 * pages/Login.jsx
 * Login form page. Calls /auth/login, stores JWT, redirects to /dashboard.
 */

import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { loginUser } from '../api/auth';
import { useAuth } from '../context/AuthContext';

export default function Login() {
    const navigate = useNavigate();
    const { login } = useAuth();

    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');

        if (!email.trim() || !password) {
            setError('Please fill in both fields.');
            return;
        }

        setLoading(true);
        try {
            const data = await loginUser(email.trim().toLowerCase(), password);
            login(data.token, data.user);   // save to context + localStorage
            navigate('/dashboard');
        } catch (err) {
            setError(err.message || 'Login failed. Please try again.');
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
                        <div className="text-5xl mb-3">🧠</div>
                        <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100">
                            Welcome back
                        </h1>
                        <p className="text-slate-500 dark:text-slate-400 text-sm mt-1">
                            Sign in to continue your journalling journey
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
                                Email
                            </label>
                            <input
                                id="login-email"
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
                                id="login-password"
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                placeholder="••••••••"
                                autoComplete="current-password"
                                required
                                className="w-full rounded-2xl border border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-700 px-4 py-3 text-slate-800 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-400 transition-colors"
                            />
                        </div>

                        <button
                            type="submit"
                            id="login-submit"
                            disabled={loading}
                            className="w-full py-3 mt-2 rounded-2xl bg-brand-500 hover:bg-brand-600 disabled:opacity-60 text-white font-semibold transition-all shadow-sm hover:shadow-md active:scale-95"
                        >
                            {loading ? 'Signing in…' : 'Sign In →'}
                        </button>
                    </form>

                    {/* Footer link */}
                    <p className="text-center text-sm text-slate-500 dark:text-slate-400 mt-6">
                        Don't have an account?{' '}
                        <Link
                            to="/signup"
                            className="text-brand-600 dark:text-brand-400 font-semibold hover:underline"
                        >
                            Create one
                        </Link>
                    </p>
                </div>

                {/* Tagline */}
                <p className="text-center text-xs text-slate-400 mt-4">
                    Your thoughts, safely journalled. 💜
                </p>
            </div>
        </div>
    );
}
