import { useAuth } from '../stores/auth';

function toHeadersObject(headers?: HeadersInit): Record<string, string> {
   if (!headers) {
      return {};
   }

   if (headers instanceof Headers) {
      return Object.fromEntries(headers.entries());
   }

   if (Array.isArray(headers)) {
      return Object.fromEntries(headers);
   }

   return { ...headers };
}

export async function authFetch(
   input: RequestInfo | URL,
   init: RequestInit = {}
): Promise<Response> {
   const { getValidToken } = useAuth();
   const token = await getValidToken();

   const mergedHeaders = {
      ...toHeadersObject(init.headers),
      Authorization: `Bearer ${token}`,
   };

   return fetch(input, {
      ...init,
      headers: mergedHeaders,
   });
}
