import { apiUrl } from '../utils/api';
import { apiFetch } from './apiFetch';

export async function getOutlookStatus(userId: string): Promise<any> {
   const query = new URLSearchParams({ user_id: userId || '' });
   const url = `${apiUrl('outlook/status')}?${query.toString()}`;

   const res = await apiFetch(url);
   const data = await res.json();

   if (!res.ok) {
      throw new Error(data?.message || 'Failed to load Outlook status.');
   }

   return data;
}

export async function getOutlookProfile(userId: string): Promise<any> {
   const query = new URLSearchParams({ user_id: userId || '' });
   const url = `${apiUrl('outlook/profile')}?${query.toString()}`;

   const res = await apiFetch(url);
   const data = await res.json();

   if (!res.ok || data?.status !== 'ok') {
      throw new Error(data?.message || 'Failed to load Outlook profile.');
   }

   return data;
}

export async function startOutlookOAuth(redirectUrl: string, userId: string): Promise<string> {
   const query = new URLSearchParams({
      redirect_url: redirectUrl,
      user_id: userId || '',
   });
   const url = `${apiUrl('outlook/oauth/start')}?${query.toString()}`;

   const res = await apiFetch(url);
   const data = await res.json();

   if (!res.ok || data?.status !== 'ok' || !data?.auth_url) {
      throw new Error(data?.message || 'Outlook authorization failed.');
   }

   return data.auth_url;
}

export async function revokeOutlook(userId: string): Promise<any> {
   const query = new URLSearchParams({ user_id: userId || '' });
   const url = `${apiUrl('outlook/revoke')}?${query.toString()}`;

   const res = await apiFetch(url, { method: 'POST' });
   const data = await res.json();

   if (!res.ok || data?.status !== 'ok') {
      throw new Error(data?.message || 'Outlook disconnect failed.');
   }

   return data;
}
