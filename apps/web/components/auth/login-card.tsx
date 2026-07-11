'use client';

import { useState } from 'react';

import { beginOAuthLogin, type OAuthProvider } from '@/lib/auth-api';

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
      window.location.assign(beginOAuthLogin(provider, `${window.location.origin}/auth/callback`));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Unable to start sign-in.');
      setLoading(null);
    }
  }

  return (
    <section
      aria-labelledby="sign-in-title"
      className="w-full max-w-md rounded-2xl border border-[var(--border)] bg-[var(--panel)] p-8 shadow-2xl"
    >
      <p className="text-sm font-semibold tracking-[0.2em] text-[var(--accent)]">AETHER</p>
      <h1 id="sign-in-title" className="mt-3 text-3xl font-semibold">
        Welcome back
      </h1>
      <p className="mt-3 text-sm leading-6 text-[var(--muted)]">
        Sign in to your secure AI automation workspace.
      </p>
      <div className="mt-8 space-y-3">
        {providers.map(({ id, label }) => (
          <button
            key={id}
            type="button"
            disabled={loading !== null}
            onClick={() => signIn(id)}
            className="w-full rounded-lg border border-[var(--border)] px-4 py-3 text-left font-medium hover:border-[var(--accent)] disabled:cursor-not-allowed disabled:opacity-60"
          >
            {loading === id ? 'Redirecting…' : label}
          </button>
        ))}
      </div>
      {error && (
        <p role="alert" className="mt-5 text-sm text-red-300">
          {error}
        </p>
      )}
    </section>
  );
}
