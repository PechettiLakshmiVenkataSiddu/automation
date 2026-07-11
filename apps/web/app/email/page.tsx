import { EmailWorkspace } from '@/components/email/email-workspace';

export const metadata = {
  title: 'Email - Aether',
  description: 'Draft-first Gmail scheduling and approval dashboard',
};

export default function EmailPage() {
  return (
    <main style={{ minHeight: '100vh', backgroundColor: '#111827', padding: '2rem 1.5rem', color: '#f3f4f6' }}>
      <EmailWorkspace />
    </main>
  );
}
