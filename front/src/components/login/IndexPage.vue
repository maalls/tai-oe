<template>
   <div class="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div class="max-w-md w-full space-y-8">
         <div>
            <h2 class="mt-6 text-center text-3xl font-extrabold text-gray-900">
               {{ t('login.signIn') }}
            </h2>
         </div>
         <form class="mt-8 space-y-6" @submit.prevent="handleSubmit">
            <div v-if="error" class="rounded-md bg-red-50 p-4">
               <p class="text-sm text-red-800">{{ error }}</p>
            </div>
            <div class="rounded-md shadow-sm -space-y-px">
               <div>
                  <label for="email" class="sr-only">{{ t('login.emailAddress') }}</label>
                  <input
                     id="email"
                     v-model="email"
                     name="email"
                     type="email"
                     autocomplete="email"
                     required
                     class="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
                     :placeholder="t('login.emailAddress')"
                  />
               </div>
               <div>
                  <label for="password" class="sr-only">{{ t('login.password') }}</label>
                  <input
                     id="password"
                     v-model="password"
                     name="password"
                     type="password"
                     autocomplete="current-password"
                     required
                     class="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
                     :placeholder="t('login.password')"
                  />
               </div>
            </div>

            <div>
               <button
                  type="submit"
                  :disabled="isSubmitting"
                  class="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
               >
                  {{ isSubmitting ? t('login.pleaseWait') : t('login.signInButton') }}
               </button>
            </div>
         </form>
      </div>
   </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useAuth } from '../../stores/auth';
import { useI18n } from '../../i18n/useI18n';

const router = useRouter();
const { signIn } = useAuth();
const { t } = useI18n();

const email = ref('');
const password = ref('');
const isSubmitting = ref(false);
const error = ref('');

async function handleSubmit() {
   isSubmitting.value = true;
   error.value = '';

   try {
      await signIn(email.value, password.value);
      router.push('/');
   } catch (err: any) {
      error.value = err.message || t('login.errorOccurred');
   } finally {
      isSubmitting.value = false;
   }
}
</script>
