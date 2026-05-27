export type AuthUser = {
   id: string;
   role?: string | null;
};

export type AuthUserResponse = {
   user?: AuthUser;
};

export async function fetchAuthUser(token: string): Promise<AuthUserResponse> {
   const res = await fetch('/api/auth/user', {
      headers: {
         Authorization: `Bearer ${token}`,
      },
   });

   const data = await res.json();

   if (!res.ok) {
      throw new Error(data?.message || 'Failed to fetch authenticated user.');
   }

   return data;
}
