import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig, AxiosHeaders } from 'axios';
import axiosRetry from 'axios-retry';
import { auth } from '@/lib/firebase';

// Environment-aware base URL determination
const isDevelopment = process.env.NODE_ENV === 'development';
export const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 
  (isDevelopment ? "http://localhost:8000/" : "https://django-backend-epcse2awb3cyh5e8.centralindia-01.azurewebsites.net/");

// Log API URL for debugging
console.log(`API base URL: ${API_BASE_URL} (${isDevelopment ? 'development' : 'production'})`);

// Default timeout value for consistency across the app
export const DEFAULT_TIMEOUT = 30000;
export const LONG_OPERATION_TIMEOUT = 300000; // Increased from 100000ms to 300000ms (5 minutes)

// Create axios instance with default config
export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
  timeout: DEFAULT_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add retry logic
// axiosRetry(apiClient, {
//   retries: 3,
//   retryDelay: axiosRetry.exponentialDelay,
//   retryCondition: (error: AxiosError) => {
//     return axiosRetry.isNetworkOrIdempotentRequestError(error) ||
//            (error.response?.status ? error.response.status >= 500 : false);
//   }
// });

// Authentication interceptor
apiClient.interceptors.request.use(
  async (config: InternalAxiosRequestConfig) => {
    try {
      const currentUser = auth?.currentUser;
      if (currentUser) {
        const token = await currentUser.getIdToken();
        if (!config.headers) {
          config.headers = new AxiosHeaders();
        }
        config.headers.set('Authorization', `Bearer ${token}`);
      }
    } catch (error) {
      console.error('Error getting auth token:', error);
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for auth errors
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Redirect to login page if unauthorized
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// CSRF token management
let csrfToken: string | null = null;

const getCsrfToken = async (): Promise<string> => {
  if (!csrfToken) {
    const response = await apiClient.get('get_csrf/', { timeout: DEFAULT_TIMEOUT });
    if (response.data?.csrfToken) {
      csrfToken = response.data.csrfToken;
    } else {
      throw new Error('No CSRF token in response');
    }
  }
  if (!csrfToken) {
    throw new Error('Failed to get CSRF token');
  }
  return csrfToken;
};

// Request interceptor to add CSRF token
apiClient.interceptors.request.use(
  async (config: InternalAxiosRequestConfig) => {
    if (config.method !== 'get') {
      try {
        const token = await getCsrfToken();
        if (!config.headers) {
          config.headers = new axios.AxiosHeaders();
        }
        config.headers['X-CSRFToken'] = token;
      } catch (error) {
        console.error('Failed to get CSRF token:', error);
        throw error;
      }
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

export { getCsrfToken }; 