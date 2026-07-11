import { ChatIntegrationWorkspace } from '@/components/chat-integration/chat-integration-workspace';

export const metadata = {
  title: 'Chat Integration - Aether',
  description: 'Scoped Slack and Teams scheduling and approvals console',
};

export default function ChatIntegrationPage() {
  return (
    <main style={{ minHeight: '100vh', backgroundColor: '#111827', padding: '2rem 1.5rem', color: '#f3f4f6' }}>
      <ChatIntegrationWorkspace />
    </main>
  );
}
