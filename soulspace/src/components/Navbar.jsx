/**
 * components/Navbar.jsx
 * Top navigation bar with dark-mode toggle and logout functionality.
 * Responsive: hamburger menu on mobile.
 */

import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Navbar() {
    const { isAuthenticated, user, logout } = useAuth();
    const navigate = useNavigate();
    const [menuOpen, setMenuOpen] = useState(false);
    const [dark, setDark] = useState(
        () => document.documentElement.classList.contains('dark')
    );

    const toggleDark = () => {
        document.documentElement.classList.toggle('dark');
        setDark((d) => !d);
    };

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    return (
        <nav className="sticky top-0 z-50 bg-white/80 dark:bg-slate-900/80 backdrop-blur border-b border-slate-200 dark:border-slate-700 transition-colors">
            <div className="max-w-5xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-between">

                {/* Logo */}
                <Link
                    to={isAuthenticated ? '/dashboard' : '/login'}
                    className="flex items-center gap-2 font-bold text-xl text-brand-600 dark:text-brand-400 select-none"
                >
                    <span className="text-2xl">🧠</span>
                    <span>SoulSpace</span>
                </Link>

                {/* Desktop controls */}
                <div className="hidden sm:flex items-center gap-3">
                    {/* Dark mode toggle */}
                    <button
                        onClick={toggleDark}
                        aria-label="Toggle dark mode"
                        className="w-9 h-9 rounded-full flex items-center justify-center bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-brand-100 dark:hover:bg-brand-900 transition-colors"
                    >
                        {dark ? '☀️' : '🌙'}
                    </button>

                    {isAuthenticated ? (
                        <>
                            <span className="text-sm text-slate-500 dark:text-slate-400 font-medium">
                                Hi, {user?.username || 'there'} 👋
                            </span>
                            <button
                                onClick={handleLogout}
                                className="px-4 py-2 rounded-full text-sm font-semibold bg-brand-500 hover:bg-brand-600 text-white transition-colors shadow-sm"
                            >
                                Logout
                            </button>
                        </>
                    ) : (
                        <>
                            <Link
                                to="/login"
                                className="text-sm font-semibold text-slate-600 dark:text-slate-300 hover:text-brand-600 transition-colors"
                            >
                                Login
                            </Link>
                            <Link
                                to="/signup"
                                className="px-4 py-2 rounded-full text-sm font-semibold bg-brand-500 hover:bg-brand-600 text-white transition-colors shadow-sm"
                            >
                                Sign Up
                            </Link>
                        </>
                    )}
                </div>

                {/* Mobile: dark toggle + hamburger */}
                <div className="flex sm:hidden items-center gap-2">
                    <button
                        onClick={toggleDark}
                        aria-label="Toggle dark mode"
                        className="w-9 h-9 rounded-full flex items-center justify-center bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300"
                    >
                        {dark ? '☀️' : '🌙'}
                    </button>
                    <button
                        onClick={() => setMenuOpen((o) => !o)}
                        aria-label="Open menu"
                        className="w-9 h-9 rounded-full flex items-center justify-center bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300"
                    >
                        {menuOpen ? '✕' : '☰'}
                    </button>
                </div>
            </div>

            {/* Mobile dropdown */}
            {menuOpen && (
                <div className="sm:hidden px-4 pb-4 flex flex-col gap-3 bg-white dark:bg-slate-900 border-t border-slate-100 dark:border-slate-700">
                    {isAuthenticated ? (
                        <>
                            <span className="text-sm text-slate-500 dark:text-slate-400">
                                Hi, {user?.username || 'there'} 👋
                            </span>
                            <button
                                onClick={() => { setMenuOpen(false); handleLogout(); }}
                                className="w-full px-4 py-2 rounded-full text-sm font-semibold bg-brand-500 text-white"
                            >
                                Logout
                            </button>
                        </>
                    ) : (
                        <>
                            <Link to="/login" onClick={() => setMenuOpen(false)} className="text-sm font-semibold text-slate-700 dark:text-slate-200">Login</Link>
                            <Link to="/signup" onClick={() => setMenuOpen(false)} className="w-full px-4 py-2 rounded-full text-sm font-semibold bg-brand-500 text-white text-center">Sign Up</Link>
                        </>
                    )}
                </div>
            )}
        </nav>
    );
}
