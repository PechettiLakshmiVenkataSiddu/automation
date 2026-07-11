import Link from 'next/link';

export default function HomePage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-5xl flex-col justify-center px-6 py-16">
      <p className="mb-5 text-sm font-semibold tracking-[0.24em] text-[var(--accent)]">AETHER</p>
      <h1 className="max-w-3xl text-5xl font-semibold tracking-tight sm:text-7xl">
        Your AI operations layer.
      </h1>
      <p className="mt-7 max-w-2xl text-lg leading-8 text-[var(--muted)]">
        Connect the work you already do. Delegate safely, approve consequential actions, and keep
        every outcome visible.
      </p>
      <div className="mt-10">
        <Link
          className="rounded-lg bg-[var(--accent)] px-5 py-3 font-semibold text-slate-950 hover:bg-emerald-300"
          href="/login"
        >
          Get started
        </Link>
      </div>
    </main>
  );
}
