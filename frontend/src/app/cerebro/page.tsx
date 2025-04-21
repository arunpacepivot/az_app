import { CerebroForm } from '@/components/cerebro/CerebroForm';
import { PageHeader } from '@/components/ui/page-header';

export default function CerebroPage() {
  return (
    <div className="container mx-auto py-6 space-y-6">
      <PageHeader
        title="Cerebro Analysis"
        description="Advanced keyword research and analysis for your products"
      />
      <CerebroForm />
    </div>
  );
} 