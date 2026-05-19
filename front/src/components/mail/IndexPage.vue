<template>
   <div class="container mx-auto p-8 max-w-6xl">
      <!-- Notification -->
      <MailNotification :notification="notification" />

      <!-- Not Authorized State -->
      <MailAuthRequired
         v-if="!isAuthorized && !isLoading"
         :isAuthorizingGmail="isAuthorizingGmail"
         :errorMessage="errorMessage"
         @authorize="authorizeGmail"
      />

      <!-- Loading State -->
      <MailLoader v-else-if="isLoading" />

      <!-- Messages -->
      <div v-else>
         <!-- Refresh Button -->

         <div class="mb-4 pb-4 border-b border-gray-200">
            <div class="flex flex-wrap gap-2">
               <button
                  @click="loadMessages(true)"
                  :disabled="isRefreshing"
                  :class="[
                     'px-3 py-2 text-gray-700 rounded hover:gray-200 disabled:opacity-50 transition-all',
                     isRefreshing ? 'animate-spin' : '',
                  ]"
                  :title="t('mail.refreshEmails')"
               >
                  <svg
                     xmlns="http://www.w3.org/2000/svg"
                     fill="none"
                     viewBox="0 0 24 24"
                     stroke-width="1.5"
                     stroke="currentColor"
                     class="w-5 h-5"
                  >
                     <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0 3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182m0-4.991v4.99"
                     />
                  </svg>
               </button>

               <button
                  @click="router.push('/mail')"
                  :class="[
                     'px-3 py-1 text-sm rounded transition',
                     selectedCategory === null
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-200 text-gray-700 hover:bg-gray-300',
                  ]"
               >
                  {{ t('mail.all') }} ({{ messages.length }})
               </button>
               <button
                  v-for="category in availableCategories"
                  :key="category"
                  @click="router.push(`/mail/${encodeURIComponent(category)}`)"
                  :class="[
                     'px-3 py-1 text-sm rounded transition',
                     selectedCategory === category
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-200 text-gray-700 hover:bg-gray-300',
                  ]"
               >
                  {{ category }} ({{ messages.filter((m) => m.category === category).length }})
               </button>
            </div>
         </div>

         <MailList
            :messages="filteredMessages as any"
            :expandedMessageIds="expandedIds"
            :messageBody="messageBody"
            :loadingMessageBody="loadingMessageBody"
            :messageAttachments="messageAttachments"
            :loadingAttachments="loadingAttachments"
            :classifyingEmails="classifyingEmails"
            :creatingOpportunity="creatingOpportunity"
            @expand="handleExpand"
            @classify="classifyEmail"
            @create-opportunity="createOpportunity"
            @resync="resyncEmail"
            @delete="deleteEmail"
         />
      </div>
   </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useAuth } from '../../stores/auth';
import { supabase } from '../../lib/supabase';
import { listEmailAttachments } from '../../api/email';
import MailNotification from './MailNotification.vue';
import MailAuthRequired from './MailAuthRequired.vue';
import MailLoader from './MailLoader.vue';
import MailList from './MailList.vue';
import { useI18n } from '../../i18n/useI18n';
import { apiUrl } from '../../utils/api';
import {
   setupEmailRealtimeSubscription,
   cleanupEmailRealtimeSubscription,
} from './realtimeSubscription';

const { session } = useAuth();
const { t } = useI18n();

let emailSubscription: any = null;

interface Message {
   id: string;
   provider?: string;
   provider_message_id?: string;
   threadId?: string;
   from?: string;
   from_raw?: any;
   to?: string;
   subject?: string;
   date?: string;
   snippet?: string;
   labels?: string[];
   hasAttachments?: boolean;
   attachmentCount?: number;
   attachments?: Array<{ filename: string; mimeType: string }>;
   category_suggestion?: string;
   classification_reason?: string;
   classified_at?: string;
   is_classified?: boolean;
   [key: string]: any; // Allow other fields from API
}

