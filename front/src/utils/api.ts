const rawApiBaseUrl = import.meta.env.VITE_API_URL;

if (!rawApiBaseUrl || !rawApiBaseUrl.trim()) {
   throw new Error('Missing required environment variable: VITE_API_URL');
}

export const API_BASE_URL = rawApiBaseUrl.replace(/\/$/, '');

export function apiUrl(path: string): string {
   const normalizedPath = path.startsWith('/') ? path : `/${path}`;
   return `${API_BASE_URL}${normalizedPath}`;
}
