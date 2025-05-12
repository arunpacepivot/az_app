"use client"
import { CerebroForm } from '@/components/cerebro/CerebroForm';
import ProtectedRoute from '@/components/auth/protected-route';
export default function CerebroPage() {
  return (
    <ProtectedRoute>
      <main className="flex-1">
        <div className="min-h-screen bg-gradient-to-b from-gray-900 to-gray-800 p-6 flex flex-col items-center justify-center">
    <CerebroForm />
        </div>
      </main>
    </ProtectedRoute>
  );
} 