const messages = ref<Message[]>([]);
const selectedCategory = ref<string | null>(null);
const isLoading = ref(false);
const isRefreshing = ref(false);
const isAuthorized = ref(false);
const isAuthorizingGmail = ref(false);
const errorMessage = ref('');
const expandedIds = ref<Set<string>>(new Set());
const messageBody = ref<Record<string, any>>({});
const loadingMessageBody = ref<Record<string, boolean>>({});
const messageAttachments = ref<Record<string, any[]>>({});
const loadingAttachments = ref<Record<string, boolean>>({});
const classifyingEmails = ref<Record<string, boolean>>({});
const creatingOpportunity = ref<Record<string, boolean>>({});
const notification = ref<{ message: string; type: 'info' | 'success' | 'error' }>({
   message: '',
   type: 'info',
});
let notificationTimeout: ReturnType<typeof setTimeout> | null = null;
const router = useRouter();
const route = useRoute();

const showNotification = (
   message: string,
   type: 'info' | 'success' | 'error' = 'info',
   duration = 3000
) => {
   notification.value = { message, type };
   if (notificationTimeout) clearTimeout(notificationTimeout);
   if (type !== 'error' && duration > 0) {
      notificationTimeout = setTimeout(() => {
         notification.value.message = '';
      }, duration);
   }
};

// Get unique categories from all messages
const availableCategories = computed(() => {
   const categories = new Set<string>();
   messages.value.forEach((msg) => {
      if (msg.category) {
         categories.add(msg.category);
      }
   });
   return Array.from(categories).sort();
});

// Filter messages by selected category
const filteredMessages = computed(() => {
   if (!selectedCategory.value) {
      return messages.value;
   }
   return messages.value.filter((msg) => msg.category === selectedCategory.value);
});

const loadMessages = async (force = false) => {
   const loading = messages.value.length === 0;
   if (loading) {
      isLoading.value = true;
   } else {
      isRefreshing.value = true;
   }

   try {
      const headers: HeadersInit = {};
      if (session.value?.access_token) {
         headers['Authorization'] = `Bearer ${session.value.access_token}`;
      }

      // Only fetch from Gmail if force=true (refresh button), otherwise show cached DB results
      const url = `${apiUrl('gmail/messages')}?max_results=100${force ? '&force=true' : ''}`;
      const response = await fetch(url, { headers });
      const result = await response.json();

      if (response.ok && result.status === 'ok') {
         messages.value = result.messages || [];
         isAuthorized.value = true;
         if (force) {
            showNotification(t('mail.refreshedSuccess'), 'success');
         }
      } else {
         if (
            result.error_code === 'GMAIL_NOT_AUTHORIZED' ||
            result.error_code === 'GMAIL_NOT_CONFIGURED'
         ) {
            isAuthorized.value = false;
            errorMessage.value = result.message;
         } else {
            errorMessage.value = result.message || t('mail.failedToLoadMessages');
            isAuthorized.value = true;
         }
      }
   } catch (error) {
      errorMessage.value = `${t('mail.errorPrefix')}: ${
         error instanceof Error ? error.message : t('mail.unknownError')
      }`;
   } finally {
      isLoading.value = false;
      isRefreshing.value = false;
   }
};

const authorizeGmail = async () => {
   isAuthorizingGmail.value = true;
   errorMessage.value = '';

   try {
      const response = await fetch(
         `${apiUrl('gmail/authorize')}?redirect_url=${encodeURIComponent(window.location.href)}`
      );
      const result = await response.json();

      if (response.ok && result.status === 'ok') {
         setTimeout(() => loadMessages(), 3000);
      } else {
         errorMessage.value = result.message || t('mail.authorizationFailed');
      }
   } catch (error) {
      errorMessage.value = `${t('mail.authorizationError')}: ${
         error instanceof Error ? error.message : t('mail.unknownError')
      }`;
   } finally {
      isAuthorizingGmail.value = false;
   }
};

const handleExpand = async (messageId: string) => {
   if (expandedIds.value.has(messageId)) {
      expandedIds.value.delete(messageId);
      return;
   }

   expandedIds.value.add(messageId);

   // Load message body if not already loaded
   if (!messageBody.value[messageId] && !loadingMessageBody.value[messageId]) {
      await fetchMessageBody(messageId);
   }

   // Load attachments if not already loaded
   if (!messageAttachments.value[messageId] && !loadingAttachments.value[messageId]) {
      await loadAttachments(messageId);
   }
};

