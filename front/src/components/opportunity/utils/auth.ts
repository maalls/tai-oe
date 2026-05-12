import { useAuth } from '../../../stores/auth';

export const buildAuthHeaders = async (includeJson = true) => {
   const { getValidToken } = useAuth();
   const headers: HeadersInit = includeJson ? { 'Content-Type': 'application/json' } : {};
   const token = await getValidToken();
   headers['Authorization'] = `Bearer ${token}`;
   return headers;
};
