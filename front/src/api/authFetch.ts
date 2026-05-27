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
   init: RequestInit = {},
   tokenOverride?: string
): Promise<Response> {
   const token =
      tokenOverride ?? (await (await import('../stores/auth')).useAuth().getValidToken());

   const mergedHeaders = {
      ...toHeadersObject(init.headers),
      Authorization: `Bearer ${token}`,
   };

   return fetch(input, {
      ...init,
      headers: mergedHeaders,
   });
}