const loadAttachments = async (messageId: string) => {
   loadingAttachments.value[messageId] = true;
   try {
      if (!session.value?.access_token) {
         messageAttachments.value[messageId] = [];
         return;
      }

      messageAttachments.value[messageId] = await listEmailAttachments(
         messageId,
         session.value.access_token
      );
   } catch (error) {
      console.error('Error loading attachments:', error);
      messageAttachments.value[messageId] = [];
   } finally {
      loadingAttachments.value[messageId] = false;
   }
};

const fetchMessageBody = async (messageId: string) => {
   loadingMessageBody.value[messageId] = true;

   try {
      const headers: HeadersInit = {};
      if (session.value?.access_token) {
         headers['Authorization'] = `Bearer ${session.value.access_token}`;
      }

      const response = await fetch(apiUrl(`gmail/message/${messageId}`), {
         headers,
      });
      const result = await response.json();

      if (response.ok && result.status === 'ok') {
         messageBody.value[messageId] = {
            body: result.message,
            opportunities: result.opportunities || [],
         };
      } else {
         messageBody.value[messageId] = {
            body: `${t('mail.failedToLoadMessage')}: ${result.message || t('mail.unknownError')}`,
            opportunities: [],
         };
      }
   } catch (error) {
      messageBody.value[messageId] = {
         body: `${t('mail.errorPrefix')}: ${error instanceof Error ? error.message : t('mail.unknownError')}`,
         opportunities: [],
      };
   } finally {
      loadingMessageBody.value[messageId] = false;
   }

   // Load attachments if not already loaded
   if (!messageAttachments.value[messageId] && !loadingAttachments.value[messageId]) {
      await loadAttachments(messageId);
   }
};

const classifyEmail = async (emailId: string) => {
   console.log(`Classifying email: ${emailId}`);
   const message = messages.value.find((m) => m.id === emailId);
   if (!message) {
      showNotification(t('mail.emailNotFound'), 'error');
      return;
   }

   classifyingEmails.value[emailId] = true;

   try {
      const headers: HeadersInit = {};
      if (session.value?.access_token) {
         headers['Authorization'] = `Bearer ${session.value.access_token}`;
      }

      const response = await fetch(apiUrl(`emails/classify/${emailId}`), {
         method: 'POST',
         headers,
      });
      const result = await response.json();

      if (response.ok && result.status === 'ok') {
         const messageIndex = messages.value.findIndex((m) => m.id === emailId);
         if (messageIndex !== -1) {
            const currentMessage = messages.value[messageIndex];
            if (currentMessage) {
               messages.value[messageIndex] = {
                  ...currentMessage,
                  id: currentMessage.id || emailId,
                  category: result.result.category,
                  category_suggestion: result.result.category_suggestion,
                  classification_reason: result.result.classification_reason,
                  classified_at: result.result.classified_at,
               };
            }
         }
         showNotification(
            t('mail.emailClassifiedAs', { category: result.result.category_suggestion }),
            'success',
            4000
         );
      } else {
         showNotification(result.message || t('mail.failedToClassify'), 'error');
         console.error('Classification error:', result);
      }
   } catch (error) {
      const errorMsg = `${t('mail.errorPrefix')}: ${
         error instanceof Error ? error.message : t('mail.unknownError')
      }`;
      showNotification(errorMsg, 'error');
      console.error('Classification exception:', error);
   } finally {
      classifyingEmails.value[emailId] = false;
   }
};

const resyncEmail = async (emailId: string, providerMessageId: string) => {
   console.log(`Resyncing email: ${emailId} (Gmail ID: ${providerMessageId})`);

   try {
      const headers: HeadersInit = {};
      if (session.value?.access_token) {
         headers['Authorization'] = `Bearer ${session.value.access_token}`;
         headers['Content-Type'] = 'application/json';
      }

      const response = await fetch(apiUrl(`email/${emailId}/resync`), {
         method: 'POST',
         headers,
         body: JSON.stringify({ provider_message_id: providerMessageId }),
      });
      const result = await response.json();

      if (response.ok && result.status === 'ok') {
         showNotification(t('mail.resyncedSuccess'), 'success', 4000);
         // Refresh the email list
         await loadMessages(true);
      } else {
         showNotification(result.message || t('mail.failedToResync'), 'error');
         console.error('Resync error:', result);
      }
   } catch (error) {
      const errorMsg = `${t('mail.errorPrefix')}: ${
         error instanceof Error ? error.message : t('mail.unknownError')
      }`;
      showNotification(errorMsg, 'error');
      console.error('Resync exception:', error);
   }
};

