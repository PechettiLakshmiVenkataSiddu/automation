'use client';

import { FormEvent, useEffect, useState } from 'react';
import {
  forgetMemories,
  loadMemoryWorkspace,
  Memory,
  removeMemory,
  saveMemory,
  setMemoryConsent,
} from '@/lib/memory-api';

export function MemorySettings() {
  const [token, setToken] = useState('');
  const [organizationId, setOrganizationId] = useState('');
  const [enabled, setEnabled] = useState(false);
  const [memories, setMemories] = useState<Memory[]>([]);
  const [text, setText] = useState('');
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    loadMemoryWorkspace()
      .then(({ token, organizationId, consent, memories }) => {
        setToken(token);
        setOrganizationId(organizationId);
        setEnabled(consent.enabled);
        setMemories(memories);
      })
      .catch((error: unknown) =>
        setError(error instanceof Error ? error.message : 'Memory settings could not load.'),
      );
  }, []);
  async function toggle() {
    try {
      await setMemoryConsent(token, organizationId, !enabled);
      setEnabled(!enabled);
    } catch {
      setError('Consent could not be updated.');
    }
  }
  async function add(event: FormEvent) {
    event.preventDefault();
    if (!text.trim() || !enabled) return;
    try {
      const memory = (await saveMemory(token, organizationId, 'preference', text.trim())) as Memory;
      setMemories((items) => [memory, ...items]);
      setText('');
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Memory could not be saved.');
    }
  }
  async function remove(id: string) {
    if (!confirm('Delete this memory? It will no longer be used in chat.')) return;
    await removeMemory(token, organizationId, id);
    setMemories((items) => items.filter((memory) => memory.id !== id));
  }
  async function forget() {
    if (!confirm('Delete every saved memory? This cannot be undone.')) return;
    await forgetMemories(token, organizationId);
    setMemories([]);
  }
  return (
    <main className="mx-auto max-w-3xl p-6">
      <p className="text-sm font-semibold tracking-[0.2em] text-[var(--accent)]">AETHER</p>
      <h1 className="mt-2 text-3xl font-semibold">Long-term memory</h1>
      <p className="mt-2 text-[var(--muted)]">
        Memory is opt-in. You can inspect, remove, export through the API, or delete everything at
        any time.
      </p>
      <section className="mt-8 rounded-xl bg-[var(--panel)] p-5">
        <label className="flex cursor-pointer items-center justify-between gap-4">
          <span>
            <strong>Use my saved memories in chat</strong>
            <br />
            <span className="text-sm text-[var(--muted)]">
              Only your own active memories are retrieved, with a fixed size limit.
            </span>
          </span>
          <input
            type="checkbox"
            checked={enabled}
            onChange={toggle}
            aria-label="Enable long-term memory"
          />
        </label>
      </section>
      <form onSubmit={add} className="mt-6">
        <label htmlFor="memory">Save a memory</label>
        <textarea
          id="memory"
          value={text}
          onChange={(event) => setText(event.target.value)}
          disabled={!enabled}
          className="mt-2 min-h-24 w-full rounded-xl border border-[var(--border)] bg-[var(--panel)] p-3"
        />
        <button
          disabled={!enabled}
          className="mt-3 rounded-lg bg-[var(--accent)] px-4 py-2 font-semibold text-slate-950 disabled:opacity-50"
        >
          Save memory
        </button>
      </form>
      <p role="alert" className="mt-3 text-sm text-red-300">
        {error}
      </p>
      <section className="mt-8">
        <div className="flex justify-between">
          <h2 className="text-xl font-semibold">Saved memories</h2>
          <button onClick={forget} className="text-sm text-red-300">
            Forget all
          </button>
        </div>
        <ul className="mt-3 space-y-3">
          {memories.map((memory) => (
            <li
              key={memory.id}
              className="flex justify-between gap-4 rounded-xl bg-[var(--panel)] p-4"
            >
              <span>{memory.text}</span>
              <button onClick={() => remove(memory.id)} className="text-sm text-red-300">
                Delete
              </button>
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}
