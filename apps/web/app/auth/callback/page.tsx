'use client';

import { useEffect, useRef, useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { motion } from 'framer-motion';

const smoothEase = [0.16, 1, 0.3, 1] as const;

function apiBaseUrl(): string {
    const url = process.env.NEXT_PUBLIC_API_BASE_URL;
    if (!url) throw new Error('NEXT_PUBLIC_API_BASE_URL is not configured.');
    return url.replace(/\/$/, '');
}

// Extract logic into a sub-component that uses useSearchParams
function AuthCallbackHandler() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const [error, setError] = useState<string | null>(null);
    const hasRun = useRef(false);

    useEffect(() => {
        if (hasRun.current) return;
        hasRun.current = true;

        const code = searchParams.get('code');
        const state = searchParams.get('state');
        const provider = sessionStorage.getItem('oauth_provider');

        if (!code || !state || !provider) {
            setError('Missing sign-in details. Please try again.');
            return;
        }

        const query = new URLSearchParams({ code, state });

        fetch(`${apiBaseUrl()}/v1/auth/${provider}/callback?${query.toString()}`, {
            method: 'GET',
            credentials: 'include',
        })
            .then((response) => {
                if (!response.ok) {
                    throw new Error('Sign-in failed. Please try again.');
                }
                sessionStorage.removeItem('oauth_provider');
                router.replace('/dashboard');
            })
            .catch((cause) => {
                setError(cause instanceof Error ? cause.message : 'Sign-in failed. Please try again.');
            });
    }, [searchParams, router]);

    // Return the UI logic for both error and loading states
    return (
        <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, ease: smoothEase }}
            className="w-full max-w-md rounded-2xl border border-[var(--border)] bg-[var(--panel)] p-8 text-center shadow-2xl"
        >
            {error ? (
                <>
                    <p className="text-lg font-semibold text-red-300">Sign-in error</p>
                    <p className="mt-3 text-sm text-[var(--muted)]">{error}</p>
                    <button
                        onClick={() => router.replace('/login')}
                        className="mt-6 rounded-lg bg-[var(--accent)] px-5 py-2.5 font-semibold text-slate-950 hover:bg-emerald-300"
                    >
                        Back to sign in
                    </button>
                </>
            ) : (
                <>
                    <motion.div
                        className="mx-auto h-8 w-8 rounded-full border-2 border-[var(--accent)] border-t-transparent"
                        animate={{ rotate: 360 }}
                        transition={{ duration: 0.8, repeat: Infinity, ease: 'linear' }}
                    />
                    <p className="mt-4 text-sm text-[var(--muted)]">Completing sign-in…</p>
                </>
            )}
        </motion.div>
    );
}

// Export the page wrapped in Suspense to satisfy Next.js requirements
export default function AuthCallbackPage() {
    return (
        <main className="flex min-h-screen items-center justify-center px-6">
            <Suspense fallback={
                <div className="text-[var(--muted)]">Loading authentication...</div>
            }>
                <AuthCallbackHandler />
            </Suspense>
        </main>
    );
}