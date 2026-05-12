<template>
   <div class="cursor-pointer">
      <div @click="$emit('expand', message.id)" class="p-4">
         <div class="flex items-start justify-between mb-2">
            <div class="flex-1 min-w-0">
               <div class="flex items-center gap-2 mb-1">
                  <p class="font-semibold text-gray-900 truncate">
                     {{
                        message.from_name
                           ? message.from_name
                           : message.from_email
                             ? message.from_email
                             : message.from_raw
                     }}

                     <span class="text-sm font-medium">{{ message.subject }}</span>
                  </p>
               </div>
               <!--p class="text-sm text-gray-600 truncate">To: {{ message.to }}</p-->
               <p v-if="message.cc_email" class="text-sm text-gray-600 truncate">
                  {{ t('mail.ccLabel') }}: {{ message.cc_email }}
               </p>
               <!--p class="text-xs">id:{{ message.id }}</p-->

               <p class="text-xs">{{ message.classification_reason }}</p>
               <div class="mt-4 flex items-center gap-2">
                  <button
                     @click="goToCategory($event, message.category || message.category_suggestion)"
                     v-bind:class="{
                        'bg-gray-100 text-gray-700': message.category == 'Other',
                     }"
                     class="inline-block px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:opacity-80 transition-opacity cursor-pointer"
                  >
                     {{
                        message.category !== 'Other'
                           ? message.category
                           : message.category_suggestion
                     }}
                  </button>
                  <!-- Opportunities badge -->
                  <button
                     v-if="message.opportunities && message.opportunities.length > 0"
                     @click="goToOpportunities($event, message)"
                     class="inline-block px-2 py-1 text-xs rounded hover:opacity-80 transition-opacity cursor-pointer"
                     :class="
                        message.opportunities.length === 1
                           ? 'bg-green-100 text-green-700'
                           : 'bg-red-100 text-red-700'
                     "
                  >
                     {{
                        message.opportunities.length === 1
                           ? formatStageLabel(message.opportunities[0]!.stage || '')
                           : t('mail.opportunitiesCount', {
                                count: message.opportunities.length,
                             })
                     }}
                  </button>
                  <!-- Create opportunity button (when no opportunities exist) -->
                  <button
                     v-else-if="message.category == 'RFQ'"
                     @click="$emit('create-opportunity', message.id)"
                     :disabled="isCreatingOpportunity"
                     class="inline-flex items-center gap-1 px-2 py-1 text-xs bg-amber-100 text-amber-700 rounded hover:opacity-80 transition-opacity cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                     <svg
                        v-if="isCreatingOpportunity"
                        class="animate-spin h-3 w-3"
                        xmlns="http://www.w3.org/2000/svg"
                        fill="none"
                        viewBox="0 0 24 24"
                     >
                        <circle
                           class="opacity-25"
                           cx="12"
                           cy="12"
                           r="10"
                           stroke="currentColor"
                           stroke-width="4"
                        ></circle>
                        <path
                           class="opacity-75"
                           fill="currentColor"
                           d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                        ></path>
                     </svg>
                     <span>{{
                        isCreatingOpportunity
                           ? t('mail.creatingOpportunity')
                           : t('mail.createOpportunity')
                     }}</span>
                  </button>
               </div>
            </div>

            <div class="flex items-start gap-2 ml-4">
               <span class="text-xs text-gray-500 whitespace-nowrap">{{
                  message.email_date ? formatDate(message.email_date!) : ''
               }}</span>
               <!-- Dropdown Menu -->
               <MailItemMenu
                  :isClassifying="isClassifying"
                  :isCreatingOpportunity="isCreatingOpportunity"
                  :messageId="message.id"
                  :provider="message.provider"
                  :providerMessageId="message.provider_message_id"
                  :contactId="message.contact_id"
                  :accountId="message.account_id"
                  @classify="$emit('classify', message.id)"
                  @create-opportunity="$emit('create-opportunity', message.id)"
                  @resync="
                     message.provider_message_id
                        ? $emit('resync', message.id, message.provider_message_id)
                        : null
                  "
                  @delete="$emit('delete', message.id)"
               />
            </div>
         </div>

         <p class="text-sm text-gray-600 line-clamp-2">{{ message.snippet }}</p>
      </div>
   </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router';
import { useI18n } from '../../i18n/useI18n';
import MailItemMenu from './MailItemMenu.vue';
import type { MailMessage } from '../../types/mail';

const router = useRouter();
const { t, locale } = useI18n();

defineProps<{
   message: MailMessage;
   isClassifying?: boolean;
   isCreatingOpportunity?: boolean;
}>();

defineEmits<{
   expand: [messageId: string];
   classify: [messageId: string];
   'create-opportunity': [messageId: string];
   resync: [messageId: string, providerMessageId: string];
   delete: [messageId: string];
}>();

const goToOpportunities = (event: Event, message: MailMessage) => {
   event.stopPropagation();

   // If there's only 1 opportunity, go directly to it
   if (message.opportunities && message.opportunities.length === 1) {
      router.push(`/opportunities/${message.opportunities[0]!.id}/quote`);
      return;
   }

   // Otherwise go to filtered opportunities list
   router.push(`/opportunities?source_reference_id=${encodeURIComponent(message.id)}`);
};

const goToCategory = (event: Event, category: string | undefined) => {
   event.stopPropagation();
   if (category) {
      router.push(`/mail/${encodeURIComponent(category)}`);
   }
};

const formatStageLabel = (stage: string) => {
   if (!stage) return '';
   const key = `opportunities.stages.${stage}`;
   const translated = t(key);
   return translated === key ? stage : translated;
};

const formatDate = (date: string): string => {
   try {
      const dateObj = new Date(date);

      const now = new Date();
      const isToday =
         dateObj.getFullYear() === now.getFullYear() &&
         dateObj.getMonth() === now.getMonth() &&
         dateObj.getDate() === now.getDate();

      // If the date string has timezone info, use that timezone
      // Otherwise fall back to user's local timezone
      const timeZone = false
         ? 'UTC' // The timezone is already in the ISO string as offset
         : Intl.DateTimeFormat().resolvedOptions().timeZone; // Use local timezone

      if (isToday) {
         return dateObj.toLocaleString(locale.value === 'fr' ? 'fr-FR' : 'en-US', {
            hour: '2-digit',
            minute: '2-digit',
            timeZone,
         });
      }

      return dateObj.toLocaleString(locale.value === 'fr' ? 'fr-FR' : 'en-US', {
         month: 'short',
         day: 'numeric',
         timeZone,
      });
   } catch {
      return date;
   }
};
</script>
