const rawApiBaseUrl = import.meta.env.VITE_API_URL;

if (!rawApiBaseUrl || !rawApiBaseUrl.trim()) {
   throw new Error('Missing required environment variable: VITE_API_URL');
}

const localHostPattern = /^https?:\/\/(localhost|127\.0\.0\.1)(:\d+)?(\/|$)/i;
const isBrowser = typeof window !== 'undefined';
const isLocalUiHost =
   isBrowser &&
   (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1');
const isLocalApiHost = localHostPattern.test(rawApiBaseUrl);
const forceProxy = import.meta.env.DEV || import.meta.env.VITE_API_USE_PROXY === 'true';
const useProxyRouting =
   forceProxy || !rawApiBaseUrl.startsWith('http') || (isLocalUiHost && isLocalApiHost);

function normalizeApiOrigin(baseUrl: string): string {
   const trimmed = baseUrl.replace(/\/$/, '');
   return trimmed.endsWith('/api') ? trimmed.slice(0, -4) : trimmed;
}

const normalizedApiOrigin = rawApiBaseUrl.startsWith('http')
   ? normalizeApiOrigin(rawApiBaseUrl)
   : '';

/**
 * Generate API URL with /api path prefix
 * - Dev (localhost): relative path /api/... (proxied by Vite to http://localhost:8080)
 * - Production: full URL with /api prefix
 *
 * Usage: apiUrl('embeddings') → /api/embeddings or https://gme.ai-oe.co/api/embeddings
 */
export function apiUrl(path: string): string {
   const normalizedPath = path.startsWith('/') ? path : `/${path}`;

   // Use same-origin proxy routing in local/dev for stable browser networking.
   if (useProxyRouting) {
      return `/api${normalizedPath}`;
   }

   return `${normalizedApiOrigin}/api${normalizedPath}`;
}

// Base origin used only by modules that append their own /api/... path.
export const API_BASE_URL = useProxyRouting ? '' : normalizedApiOrigin;
