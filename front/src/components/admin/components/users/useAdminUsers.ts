import { ref } from 'vue';

import {
   listAdminUsers,
   updateAdminUserRole,
   type AdminUser,
   type AdminUserRole,
} from '../../../../api/adminUsers';

type UseAdminUsersDeps = {
   getValidToken?: () => Promise<string>;
   listUsers?: (token: string) => Promise<{ users: AdminUser[] }>;
   updateUserRole?: (
      token: string,
      userId: string,
      role: AdminUserRole
   ) => Promise<{ user: AdminUser }>;
};

export const useAdminUsers = (deps: UseAdminUsersDeps = {}) => {
   if (!deps.getValidToken) {
      throw new Error('Missing getValidToken dependency.');
   }

   const getValidToken = deps.getValidToken;
   const listUsers = deps.listUsers ?? listAdminUsers;
   const updateUserRole = deps.updateUserRole ?? updateAdminUserRole;

   const users = ref<AdminUser[]>([]);
   const isLoading = ref(false);
   const isUpdating = ref(false);
   const updatingUserId = ref<string | null>(null);
   const errorMessage = ref('');
   const successMessage = ref('');

   const loadUsers = async () => {
      isLoading.value = true;
      errorMessage.value = '';
      successMessage.value = '';

      try {
         const token = await getValidToken();
         const payload = await listUsers(token);
         users.value = payload.users || [];
      } catch (error) {
         users.value = [];
         errorMessage.value = error instanceof Error ? error.message : 'Failed to load users.';
      } finally {
         isLoading.value = false;
      }
   };

   const changeRole = async (userId: string, role: AdminUserRole) => {
      isUpdating.value = true;
      updatingUserId.value = userId;
      errorMessage.value = '';
      successMessage.value = '';

      try {
         const token = await getValidToken();
         const payload = await updateUserRole(token, userId, role);
         users.value = users.value.map((user) =>
            user.id === userId ? { ...user, role: payload.user.role } : user
         );
         successMessage.value = 'Role updated successfully.';
      } catch (error) {
         errorMessage.value = error instanceof Error ? error.message : 'Failed to update role.';
      } finally {
         isUpdating.value = false;
         updatingUserId.value = null;
      }
   };

   return {
      users,
      isLoading,
      isUpdating,
      updatingUserId,
      errorMessage,
      successMessage,
      loadUsers,
      changeRole,
   };
};
