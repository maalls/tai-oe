// API client for /api/profile

import { authFetch } from './authFetch';

export interface Profile {
   id: string;
   email: string;
   full_name?: string;
}

export async function fetchProfile(token: string): Promise<Profile> {
   const res = await authFetch('/api/profile', {}, token);
   if (!res.ok) throw new Error('Erreur lors de la récupération du profil');
   return await res.json();
}

export async function updateProfile(
   token: string,
   data: Partial<Pick<Profile, 'full_name'>>
): Promise<Profile> {
   const res = await authFetch(
      '/api/profile',
      {
         method: 'PUT',
         headers: {
            'Content-Type': 'application/json',
         },
         body: JSON.stringify(data),
      },
      token
   );
   if (!res.ok) throw new Error('Erreur lors de la mise à jour du profil');
   return await res.json();
}
