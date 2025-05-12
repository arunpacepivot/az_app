import { NextResponse } from 'next/server';

export async function POST(request: Request) {
  try {
    // Use environment variable for backend URL
    const isDevelopment = process.env.NODE_ENV === 'development';
    const baseUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 
      (isDevelopment ? "http://localhost:8000/" : "https://django-backend-epcse2awb3cyh5e8.centralindia-01.azurewebsites.net/");
    
    // Forward the request to the Django backend
    const data = await request.json();
    
    const backendResponse = await fetch(`${baseUrl}/api/v1/lister/`, {
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
