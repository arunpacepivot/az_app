import { TopicalForm } from '@/components/topical/TopicalForm';
import { PageHeader } from '@/components/ui/page-header';

export default function TopicalPage() {
  return (
    <div className="container mx-auto py-6 space-y-6">
      <PageHeader
        title="Topical Analysis"
        description="Analyze topics and trends from your data"
      />
      <TopicalForm />
    </div>
  );
} 