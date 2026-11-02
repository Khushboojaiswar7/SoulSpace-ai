/**
 * components/ChatBot.jsx
 * Floating mini mental wellness chatbot widget.
 *
 * Features:
 *   – Floating button at bottom-right corner (always visible on all pages)
 *   – Click to open/close the chat panel
 *   – User messages appear on the right, bot replies on the left
 *   – Auto-scrolls to the latest message
 *   – Calls POST /api/chat via sendChatMessage()
 *   – Full Tailwind dark-mode support
 *   – Mobile responsive
 *
 * Usage:
 *   Mount once in App.jsx so it's available site-wide:
 *     <ChatBot token={token} />
 */

import React, { useState, useRef, useEffect, useCallback } from 'react';
import { sendChatMessage } from '../api/chat';
import { useAuth } from '../context/AuthContext';

/* ── Individual message bubble ─────────────────────────────────────────── */
function MessageBubble({ role, text }) {
    const isUser = role === 'user';
    return (
        <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-3`}>
            {/* Bot avatar */}
            {!isUser && (
                <span className="mr-2 flex-shrink-0 w-7 h-7 rounded-full bg-violet-100 dark:bg-violet-900/50 flex items-center justify-center text-sm select-none">
                    🧠
                </span>
            )}

            <div
                className={`max-w-[78%] px-4 py-2.5 rounded-2xl text-sm leading-relaxed shadow-sm ${isUser
                    ? 'bg-brand-500 text-white rounded-tr-sm'
                    : 'bg-white dark:bg-slate-700 text-slate-800 dark:text-slate-100 border border-slate-100 dark:border-slate-600 rounded-tl-sm'
                    }`}
            >
                {text}
            </div>

            {/* User avatar */}
            {isUser && (
                <span className="ml-2 flex-shrink-0 w-7 h-7 rounded-full bg-brand-100 dark:bg-brand-900/40 flex items-center justify-center text-sm select-none">
                    🙂
                </span>
            )}
        </div>
    );
}

/* ── Typing indicator (animated dots) ──────────────────────────────────── */
function TypingIndicator() {
    return (
        <div className="flex justify-start mb-3">
            <span className="mr-2 flex-shrink-0 w-7 h-7 rounded-full bg-violet-100 dark:bg-violet-900/50 flex items-center justify-center text-sm">
                🧠
            </span>
            <div className="px-4 py-3 rounded-2xl rounded-tl-sm bg-white dark:bg-slate-700 border border-slate-100 dark:border-slate-600 shadow-sm flex gap-1 items-center">
                {[0, 150, 300].map((delay) => (
                    <span
                        key={delay}
                        className="w-2 h-2 rounded-full bg-violet-400 dark:bg-violet-300 animate-bounce"
                        style={{ animationDelay: `${delay}ms` }}
                    />
                ))}
            </div>
        </div>
    );
}

/* ── Main ChatBot component ─────────────────────────────────────────────── */
export default function ChatBot() {
    const { token } = useAuth();                    // JWT from context (optional for /api/chat)
    const [isOpen, setIsOpen] = useState(false); // panel visibility
    const [input, setInput] = useState('');
    const [messages, setMessages] = useState([
        {
            role: 'bot',
            text: "Hi there! 👋 I'm your SoulSpace Assistant. How are you feeling today?",
        },
    ]);
    const [isTyping, setIsTyping] = useState(false);

    const messagesEndRef = useRef(null);  // anchor for auto-scroll
    const inputRef = useRef(null);  // focus input on open

    /* Auto-scroll to latest message */
    const scrollToBottom = useCallback(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, []);

    useEffect(() => {
        scrollToBottom();
    }, [messages, isTyping, scrollToBottom]);

    /* Focus input whenever panel opens */
    useEffect(() => {
        if (isOpen) {
            setTimeout(() => inputRef.current?.focus(), 150);
        }
    }, [isOpen]);

    /**
     * sendMessage
     * Appends the user's message, calls the backend chatbot API,
     * then appends the bot's reply.
     */
    const sendMessage = useCallback(async () => {
        const text = input.trim();
        if (!text || isTyping) return;

        // Append user message immediately
        setMessages((prev) => [...prev, { role: 'user', text }]);
        setInput('');
        setIsTyping(true);

        try {
            const reply = await sendChatMessage(text, token ?? null);
            setMessages((prev) => [...prev, { role: 'bot', text: reply }]);
        } catch (err) {
            setMessages((prev) => [
                ...prev,
                {
                    role: 'bot',
                    text: "I'm having a little trouble right now. 💙 Please try again in a moment.",
                },
            ]);
        } finally {
            setIsTyping(false);
        }
    }, [input, isTyping, token]);

    /* Allow submitting with Enter (Shift+Enter = newline) */
    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    };

    return (
        <>
            {/* ── Chat panel ────────────────────────────────────────────── */}
            <div
                className={`
                    fixed bottom-24 right-4 z-50
                    w-[22rem] sm:w-96
                    flex flex-col
                    bg-slate-50 dark:bg-slate-800
                    border border-slate-200 dark:border-slate-700
                    rounded-3xl shadow-2xl
                    transition-all duration-300 ease-out origin-bottom-right
                    ${isOpen
                        ? 'opacity-100 scale-100 pointer-events-auto'
                        : 'opacity-0 scale-90 pointer-events-none'
                    }
                `}
                style={{ maxHeight: '75vh' }}
                aria-hidden={!isOpen}
            >
                {/* Header */}
                <div className="flex items-center justify-between px-5 py-4 bg-gradient-to-r from-violet-600 to-indigo-600 rounded-t-3xl flex-shrink-0">
                    <div className="flex items-center gap-2">
                        <span className="text-xl" aria-hidden="true">🧠</span>
                        <div>
                            <p className="text-sm font-bold text-white leading-none">
                                SoulSpace Assistant
                            </p>
                            <p className="text-xs text-violet-200 mt-0.5">Here to listen 💙</p>
                        </div>
                    </div>
                    <button
                        onClick={() => setIsOpen(false)}
                        className="text-white/70 hover:text-white transition-colors rounded-full p-1 hover:bg-white/10"
                        aria-label="Close chat"
                    >
                        ✕
                    </button>
                </div>

                {/* Scrollable messages area */}
                <div className="flex-1 overflow-y-auto px-4 pt-4 pb-2 min-h-0 overscroll-contain">
                    {messages.map((msg, i) => (
                        <MessageBubble key={i} role={msg.role} text={msg.text} />
                    ))}

                    {/* Typing indicator – shows while waiting for bot reply */}
                    {isTyping && <TypingIndicator />}

                    {/* Invisible anchor for auto-scroll */}
                    <div ref={messagesEndRef} />
                </div>

                {/* Input row */}
                <div className="flex-shrink-0 flex items-end gap-2 px-4 py-3 border-t border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 rounded-b-3xl">
                    <textarea
                        ref={inputRef}
                        rows={1}
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="Type a message…"
                        className="
                            flex-1 resize-none rounded-2xl
                            border border-slate-200 dark:border-slate-600
                            bg-slate-50 dark:bg-slate-700
                            px-4 py-2.5 text-sm
                            text-slate-800 dark:text-slate-100
                            placeholder-slate-400
                            focus:outline-none focus:ring-2 focus:ring-violet-400
                            transition-colors max-h-28 overflow-y-auto
                        "
                        style={{ lineHeight: '1.5' }}
                        aria-label="Chat message input"
                    />
                    <button
                        onClick={sendMessage}
                        disabled={!input.trim() || isTyping}
                        className="
                            flex-shrink-0 w-10 h-10 rounded-2xl
                            bg-gradient-to-br from-violet-500 to-indigo-600
                            hover:from-violet-600 hover:to-indigo-700
                            disabled:opacity-40 disabled:cursor-not-allowed
                            text-white flex items-center justify-center
                            transition-all shadow-sm hover:shadow-md active:scale-95
                        "
                        aria-label="Send message"
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
                            <path d="M3.105 2.289a.75.75 0 00-.826.95l1.903 6.115a.75.75 0 00.95.489l6.6-2.2a.375.375 0 010 .713l-6.6-2.2a.75.75 0 00-.95.488l-1.903 6.115a.75.75 0 00.826.95A24.068 24.068 0 0118 10a24.068 24.068 0 01-14.895-7.711z" />
                        </svg>
                    </button>
                </div>
            </div>

            {/* ── Floating toggle button ─────────────────────────────────── */}
            <button
                onClick={() => setIsOpen((o) => !o)}
                className={`
                    fixed bottom-5 right-4 z-50
                    w-14 h-14 rounded-full
                    bg-gradient-to-br from-violet-500 to-indigo-600
                    hover:from-violet-600 hover:to-indigo-700
                    shadow-lg hover:shadow-xl
                    flex items-center justify-center
                    text-white text-2xl
                    transition-all duration-300
                    active:scale-90
                    ${isOpen ? 'rotate-90' : 'rotate-0'}
                `}
                aria-label={isOpen ? 'Close chatbot' : 'Open SoulSpace Assistant'}
            >
                {isOpen ? (
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-6 h-6">
                        <path d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z" />
                    </svg>
                ) : (
                    <span aria-hidden="true">💬</span>
                )}
            </button>
        </>
    );
}
