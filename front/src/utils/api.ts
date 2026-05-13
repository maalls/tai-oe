const rawApiBaseUrl = import.meta.env.VITE_API_URL;

if (!rawApiBaseUrl || !rawApiBaseUrl.trim()) {
   throw new Error('Missing required environment variable: VITE_API_URL');
}

/**
 * Generate API URL with /api path prefix
 * - Dev (localhost): relative path /api/... (proxied by Vite to http://localhost:8080)
 * - Production: full URL with /api prefix
 * 
 * Usage: apiUrl('embeddings') → /api/embeddings or https://gme.ai-oe.co/api/embeddings
 */
export function apiUrl(path: string): string {
   const normalizedPath = path.startsWith('/') ? path : `/${path}`;
   const isDev = import.meta.env.DEV;
   const isLocalhost = rawApiBaseUrl.includes('localhost');
   
   if (isLocalhost) {
      // Localhost: use relative /api path for Vite proxy (dev or preview)
      return `/api${normalizedPath}`;
   }
   
   // Production: use full URL with /api prefix
   const baseUrl = rawApiBaseUrl.replace(/\/$/, '');
   return `${baseUrl}/api${normalizedPath}`;
}

// Export for debugging/reference
export const API_BASE_URL = rawApiBaseUrl;
