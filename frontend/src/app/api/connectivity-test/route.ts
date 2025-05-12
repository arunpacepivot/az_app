import { NextResponse } from 'next/server';

export async function POST(request: Request) {
  try {

    const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
    
    // Forward the request to the Django backend
    const data = await request.json();
    
    const backendResponse = await fetch(`${BACKEND_URL}/api/v1/health/connectivity-test/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });

    if (!backendResponse.ok) {
      throw new Error('Backend connectivity test failed');
    }

    const responseData = await backendResponse.json();
    return NextResponse.json(responseData);
  } catch (error) {
    console.error('Connectivity test error:', error);
    return NextResponse.json(
      { 
        status: 'error', 
        message: error instanceof Error ? error.message : 'Unknown error' 
      }, 
      { status: 500 }
    );
  }
}
