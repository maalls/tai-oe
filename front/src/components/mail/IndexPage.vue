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
import MailNotification from './MailNotification.vue';
import MailAuthRequired from './MailAuthRequired.vue';
import MailLoader from './MailLoader.vue';
import MailList from './MailList.vue';
import { useI18n } from '../../i18n/useI18n';

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
      const url = `/api/gmail/messages?max_results=100${force ? '&force=true' : ''}`;
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
         `/api/gmail/authorize?redirect_url=${encodeURIComponent(window.location.href)}`
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
      const { data, error } = await supabase
         .from('email_attachment')
         .select('id, filename, mime_type, size, storage_path')
         .eq('email_id', messageId);

      if (error) {
         console.error('Failed to load attachments:', error);
         messageAttachments.value[messageId] = [];
      } else {
         messageAttachments.value[messageId] = data || [];
      }
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

      const response = await fetch(`/api/gmail/message/${messageId}`, {
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

      const response = await fetch(`/api/emails/classify/${emailId}`, {
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

      const response = await fetch(`/api/email/${emailId}/resync`, {
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

      const response = await fetch(`/api/email/${emailId}`, {
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
   if (!userId) {
      console.log('[Realtime] No user ID, skipping subscription');
      return;
   }

   console.log('[Realtime] Setting up subscription for user:', userId);
   console.log('[Realtime] Supabase URL:', import.meta.env.VITE_SUPABASE_URL);

   try {
      // Get the user's JWT token from session
      const token = session.value?.access_token;
      console.log('[Realtime] Token available:', !!token);

      if (token) {
         // Set auth on Supabase client for realtime
         console.log('[Realtime] Setting auth session...');
         await supabase.auth.setSession({
            access_token: token,
            refresh_token: session.value?.refresh_token || '',
         });
         console.log('[Realtime] Auth session set successfully');
      }

      // Subscribe to email updates for this user - use simpler channel name
      const channelName = `emails:${userId}`;
      console.log('[Realtime] Creating channel:', channelName);

      emailSubscription = supabase
         .channel(channelName)
         .on(
            'postgres_changes',
            {
               event: 'UPDATE',
               schema: 'public',
               table: 'emails',
               filter: `user_id=eq.${userId}`,
            },
            (payload: any) => {
               console.log('[Realtime] Email UPDATE received:', payload.new?.id);
               if (payload.new?.id) {
                  // Update existing email in the list
                  const index = messages.value.findIndex((m) => m.id === payload.new.id);
                  if (index !== -1) {
                     // Update all fields from database
                     messages.value[index] = {
                        ...messages.value[index],
                        ...payload.new,
                     } as any;
                  }
               }
            }
         )
         .subscribe((status: string, err?: any) => {
            console.log('[Realtime] Subscription status changed:', status);
            if (err) {
               console.error('[Realtime] Subscription error:', err);
            }
            // Note: Browser extensions may trigger "listener indicated an asynchronous response"
            // warning after SUBSCRIBED status - this is harmless and doesn't affect functionality
         });
   } catch (error) {
      console.error('[Realtime] Error setting up subscription:', error);
      console.error('[Realtime] Error type:', error instanceof Error ? error.name : typeof error);
      console.error(
         '[Realtime] Error message:',
         error instanceof Error ? error.message : String(error)
      );
   }
};

const cleanupRealtimeSubscription = () => {
   if (emailSubscription) {
      console.log('[Realtime] Cleaning up subscription...');
      try {
         emailSubscription.unsubscribe();
         console.log('[Realtime] Subscription unsubscribed successfully');
      } catch (error) {
         console.error('[Realtime] Error unsubscribing:', error);
      }
      emailSubscription = null;
   }
};

const createOpportunity = async (messageId: string) => {
   creatingOpportunity.value[messageId] = true;
   try {
      const headers: HeadersInit = { 'Content-Type': 'application/json' };
      if (session.value?.access_token) {
         headers['Authorization'] = `Bearer ${session.value.access_token}`;
      }

      const response = await fetch('/api/opportunities/create-from-email', {
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
