import { authFetch } from './authFetch';

export type AuthUser = {
   id: string;
   role?: string | null;
};

export type AuthUserResponse = {
   user?: AuthUser;
};

export async function fetchAuthUser(token: string): Promise<AuthUserResponse> {
   const res = await authFetch('/api/auth/user', {}, token);

   const data = await res.json();

   if (!res.ok) {
      throw new Error(data?.message || 'Failed to fetch authenticated user.');
   }

   return data;
}
