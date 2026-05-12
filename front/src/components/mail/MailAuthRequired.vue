<template>
   <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-8 text-center">
      <div class="mb-4">
         <svg
            class="w-16 h-16 mx-auto text-yellow-600"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
         >
            <path
               stroke-linecap="round"
               stroke-linejoin="round"
               stroke-width="2"
               d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
            ></path>
         </svg>
      </div>
      <h2 class="text-xl font-semibold text-gray-800 mb-2">
         {{ t('mail.authorizationRequired') }}
      </h2>
      <p class="text-gray-600 mb-6">{{ t('mail.authorizeMessage') }}</p>
      <button
         @click="$emit('authorize')"
         :disabled="isAuthorizingGmail"
         class="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed font-medium"
      >
         {{ isAuthorizingGmail ? t('mail.authorizing') : t('mail.authorizeButton') }}
      </button>
      <div v-if="errorMessage" class="mt-4 text-red-600 text-sm">
         {{ errorMessage }}
      </div>
   </div>
</template>

<script setup lang="ts">
import { useI18n } from '../../i18n/useI18n';

const { t } = useI18n();

defineProps<{
   isAuthorizingGmail: boolean;
   errorMessage: string;
}>();

defineEmits<{
   authorize: [];
}>();
</script>
