<template>
   <div class="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div class="max-w-md w-full space-y-8">
         <div>
            <h2 class="mt-6 text-center text-3xl font-extrabold text-gray-900">
               Reset your password
            </h2>
         </div>

         <div v-if="statusMessage" class="rounded-md bg-blue-50 p-4">
            <p class="text-sm text-blue-800">{{ statusMessage }}</p>
         </div>

         <div v-if="errorMessage" class="rounded-md bg-red-50 p-4">
            <p class="text-sm text-red-800">{{ errorMessage }}</p>
         </div>

         <form v-if="canReset" class="mt-8 space-y-6" @submit.prevent="handleSubmit">
            <div class="rounded-md shadow-sm -space-y-px">
               <div>
                  <label for="password" class="sr-only">New password</label>
                  <input
                     id="password"
                     v-model="password"
                     name="password"
                     type="password"
                     autocomplete="new-password"
                     required
                     minlength="8"
                     class="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
                     placeholder="New password"
                  />
               </div>
               <div>
                  <label for="confirm-password" class="sr-only">Confirm password</label>
                  <input
                     id="confirm-password"
                     v-model="confirmPassword"
                     name="confirm-password"
                     type="password"
                     autocomplete="new-password"
                     required
                     minlength="8"
                     class="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
                     placeholder="Confirm new password"
                  />
               </div>
            </div>

            <div>
               <button
                  type="submit"
                  :disabled="isSubmitting"
                  class="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
               >
                  {{ isSubmitting ? 'Updating...' : 'Update password' }}
               </button>
            </div>
         </form>

         <div class="text-center">
            <button class="text-sm text-blue-600 hover:text-blue-500" @click="goToLogin">
               Back to login
            </button>
         </div>
      </div>
   </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { supabase } from '../../lib/supabase';

const router = useRouter();

const password = ref('');
const confirmPassword = ref('');
const isSubmitting = ref(false);
const canReset = ref(false);
const errorMessage = ref('');
const statusMessage = ref('');

function getHashParams() {
   const hash = window.location.hash.startsWith('#')
      ? window.location.hash.slice(1)
      : window.location.hash;
   return new URLSearchParams(hash);
}

function goToLogin() {
   router.push('/login');
}

onMounted(async () => {
   const hashParams = getHashParams();
   const hashError = hashParams.get('error_description') || hashParams.get('error');

   if (hashError) {
      errorMessage.value = decodeURIComponent(hashError.replace(/\+/g, ' '));
      canReset.value = false;
      return;
   }

   const {
      data: { session },
   } = await supabase.auth.getSession();

   if (!session) {
      errorMessage.value = 'This password reset link is invalid or has expired.';
      canReset.value = false;
      return;
   }

   canReset.value = true;
   statusMessage.value = 'Enter your new password.';
});

async function handleSubmit() {
   errorMessage.value = '';
   statusMessage.value = '';

   if (password.value.length < 8) {
      errorMessage.value = 'Password must be at least 8 characters long.';
      return;
   }

   if (password.value !== confirmPassword.value) {
      errorMessage.value = 'Passwords do not match.';
      return;
   }

   isSubmitting.value = true;
   try {
      const { error } = await supabase.auth.updateUser({ password: password.value });
      if (error) {
         throw error;
      }

      statusMessage.value = 'Password updated successfully. You can now sign in.';
      canReset.value = false;
      window.history.replaceState({}, document.title, '/reset-password');
   } catch (error: any) {
      errorMessage.value = error?.message || 'Failed to update password.';
   } finally {
      isSubmitting.value = false;
   }
}
</script>
