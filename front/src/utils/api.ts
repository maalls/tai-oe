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

   // Relative base (/api): rely on same-origin/proxy routing.
   if (!rawApiBaseUrl.startsWith('http')) {
      return `/api${normalizedPath}`;
   }

   // Absolute base: call backend directly and avoid duplicate /api/api paths.
   let baseUrl = rawApiBaseUrl.replace(/\/$/, '');
   if (baseUrl.endsWith('/api')) {
      baseUrl = baseUrl.slice(0, -4);
   }
   return `${baseUrl}/api${normalizedPath}`;
}

// Export for debugging/reference
export const API_BASE_URL = rawApiBaseUrl;
