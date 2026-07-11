import { AnalyticsDashboard } from '@/components/analytics/analytics-dashboard';

export const metadata = {
  title: 'Usage Analytics - Aether',
  description: 'Monitor token billing allocations and workflow performance rates',
};

export default function AnalyticsPage() {
  return (
    <main style={{ minHeight: '100vh', backgroundColor: '#111827', padding: '2.5rem 1.5rem', color: '#f3f4f6' }}>
      <AnalyticsDashboard />
    </main>
  );
}
