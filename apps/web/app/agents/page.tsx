import { AgentMonitor } from '@/components/agents/agent-monitor';

export const metadata = {
  title: 'AI Agents - Aether',
  description: 'Secure multi-agent orchestrator dashboard',
};

export default function AgentsPage() {
  return (
    <main style={{ minHeight: '100vh', backgroundColor: '#111827', padding: '2rem 1.5rem', color: '#f3f4f6' }}>
      <AgentMonitor />
    </main>
  );
}
