// API client for /api/profile
import type { Ref } from 'vue';

export interface Profile {
   id: string;
   email: string;
   full_name?: string;
}

export async function fetchProfile(token: string): Promise<Profile> {
   const res = await fetch('/api/profile', {
      headers: {
         Authorization: `Bearer ${token}`,
      },
   });
   if (!res.ok) throw new Error('Erreur lors de la récupération du profil');
   return await res.json();
}

export async function updateProfile(
   token: string,
   data: Partial<Pick<Profile, 'full_name'>>
): Promise<Profile> {
   const res = await fetch('/api/profile', {
      method: 'PUT',
      headers: {
         Authorization: `Bearer ${token}`,
         'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
   });
   if (!res.ok) throw new Error('Erreur lors de la mise à jour du profil');
   return await res.json();
}
