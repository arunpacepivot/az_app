import { NextRequest, NextResponse } from 'next/server';

// Get the backend URL from environment variables
const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

export async function GET(request: NextRequest) {
  try {
    // Get query parameters from the request
    const searchParams = request.nextUrl.searchParams;
    const user_id = searchParams.get('user_id');
    const region = searchParams.get('region') || 'EU';
    const scopes = searchParams.get('scopes') || 'advertising::campaign_management';

    // Construct the backend API URL with query parameters
    const backendUrl = new URL(`${BACKEND_URL}/api/v1/amazon/advertising/auth/init`);
    
    if (user_id) backendUrl.searchParams.append('user_id', user_id);
    if (region) backendUrl.searchParams.append('region', region);
    if (scopes) backendUrl.searchParams.append('scopes', scopes);

    // Forward the request to the backend
    const response = await fetch(backendUrl.toString(), {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      // Handle non-JSON responses gracefully
      let errorData;
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        errorData = await response.json();
      } else {
        const text = await response.text();
        errorData = { error: `Server error: ${text.substring(0, 100)}...` };
      }
      
      return NextResponse.json(
        { error: errorData.error || 'Failed to initialize Amazon Advertising authorization' },
        { status: response.status }
      );
    }

    // Return the response from the backend
    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error initializing Amazon Advertising auth:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
} 