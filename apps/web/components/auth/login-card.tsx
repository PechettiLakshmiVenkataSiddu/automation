'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

import { beginOAuthLogin, type OAuthProvider } from '@/lib/auth-api';

const smoothEase = [0.16, 1, 0.3, 1] as const;

const providers: ReadonlyArray<{ id: OAuthProvider; label: string }> = [
  { id: 'google', label: 'Continue with Google' },
  { id: 'github', label: 'Continue with GitHub' },
];

export function LoginCard() {
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<OAuthProvider | null>(null);

  async function signIn(provider: OAuthProvider) {
    setLoading(provider);
    setError(null);
    try {
      sessionStorage.setItem('oauth_provider', provider);
      window.location.assign(beginOAuthLogin(provider, `${window.location.origin}/auth/callback`));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Unable to start sign-in.');
      setLoading(null);
    }
  }

  return (
    <motion.section
      initial={{ opacity: 0, y: 24, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.6, ease: smoothEase }}
      aria-labelledby="sign-in-title"
      className="relative w-full max-w-md overflow-hidden rounded-2xl border border-[var(--border)] bg-[var(--panel)] p-8 shadow-2xl"
    >
      {/* subtle ambient pulse, top corner — "system is listening" feel */}
      <motion.div
        aria-hidden
        className="pointer-events-none absolute -right-16 -top-16 h-40 w-40 rounded-full bg-[var(--accent)] opacity-[0.1] blur-2xl"
        animate={{ opacity: [0.06, 0.14, 0.06] }}
        transition={{ duration: 4, repeat: Infinity, ease: 'easeInOut' }}
      />

      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.1, duration: 0.5 }}
        className="text-sm font-semibold tracking-[0.2em] text-[var(--accent)]"
      >
        AETHER
      </motion.p>
      <motion.h1
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.15, duration: 0.5, ease: smoothEase }}
        id="sign-in-title"
        className="mt-3 text-3xl font-semibold"
      >
        Welcome back
      </motion.h1>
      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.22, duration: 0.5 }}
        className="mt-3 text-sm leading-6 text-[var(--muted)]"
      >
        Sign in to your secure AI automation workspace.
      </motion.p>
      <div className="mt-8 space-y-3">
        {providers.map(({ id, label }, index) => (
          <motion.button
            key={id}
            type="button"
            disabled={loading !== null}
            onClick={() => signIn(id)}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.28 + index * 0.08, duration: 0.5, ease: smoothEase }}
            whileHover={{ scale: 1.015, borderColor: 'var(--accent)' }}
            whileTap={{ scale: 0.985 }}
            className="w-full rounded-lg border border-[var(--border)] px-4 py-3 text-left font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-60"
          >
            <AnimatePresence mode="wait">
              <motion.span
                key={loading === id ? 'loading' : 'idle'}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.2 }}
                className="inline-block"
              >
                {loading === id ? 'Redirecting…' : label}
              </motion.span>
            </AnimatePresence>
          </motion.button>
        ))}
      </div>
      <AnimatePresence>
        {error && (
          <motion.p
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.3, ease: smoothEase }}
            role="alert"
            className="mt-5 text-sm text-red-300"
          >
            {error}
          </motion.p>
        )}
      </AnimatePresence>
    </motion.section>
  );
}