import { NotificationsCenter } from '@/components/notifications/notifications-center';

export const metadata = {
  title: 'Notifications - Aether',
  description: 'Durable notifications logs and delivery preferences control center',
};

export default function NotificationsPage() {
  return (
    <main style={{ minHeight: '100vh', backgroundColor: '#111827', padding: '2rem 1.5rem', color: '#f3f4f6' }}>
      <NotificationsCenter />
    </main>
  );
}
