<template>
   <div>
      <AdminNavHeader />
      <div class="p-6 space-y-4">
         <div class="flex items-center justify-between gap-4">
            <h1 class="text-2xl font-bold">Users</h1>
            <button
               type="button"
               class="px-4 py-2 bg-slate-900 text-white rounded-md hover:bg-slate-800 transition"
               :disabled="isLoading"
               @click="reload"
            >
               Refresh
            </button>
         </div>

         <p v-if="errorMessage" class="text-sm text-red-700 bg-red-50 border border-red-200 rounded p-3">
            {{ errorMessage }}
         </p>
         <p
            v-if="successMessage"
            class="text-sm text-green-700 bg-green-50 border border-green-200 rounded p-3"
         >
            {{ successMessage }}
         </p>

         <div v-if="isLoading" class="text-gray-600">Loading users...</div>

         <div v-else class="overflow-x-auto bg-white rounded-lg border border-gray-200">
            <table class="min-w-full text-sm">
               <thead class="bg-gray-50 text-gray-700">
                  <tr>
                     <th class="px-4 py-3 text-left font-semibold">Email</th>
                     <th class="px-4 py-3 text-left font-semibold">Name</th>
                     <th class="px-4 py-3 text-left font-semibold">Role</th>
                     <th class="px-4 py-3 text-left font-semibold">Created</th>
                     <th class="px-4 py-3 text-right font-semibold">Actions</th>
                  </tr>
               </thead>
               <tbody>
                  <tr
                     v-for="user in users"
                     :key="user.id"
                     class="border-t border-gray-100 hover:bg-gray-50"
                  >
                     <td class="px-4 py-3">{{ user.email }}</td>
                     <td class="px-4 py-3">{{ user.full_name || '-' }}</td>
                     <td class="px-4 py-3">
                        <select
                           v-model="draftRoles[user.id]"
                           class="border rounded px-2 py-1 bg-white"
                           :disabled="isUpdating && updatingUserId === user.id"
                        >
                           <option value="user">user</option>
                           <option value="admin">admin</option>
                        </select>
                     </td>
                     <td class="px-4 py-3 text-gray-600">{{ formatDate(user.created_at) }}</td>
                     <td class="px-4 py-3 text-right">
                        <button
                           type="button"
                           class="px-3 py-1.5 bg-blue-600 text-white rounded hover:bg-blue-700 transition disabled:opacity-50"
                           :disabled="isUpdating && updatingUserId === user.id"
                           @click="applyRole(user.id)"
                        >
                           Save
                        </button>
                     </td>
                  </tr>
                  <tr v-if="!users.length">
                     <td colspan="5" class="px-4 py-8 text-center text-gray-500">No users found.</td>
                  </tr>
               </tbody>
            </table>
         </div>
      </div>
   </div>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from 'vue';

import AdminNavHeader from '../../AdminNavHeader.vue';
import { useAdminUsers } from './useAdminUsers';
import type { AdminUserRole } from '../../../../api/adminUsers';
import { useAuth } from '../../../../stores/auth';

const { getValidToken } = useAuth();

const {
   users,
   isLoading,
   isUpdating,
   updatingUserId,
   errorMessage,
   successMessage,
   loadUsers,
   changeRole,
} = useAdminUsers({ getValidToken });

const draftRoles = ref<Record<string, AdminUserRole>>({});

const syncDraftRoles = () => {
   draftRoles.value = Object.fromEntries(users.value.map((user) => [user.id, user.role]));
};

const reload = async () => {
   await loadUsers();
   syncDraftRoles();
};

const applyRole = async (userId: string) => {
   const role = draftRoles.value[userId];
   if (!role) {
      return;
   }

   await changeRole(userId, role);
};

const formatDate = (value: string) => {
   const date = new Date(value);
   if (Number.isNaN(date.getTime())) {
      return value;
   }
   return date.toLocaleDateString('fr-FR');
};

watch(
   users,
   () => {
      syncDraftRoles();
   },
   { deep: true }
);

onMounted(async () => {
   await reload();
});
</script>
