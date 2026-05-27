import { apiUrl } from '../utils/api';

export type AdminUserRole = 'admin' | 'user';

export interface AdminUser {
   id: string;
   email: string;
   full_name?: string | null;
   role: AdminUserRole;
   created_at: string;
}

export interface ListAdminUsersResponse {
   users: AdminUser[];
}

export interface UpdateAdminUserRoleResponse {
   user: AdminUser;
}

export async function listAdminUsers(
   token: string,
   limit = 50,
   offset = 0
): Promise<ListAdminUsersResponse> {
   const query = new URLSearchParams({
      limit: String(limit),
      offset: String(offset),
   });
   const url = `${apiUrl('admin/users')}?${query.toString()}`;

   const res = await fetch(url, {
      headers: {
         Authorization: `Bearer ${token}`,
      },
   });
   const data = await res.json();

   if (!res.ok) {
      throw new Error(data?.message || 'Failed to load admin users.');
   }

   return data;
}

export async function updateAdminUserRole(
   token: string,
   userId: string,
   role: AdminUserRole
): Promise<UpdateAdminUserRoleResponse> {
   const url = apiUrl(`admin/users/${userId}/role`);

   const res = await fetch(url, {
      method: 'PATCH',
      headers: {
         Authorization: `Bearer ${token}`,
         'Content-Type': 'application/json',
      },
      body: JSON.stringify({ role }),
   });
   const data = await res.json();

   if (!res.ok) {
      throw new Error(data?.message || 'Failed to update user role.');
   }

   return data;
}
