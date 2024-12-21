import { NextResponse } from 'next/server';

export async function POST(request: Request) {
  try {
    // Use environment variable for backend URL
    const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL;
    
    // Forward the request to the Django backend
    const data = await request.json();
    
    const backendResponse = await fetch(`${BACKEND_URL}/api/v1/lister/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });

    if (!backendResponse.ok) {
      throw new Error('Backend lister failed');
    }

    const responseData = await backendResponse.json();
    return NextResponse.json(responseData);
  } catch (error) {
    console.error('Lister error:', error);
    return NextResponse.json(
      { 
        status: 'error', 
        message: error instanceof Error ? error.message : 'Unknown error' 
      }, 
      { status: 500 }
    );
  }
}
