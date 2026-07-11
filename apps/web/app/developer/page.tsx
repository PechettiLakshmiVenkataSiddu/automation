import { TerminalMonitor } from '@/components/developer/terminal-monitor';

export const metadata = {
  title: 'Developer Terminal - Aether',
  description: 'Secure sandboxed terminal and execution gateway',
};

export default function DeveloperPage() {
  return (
    <main style={{ minHeight: '100vh', backgroundColor: '#111827', padding: '2rem 1.5rem', color: '#f3f4f6' }}>
      <TerminalMonitor />
    </main>
  );
}
