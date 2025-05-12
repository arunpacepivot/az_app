"use client"

import ProtectedRoute from '@/components/auth/protected-route'
import { NgramForm } from '@/components/ngram/NgramForm'

export default function NgramPage() {
  return (
    <ProtectedRoute>
      <NgramForm />
    </ProtectedRoute>
  )
} 