import { NextRequest, NextResponse } from 'next/server';

// Get the backend URL from environment variables
const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

export async function GET(request: NextRequest) {
  try {
    // Get authorization header from the client request
    const authHeader = request.headers.get('Authorization');
    
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }
    
    const token = authHeader.split(' ')[1];

    console.log('Fetching advertising profiles from backend');

    // Forward the request to the backend with the token
    // This needs to exactly match the backend's endpoint structure
    const response = await fetch(`${BACKEND_URL}/api/v1/amazon/advertising/profiles`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
    });

    if (!response.ok) {
      // If no connected accounts, return empty array instead of error
      if (response.status === 404) {
        return NextResponse.json([]);
      }

      // Handle non-JSON responses gracefully
      let errorData;
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        errorData = await response.json();
      } else {
        const text = await response.text();
        errorData = { error: `Server error: ${text.substring(0, 100)}...` };
      }

      console.error('Error fetching advertising profiles:', errorData);

      return NextResponse.json(
        { error: errorData.error || 'Failed to fetch Amazon Advertising profiles' },
        { status: response.status }
      );
    }

    // Return the profiles from the backend
    const data = await response.json();
    console.log(`Successfully fetched ${data.length || 0} advertising profiles`);
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error fetching Amazon Advertising profiles:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
} 