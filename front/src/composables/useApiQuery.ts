import { apiUrl } from '../utils/api';
import { authFetch } from '../api/authFetch';

type QueryValue = string | number | boolean | null | undefined;

export function useApiQuery() {
   async function fetchApiJson<T>(
      path: string,
      query: Record<string, QueryValue> = {}
   ): Promise<T> {
      const url = new URL(apiUrl(path), window.location.origin);

      Object.entries(query).forEach(([key, value]) => {
         if (value !== null && value !== undefined && value !== '') {
            url.searchParams.set(key, String(value));
         }
      });

      const response = await authFetch(url.toString());

      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
         const message =
            payload?.message || payload?.error || `Request failed with status ${response.status}`;
         throw new Error(message);
      }

      return payload as T;
   }

   return {
      fetchApiJson,
   };
}
