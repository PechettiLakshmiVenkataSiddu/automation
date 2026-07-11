import { AdminPanel } from '@/components/admin/admin-panel';

export const metadata = {
  title: 'Admin Control Room - Aether',
  description: 'Manage users memberships roles, system policies, API keys, and audit search records',
};

export default function AdminPage() {
  return (
    <main style={{ minHeight: '100vh', backgroundColor: '#111827', padding: '2.5rem 1.5rem', color: '#f3f4f6' }}>
      <AdminPanel />
    </main>
  );
}
