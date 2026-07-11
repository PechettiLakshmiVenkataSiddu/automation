'use client';

import { FormEvent, useState } from 'react';

import {
  createConversation,
  getOrganizations,
  refreshAccessToken,
  sendChatMessage,
} from '@/lib/chat-api';

type Entry = { role: 'user' | 'assistant'; content: string };

export function ChatWorkspace() {
  const [entries, setEntries] = useState<Entry[]>([]);
  const [value, setValue] = useState('');
  const [busy, setBusy] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const content = value.trim();
    if (!content || busy) return;
    setBusy(true);
    setError(null);
    setValue('');
    setEntries((current) => [...current, { role: 'user', content }]);
    try {
      const token = await refreshAccessToken();
      const organizations = await getOrganizations(token);
      if (!organizations[0]) throw new Error('No active workspace is available.');
      let activeConversationId = conversationId;
      if (!activeConversationId) {
        const conversation = await createConversation(
          token,
          organizations[0].id,
          content.slice(0, 80),
        );
        activeConversationId = conversation.id;
        setConversationId(activeConversationId);
      }
      const answer = await sendChatMessage(token, activeConversationId, content);
      setEntries((current) => [...current, { role: 'assistant', content: answer.content }]);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Chat could not complete.');
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-4xl flex-col p-6">
      <header>
        <p className="text-sm font-semibold tracking-[0.2em] text-[var(--accent)]">AETHER</p>
        <h1 className="mt-2 text-3xl font-semibold">AI Chat</h1>
      </header>
      <section aria-live="polite" className="mt-8 flex flex-1 flex-col gap-4">
        {entries.map((entry, index) => (
          <article
            key={index}
            className={`max-w-3xl rounded-xl p-4 ${entry.role === 'user' ? 'self-end bg-emerald-950' : 'bg-[var(--panel)]'}`}
          >
            <p className="mb-1 text-xs uppercase tracking-widest text-[var(--muted)]">
              {entry.role}
            </p>
            <p className="whitespace-pre-wrap leading-7">{entry.content}</p>
          </article>
        ))}
      </section>
      <form onSubmit={submit} className="mt-6">
        <label className="sr-only" htmlFor="message">
          Message
        </label>
        <textarea
          id="message"
          value={value}
          onChange={(event) => setValue(event.target.value)}
          disabled={busy}
          className="min-h-28 w-full rounded-xl border border-[var(--border)] bg-[var(--panel)] p-4"
          placeholder="Ask Aether anything…"
        />
        <div className="mt-3 flex items-center justify-between">
          <p role="alert" className="text-sm text-red-300">
            {error}
          </p>
          <button
            className="rounded-lg bg-[var(--accent)] px-5 py-3 font-semibold text-slate-950 disabled:opacity-60"
            disabled={busy}
          >
            {busy ? 'Thinking…' : 'Send'}
          </button>
        </div>
      </form>
    </main>
  );
}
