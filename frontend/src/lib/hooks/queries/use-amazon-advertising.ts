import { useQuery, useMutation, UseQueryResult, UseMutationResult } from '@tanstack/react-query';
import { useAuth } from '@/lib/context/AuthContext';

// Get the backend URL from environment variables
const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL;

type AdvertisingProfile = {
  profileId: string;
  accountInfo?: {
    marketplaceStringId?: string;
    id?: string;
    name?: string;
  };
  error?: string;
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
 * NOTE: This is currently disabled as the backend integration is still being set up
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
      
      // Use the backend URL with the correct API path
      const response = await fetch(`${BACKEND_URL}/api/v1/amazon/advertising/profiles`, {
        headers: {
          'Authorization': `Bearer ${idToken}`
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
    enabled: false, // Disabled for now until backend is ready
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
      
      const response = await fetch(`/api/amazon/advertising/auth/init?user_id=${userId}&region=${region}&scopes=${scopes}`);
      
      if (!response.ok) {
        const contentType = response.headers.get('content-type');
        
        if (contentType && contentType.includes('application/json')) {
          const errorData = await response.json();
          throw new Error(errorData.error || 'Failed to initialize Amazon Advertising authorization');
        } else {
          throw new Error(`Server error: ${response.status}`);
        }
      }
      
      return await response.json();
    }
  });
}; 