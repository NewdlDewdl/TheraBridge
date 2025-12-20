import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Dashboard V2 | TherapyBridge',
  description: 'Widget-based therapy progress dashboard',
};

export default function DashboardV2Layout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-[#F7F5F3]">
      <div className="mx-auto max-w-[1400px] px-12 py-12">
        {children}
      </div>
    </div>
  );
}
