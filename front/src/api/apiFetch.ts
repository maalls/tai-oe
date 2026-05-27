export async function apiFetch(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
   if (typeof init === 'undefined') {
      return fetch(input);
   }
   return fetch(input, init);
}