const deleteEmail = async (emailId: string) => {
   console.log(`Deleting email: ${emailId}`);

   try {
      const headers: HeadersInit = {};
      if (session.value?.access_token) {
         headers['Authorization'] = `Bearer ${session.value.access_token}`;
      }

      const response = await fetch(apiUrl(`email/${emailId}`), {
         method: 'DELETE',
         headers,
      });
      const result = await response.json();

      if (response.ok && result.status === 'ok') {
         showNotification(t('mail.deletedSuccess'), 'success', 4000);
         // Refresh the email list
         await loadMessages(true);
      } else {
         showNotification(result.message || t('mail.failedToDelete'), 'error');
         console.error('Delete error:', result);
      }
   } catch (error) {
      const errorMsg = `${t('mail.errorPrefix')}: ${
         error instanceof Error ? error.message : t('mail.unknownError')
      }`;
      showNotification(errorMsg, 'error');
      console.error('Delete exception:', error);
   }
};

const setupRealtimeSubscription = async (userId: string) => {
   emailSubscription = await setupEmailRealtimeSubscription({
      userId,
      accessToken: session.value?.access_token,
      refreshToken: session.value?.refresh_token,
      supabaseClient: supabase,
      onEmailUpdate: (emailId: string, payload: any) => {
         console.log('[Realtime] Email UPDATE received:', emailId);
         const index = messages.value.findIndex((m) => m.id === emailId);
         if (index !== -1) {
            messages.value[index] = {
               ...messages.value[index],
               ...payload.new,
            } as any;
         }
      },
   });
};

const cleanupRealtimeSubscription = () => {
   emailSubscription = cleanupEmailRealtimeSubscription(emailSubscription);
};

const createOpportunity = async (messageId: string) => {
   creatingOpportunity.value[messageId] = true;
   try {
      const headers: HeadersInit = { 'Content-Type': 'application/json' };
      if (session.value?.access_token) {
         headers['Authorization'] = `Bearer ${session.value.access_token}`;
      }

      const response = await fetch(apiUrl('opportunities/create-from-email'), {
         method: 'POST',
         headers,
         body: JSON.stringify({ message_id: messageId }),
      });

      const result = await response.json();
      if (!response.ok) {
         throw new Error(result?.message || t('mail.failedCreateOpportunity'));
      }

      const opportunityId = result?.opportunity.id;
      showNotification(
         t('mail.opportunityCreated', {
            name: result.opportunity.name || result.opportunity.id,
         }),
         'success',
         3000
      );

      console.log('Redirecting to opportunity detail page:', opportunityId);
      // Redirect to opportunity detail page after success
      setTimeout(() => {
         router.push(`/opportunities/${opportunityId}/source`);
      }, 1500);
   } catch (error: any) {
      const msg = error?.message || t('mail.failedCreateOpportunity');
      showNotification(msg, 'error', 5000);
   } finally {
      creatingOpportunity.value[messageId] = false;
   }
};

onMounted(() => {
   // Set selected category from route parameter if present
   if (route.params.category) {
      selectedCategory.value = decodeURIComponent(route.params.category as string);
   }
   loadMessages();
   // Setup realtime subscription when user is authenticated
   if (session.value?.user?.id) {
      setupRealtimeSubscription(session.value.user.id);
   }
});

// Watch for route changes to update selected category
watch(
   () => route.params.category,
   (newCategory) => {
      selectedCategory.value = newCategory ? decodeURIComponent(newCategory as string) : null;
   }
);

onUnmounted(() => {
   cleanupRealtimeSubscription();
});
</script>
