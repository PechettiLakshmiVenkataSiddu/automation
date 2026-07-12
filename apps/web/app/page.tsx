'use client';

import Link from 'next/link';
import { motion } from 'framer-motion';

const smoothEase = [0.16, 1, 0.3, 1] as const;

const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.12, delayChildren: 0.1 },
  },
};

const item = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0, transition: { duration: 0.7, ease: smoothEase } },
};

export default function HomePage() {
  return (
    <motion.main
      variants={container}
      initial="hidden"
      animate="show"
      className="relative mx-auto flex min-h-screen max-w-5xl flex-col justify-center px-6 py-16"
    >
      {/* ambient glow, hints at "AI is active" */}
      <motion.div
        aria-hidden
        className="pointer-events-none absolute -left-32 top-1/3 h-72 w-72 rounded-full bg-[var(--accent)] opacity-[0.08] blur-3xl"
        animate={{ scale: [1, 1.15, 1], opacity: [0.06, 0.12, 0.06] }}
        transition={{ duration: 6, repeat: Infinity, ease: 'easeInOut' }}
      />

      <motion.p
        variants={item}
        className="mb-5 text-sm font-semibold tracking-[0.24em] text-[var(--accent)]"
      >
        AETHER
      </motion.p>
      <motion.h1
        variants={item}
        className="max-w-3xl text-5xl font-semibold tracking-tight sm:text-7xl"
      >
        Your AI operations layer.
      </motion.h1>
      <motion.p variants={item} className="mt-7 max-w-2xl text-lg leading-8 text-[var(--muted)]">
        Connect the work you already do. Delegate safely, approve consequential actions, and keep
        every outcome visible.
      </motion.p>
      <motion.div variants={item} className="mt-10">
        <motion.div
          whileHover={{ scale: 1.03 }}
          whileTap={{ scale: 0.97 }}
          transition={{ duration: 0.25, ease: smoothEase }}
          className="inline-block"
        >
          <Link
            className="rounded-lg bg-[var(--accent)] px-5 py-3 font-semibold text-slate-950 transition-colors hover:bg-emerald-300"
            href="/login"
          >
            Get started
          </Link>
        </motion.div>
      </motion.div>
    </motion.main>
  );
}