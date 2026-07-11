import { CalendarWorkspace } from '@/components/calendar/calendar-workspace';

export const metadata = {
  title: 'Calendar - Aether',
  description: 'Scoped calendar scheduling and approval control center',
};

export default function CalendarPage() {
  return (
    <main style={{ minHeight: '100vh', backgroundColor: '#111827', padding: '2rem 1.5rem', color: '#f3f4f6' }}>
      <CalendarWorkspace />
    </main>
  );
}
