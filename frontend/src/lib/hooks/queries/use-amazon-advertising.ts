import { useQuery, useMutation, UseQueryResult, UseMutationResult } from '@tanstack/react-query';
import { useAuth } from '@/lib/context/AuthContext';

// Get the backend URL from environment variables
const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL;

export type AdvertisingProfile = {
  profileId: string;
  profile_id?: string; // For compatibility
  countryCode?: string;
  currencyCode?: string;
  dailyBudget?: number;
  timezone?: string;
  accountInfo?: {
    marketplaceStringId?: string;
    id?: string;
    type?: string;
    name?: string;
  };
  profileName?: string;
  accountId?: string;
  status?: string;
};

type ConnectAmazonPayload = {
  userId: string;
  region?: string;
  scopes?: string;
};

type ConnectAmazonResponse = {
  authorization_url: string;
  state: string;
};

/**
 * Hook to fetch Amazon Advertising profiles
 */
export const useAmazonAdvertisingProfiles = (): UseQueryResult<AdvertisingProfile[], Error> => {
  const { user } = useAuth();

  return useQuery({
    queryKey: ['amazon-advertising-profiles'],
    queryFn: async () => {
      if (!user) {
        throw new Error('User not authenticated');
      }

      // Get the user's ID token for authentication
      const idToken = await user.getIdToken();
      
      // Use the exact backend API path from the sample code
      const response = await fetch(`/api/amazon/advertising/profiles`, {
        headers: {
          'Authorization': `Bearer ${idToken}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        const contentType = response.headers.get('content-type');
        
        if (contentType && contentType.includes('application/json')) {
          const errorData = await response.json();
          throw new Error(errorData.error || 'Failed to fetch advertising profiles');
        } else {
          throw new Error(`Server error: ${response.status}`);
        }
      }
      
      return await response.json();
    },
    enabled: !!user, // Enable if user is authenticated
    retry: 2,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  });
};

/**
 * Hook to connect Amazon Advertising account
 */
export const useConnectAmazonAdvertising = (): UseMutationResult<ConnectAmazonResponse, Error, ConnectAmazonPayload> => {
  return useMutation({
    mutationFn: async (payload: ConnectAmazonPayload) => {
      const { userId, region = 'EU', scopes = 'advertising::campaign_management' } = payload;
      
      // Format scopes exactly as shown in the curl example (single scope)
      const encodedScopes = encodeURIComponent(scopes.split(',')[0]); // Take first scope if multiple
      
      // Match exactly the curl command format
      const url = `/api/amazon/advertising/auth/init?region=${region}&scopes=${encodedScopes}&user_id=${userId}`;
      console.log(`Connecting to Amazon Advertising API: ${url}`);
      
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        const contentType = response.headers.get('content-type');
        
        if (contentType && contentType.includes('application/json')) {
          const errorData = await response.json();
          throw new Error(errorData.error || 'Failed to start Amazon Advertising authorization');
        } else {
          throw new Error(`Server error: ${response.status}`);
        }
      }
      
      return await response.json();
    }
  });
}; 