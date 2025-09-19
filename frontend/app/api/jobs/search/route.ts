import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = 'https://remote-away.com';

export const dynamic = 'force-dynamic';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const backendUrl = `${BACKEND_URL}/api/v1/jobs/search/?${searchParams.toString()}`;
    
    console.log('Proxying search request to:', backendUrl);
    
    const response = await fetch(backendUrl);
    
    if (!response.ok) {
      return NextResponse.json(
        { error: 'Backend search request failed' },
        { status: response.status }
      );
    }
    
    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Search proxy error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}