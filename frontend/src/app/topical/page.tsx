"use client"

import { TopicalForm } from '@/components/topical/TopicalForm';
import ProtectedRoute from '@/components/auth/protected-route';

export default function TopicalPage() {
  return (
    <ProtectedRoute>
      <main className="flex-1">
        <div className="min-h-screen bg-gradient-to-b from-gray-900 to-gray-800 p-6 flex flex-col items-center justify-center">
          <TopicalForm />
        </div>
      </main>
    </ProtectedRoute>
  );
} 