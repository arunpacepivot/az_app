import { Metadata } from 'next'
import { SqpForm } from '@/components/sqp/SqpForm'

export const metadata: Metadata = {
  title: 'SQP Analysis Tool',
  description: 'Analyze search query performance to identify high-performing keywords and opportunities for improvement',
}

export default function SqpPage() {
  return <SqpForm />
} 