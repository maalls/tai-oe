<template>
   <form @submit.prevent="onSubmit" class="space-y-4">
      <div class="grid grid-cols-1 md:grid-cols-4 gap-3">
         <input
            v-model="email"
            type="email"
            placeholder="Email"
            class="border rounded px-3 py-2"
            :disabled="isCreating"
            required
         />
         <input
            v-model="fullName"
            type="text"
            placeholder="Full name"
            class="border rounded px-3 py-2"
            :disabled="isCreating"
         />
         <input
            v-model="password"
            type="password"
            placeholder="Temporary password"
            class="border rounded px-3 py-2"
            :disabled="isCreating"
            required
         />
         <select v-model="role" class="border rounded px-3 py-2 bg-white" :disabled="isCreating">
            <option value="user">user</option>
            <option value="admin">admin</option>
         </select>
      </div>
      <div class="flex justify-end">
         <button
            type="submit"
            class="px-3 py-2 bg-slate-900 text-white rounded hover:bg-slate-800 transition disabled:opacity-50"
            :disabled="isCreating"
         >
            Add user
         </button>
      </div>
      <p
         v-if="errorMessage"
         class="text-sm text-red-700 bg-red-50 border border-red-200 rounded p-3 mt-2"
      >
         {{ errorMessage }}
      </p>
      <p
         v-if="successMessage"
         class="text-sm text-green-700 bg-green-50 border border-green-200 rounded p-3 mt-2"
      >
         {{ successMessage }}
      </p>
   </form>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import { useAdminUsers } from './useAdminUsers';
import type { AdminUserRole } from '../../../../api/adminUsers';
import { useAuth } from '../../../../stores/auth';

const emit = defineEmits(['created']);
const router = useRouter();

const { getValidToken } = useAuth();
const { isCreating, errorMessage, successMessage, addUser } = useAdminUsers({ getValidToken });

const email = ref('');
const fullName = ref('');
const password = ref('');
const role = ref<AdminUserRole>('user');

const onSubmit = async () => {
   await addUser({
      email: email.value,
      password: password.value,
      full_name: fullName.value,
      role: role.value,
   });
   if (!errorMessage.value) {
      emit('created');
      router.push({ name: 'admin-users' });
   }
};

watch(successMessage, (val) => {
   if (val) {
      email.value = '';
      fullName.value = '';
      password.value = '';
      role.value = 'user';
   }
});
</script>
