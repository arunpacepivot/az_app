//important as mentioned in next docs
import { NextResponse } from 'next/server';

export async function GET() {
  return NextResponse.json({ message: 'Hello from auth route' });
}

export async function POST(request: Request) {
  const data = await request.json();
  return NextResponse.json({ message: 'Auth endpoint', data });
}
