<template>
   <div class="p-6 max-w-4xl mx-auto">
      <h1 class="text-3xl font-bold text-gray-900 mb-6">{{ t('settings.title') }}</h1>

      <div class="bg-white rounded-lg shadow p-6 space-y-6">
         <!-- Language Settings -->
         <div>
            <h2 class="text-lg font-semibold text-gray-900 mb-4">{{ t('settings.language') }}</h2>
            <div class="flex items-center gap-3">
               <label class="text-sm text-gray-700">{{ t('settings.selectLanguage') }}</label>
               <LocaleSwitcher />
            </div>
         </div>

         <div class="border-t border-gray-200"></div>

         <!-- User Info -->
         <div v-if="user">
            <h2 class="text-lg font-semibold text-gray-900 mb-4">{{ t('settings.account') }}</h2>
            <div class="space-y-3 text-sm">
               <div>
                  <span class="text-gray-600">{{ t('settings.email') }}</span>
                  <span class="ml-2 text-gray-900">{{ user.email }}</span>
               </div>
               <div class="max-w-md">
                  <label class="text-gray-600 block mb-1">{{ t('settings.senderName') }}</label>
                  <input
                     v-model="senderName"
                     type="text"
                     class="w-full rounded-md border px-3 py-2 transition-all duration-200"
                     :class="senderNameInputClass"
                     :placeholder="t('settings.senderNamePlaceholder')"
                     @blur="handleSenderNameBlur"
                     @keydown.enter.prevent="handleSenderNameEnter"
                  />
                  <p class="text-xs text-gray-500 mt-1">{{ t('settings.senderNameHelp') }}</p>
                  <p v-if="senderNameSuccess" class="text-xs text-green-700 mt-1">
                     {{ senderNameSuccess }}
                  </p>
                  <p v-if="senderNameError" class="text-xs text-red-600 mt-1">
                     {{ senderNameError }}
                  </p>
               </div>
               <div>
                  <button
                     @click="handleSignOut"
                     class="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition"
                  >
                     {{ t('settings.signOut') }}
                  </button>
               </div>
            </div>
         </div>

         <div class="border-t border-gray-200"></div>

         <!-- Gmail Settings -->
         <div>
            <h2 class="text-lg font-semibold text-gray-900 mb-4">
               {{ t('settings.googleTitle') }}
            </h2>
            <div class="space-y-3 text-sm">
               <div class="flex items-center gap-2">
                  <span class="text-gray-600">{{ t('settings.status') }}</span>
                  <span
                     v-if="gmailStatus"
                     class="px-2 py-0.5 rounded text-xs"
                     :class="
                        gmailStatus.authorized
                           ? 'bg-green-100 text-green-800'
                           : 'bg-gray-100 text-gray-700'
                     "
                  >
                     {{
                        gmailStatus.authorized
                           ? t('settings.connected')
                           : t('settings.notConnected')
                     }}
                  </span>
                  <span v-else-if="!gmailError" class="text-gray-500">{{
                     t('common.loading')
                  }}</span>
                  <span v-if="gmailError" class="text-red-600 text-xs">
                     {{ gmailError }}
                  </span>
               </div>

               <details
                  v-if="gmailErrorDetails && gmailErrorDetails !== gmailError"
                  class="text-xs text-gray-600"
               >
                  <summary class="cursor-pointer select-none">
                     {{ t('settings.errorDetails') }}
                  </summary>
                  <pre class="mt-1 whitespace-pre-wrap wrap-break-word">{{
                     gmailErrorDetails
                  }}</pre>
               </details>

               <div v-if="gmailProfile" class="space-y-2">
                  <div class="text-gray-700">
                     <span class="text-gray-600">{{ t('settings.emailLabel') }}</span>
                     <span class="ml-2 text-gray-900">{{
                        gmailProfile.profile?.emailAddress
                     }}</span>
                  </div>
                  <div class="text-gray-700">
                     <span class="text-gray-600">{{ t('settings.permissions') }}</span>
                     <ul class="mt-1 list-disc list-inside text-gray-900">
                        <li v-for="item in permissionItems" :key="item">{{ item }}</li>
                        <li v-if="!permissionItems.length" class="text-gray-500">
                           {{ t('settings.none') }}
                        </li>
                     </ul>
                  </div>
               </div>
               <div class="flex items-center gap-3">
                  <button
                     @click="handleGmailAuthorize"
                     class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition"
                     :disabled="gmailLoading"
                  >
                     {{
                        isGmailAuthorized
                           ? t('settings.reauthorizeGmail')
                           : t('settings.authorizeGmail')
                     }}
                  </button>
                  <button
                     @click="handleGmailRevoke"
                     class="px-4 py-2 bg-gray-200 text-gray-900 rounded-md hover:bg-gray-300 transition"
                     :disabled="gmailLoading || !isGmailAuthorized"
                  >
                     {{ t('settings.disconnect') }}
                  </button>
               </div>
               <div class="text-xs text-gray-500">
                  {{ t('settings.gmailTokenHint') }}
               </div>
            </div>
         </div>

         <div class="border-t border-gray-200"></div>

         <!-- Outlook Settings -->
         <div>
            <h2 class="text-lg font-semibold text-gray-900 mb-4">Outlook / Microsoft</h2>
            <div class="space-y-3 text-sm">
               <div class="flex items-center gap-2">
                  <span class="text-gray-600">{{ t('settings.status') }}</span>
                  <span
                     v-if="outlookStatus"
                     class="px-2 py-0.5 rounded text-xs"
                     :class="
                        outlookStatus.authorized
                           ? 'bg-green-100 text-green-800'
                           : 'bg-gray-100 text-gray-700'
                     "
                  >
                     {{
                        outlookStatus.authorized
                           ? t('settings.connected')
                           : t('settings.notConnected')
                     }}
                  </span>
                  <span v-else-if="!outlookError" class="text-gray-500">{{
                     t('common.loading')
                  }}</span>
                  <span v-if="outlookError" class="text-red-600 text-xs">
                     {{ outlookError }}
                  </span>
               </div>

               <div v-if="outlookProfile" class="space-y-2">
                  <div class="text-gray-700">
                     <span class="text-gray-600">{{ t('settings.emailLabel') }}</span>
                     <span class="ml-2 text-gray-900">{{
                        getOutlookDisplayEmail(outlookProfile.profile)
                     }}</span>
                  </div>
                  <div class="text-gray-700">
                     <span class="text-gray-600">{{ t('settings.permissions') }}</span>
                     <ul class="mt-1 list-disc list-inside text-gray-900">
                        <li v-for="item in outlookPermissionItems" :key="item">{{ item }}</li>
                        <li v-if="!outlookPermissionItems.length" class="text-gray-500">
                           {{ t('settings.none') }}
                        </li>
                     </ul>
                  </div>
               </div>

               <div class="flex items-center gap-3">
                  <button
                     @click="handleOutlookAuthorize"
                     class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition"
                     :disabled="outlookLoading"
                  >
                     {{ isOutlookAuthorized ? 'Reconnecter Outlook' : 'Autoriser Outlook' }}
                  </button>
                  <button
                     @click="handleOutlookRevoke"
                     class="px-4 py-2 bg-gray-200 text-gray-900 rounded-md hover:bg-gray-300 transition"
                     :disabled="outlookLoading || !isOutlookAuthorized"
                  >
                     {{ t('settings.disconnect') }}
                  </button>
               </div>
            </div>
         </div>

         <div class="border-t border-gray-200"></div>

         <!-- IMAP Settings -->
         <div>
            <h2 class="text-lg font-semibold text-gray-900 mb-4">
               {{ t('settings.imapTitle') }}
            </h2>
            <div class="space-y-4 text-sm">
               <div class="flex items-center gap-2">
                  <span class="text-gray-600">{{ t('settings.status') }}</span>
                  <span
                     v-if="imapStatus"
                     class="px-2 py-0.5 rounded text-xs"
                     :class="
                        imapStatus.connected
                           ? 'bg-green-100 text-green-800'
                           : imapStatus.configured
                             ? 'bg-amber-100 text-amber-800'
                             : 'bg-gray-100 text-gray-700'
                     "
                  >
                     {{
                        imapStatus.connected
                           ? t('settings.connected')
                           : imapStatus.configured
                             ? t('settings.imapConfigured')
                             : t('settings.imapNotConfigured')
                     }}
                  </span>
                  <span v-else class="text-gray-500">{{ t('common.loading') }}</span>
               </div>

               <div v-if="imapError" class="text-red-600 text-xs">
                  {{ imapError }}
               </div>
               <div v-if="imapSuccess" class="text-green-700 text-xs">
                  {{ imapSuccess }}
               </div>

               <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <label class="block">
                     <span class="text-gray-600 block mb-1">{{ t('settings.imapHost') }}</span>
                     <input
                        v-model="imapForm.host"
                        type="text"
                        class="w-full rounded-md border border-gray-300 px-3 py-2"
                        placeholder="imap.example.com"
                     />
                  </label>
                  <label class="block">
                     <span class="text-gray-600 block mb-1">{{ t('settings.imapPort') }}</span>
                     <input
                        v-model.number="imapForm.port"
                        type="number"
                        class="w-full rounded-md border border-gray-300 px-3 py-2"
                        placeholder="993"
                     />
                  </label>
                  <label class="block">
                     <span class="text-gray-600 block mb-1">{{ t('settings.imapUsername') }}</span>
                     <input
                        v-model="imapForm.username"
                        type="text"
                        class="w-full rounded-md border border-gray-300 px-3 py-2"
                        placeholder="user@example.com"
                     />
                  </label>
                  <label class="block">
                     <span class="text-gray-600 block mb-1">{{ t('settings.imapPassword') }}</span>
                     <input
                        v-model="imapForm.password"
                        type="password"
                        class="w-full rounded-md border border-gray-300 px-3 py-2"
                        :placeholder="imapForm.has_password ? '••••••••' : ''"
                     />
                  </label>
                  <label class="block md:col-span-2">
                     <span class="text-gray-600 block mb-1">{{ t('settings.imapMailbox') }}</span>
                     <input
                        v-model="imapForm.mailbox"
                        type="text"
                        class="w-full rounded-md border border-gray-300 px-3 py-2"
                        placeholder="INBOX"
                     />
                  </label>
               </div>

               <div class="flex flex-wrap gap-4 text-gray-700">
                  <label class="inline-flex items-center gap-2">
                     <input v-model="imapForm.use_ssl" type="checkbox" />
                     <span>{{ t('settings.imapUseSsl') }}</span>
                  </label>
                  <label class="inline-flex items-center gap-2">
                     <input v-model="imapForm.enabled" type="checkbox" />
                     <span>{{ t('settings.imapEnabled') }}</span>
                  </label>
               </div>

               <div class="flex items-center gap-3">
                  <button
                     @click="handleImapSave"
                     class="px-4 py-2 bg-slate-900 text-white rounded-md hover:bg-slate-800 transition"
                     :disabled="imapLoading"
                  >
                     {{ t('settings.saveImap') }}
                  </button>
                  <button
                     @click="handleImapTest"
                     class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition"
                     :disabled="imapLoading || !imapStatus?.configured"
                  >
                     {{ t('settings.testImap') }}
                  </button>
                  <button
                     @click="handleImapClear"
                     class="px-4 py-2 bg-gray-200 text-gray-900 rounded-md hover:bg-gray-300 transition"
                     :disabled="imapLoading || !imapStatus?.configured"
                  >
                     {{ t('settings.clearImap') }}
                  </button>
               </div>

               <div class="text-xs text-gray-500 space-y-1">
                  <div>{{ t('settings.imapPasswordHint') }}</div>
                  <div>{{ t('settings.imapMailboxHint') }}</div>
               </div>
            </div>
         </div>

         <div class="border-t border-gray-200"></div>

         <!-- Email Fetch Loop -->
         <div>
            <h2 class="text-lg font-semibold text-gray-900 mb-4">
               {{ t('settings.emailFetchLoopTitle') }}
            </h2>
            <div class="space-y-3 text-sm">
               <div class="flex items-center gap-2">
                  <span class="text-gray-600">{{ t('settings.status') }}</span>
                  <span
                     v-if="fetchLoopStatus"
                     class="px-2 py-0.5 rounded text-xs"
                     :class="
                        fetchLoopStatus.running
                           ? 'bg-green-100 text-green-800'
                           : 'bg-gray-100 text-gray-700'
                     "
                  >
                     {{ fetchLoopStatus.running ? t('settings.running') : t('settings.stopped') }}
                  </span>
                  <span v-else class="text-gray-500">{{ t('common.loading') }}</span>
                  <button
                     @click="loadFetchLoopStatus"
                     class="ml-2 px-2 py-1 text-xs bg-gray-200 text-gray-800 rounded hover:bg-gray-300 transition"
                  >
                     {{ t('settings.refresh') }}
                  </button>
               </div>
               <div v-if="fetchLoopStatus?.last_heartbeat" class="text-xs text-gray-500">
                  {{ t('settings.lastHeartbeat') }}:
                  {{ formatHeartbeat(fetchLoopStatus.last_heartbeat) }}
               </div>
               <p class="text-gray-600">
                  {{ t('settings.fetchLoopDescription') }}
               </p>
               <div>
                  <label class="text-gray-600 block mb-1">{{ t('settings.allUsers') }}</label>
                  <div class="text-gray-900 font-mono bg-gray-50 p-2 rounded">
                     {{ fetchLoopCommandAll }}
                  </div>
               </div>
               <div>
                  <label class="text-gray-600 block mb-1">{{ t('settings.currentUser') }}</label>
                  <div class="text-gray-900 font-mono bg-gray-50 p-2 rounded">
                     {{ fetchLoopCommandUser }}
                  </div>
               </div>
               <p class="text-xs text-gray-500">{{ t('settings.fetchLoopDefaults') }}</p>
            </div>
         </div>

         <div class="border-t border-gray-200"></div>

         <!-- API Settings -->
         <div>
            <h2 class="text-lg font-semibold text-gray-900 mb-4">
               {{ t('settings.apiEndpoints') }}
            </h2>
            <div class="space-y-3 text-sm">
               <div>
                  <label class="text-gray-600 block mb-1">{{ t('settings.llmApi') }}</label>
                  <div class="text-gray-900 font-mono bg-gray-50 p-2 rounded">
                     {{ LLM_API_URL }}
                  </div>
               </div>
               <div>
                  <label class="text-gray-600 block mb-1">{{ t('settings.databaseApi') }}</label>
                  <div class="text-gray-900 font-mono bg-gray-50 p-2 rounded">
                     {{ API_BASE_URL }}
                  </div>
               </div>
            </div>
         </div>
      </div>
   </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import LocaleSwitcher from '../LocaleSwitcher.vue';
import { useAuth } from '../../stores/auth';
import { useI18n } from '../../i18n/useI18n';
import { API_BASE_URL, apiUrl } from '../../utils/api';
import { authFetch } from '../../api/authFetch';
import {
   getOutlookProfile,
   getOutlookStatus,
   revokeOutlook,
   startOutlookOAuth,
} from '../../api/outlook';
import { getOutlookDisplayEmail } from './outlookEmail';

const router = useRouter();
const { user, signOut, updateDisplayName } = useAuth();
const { t } = useI18n();

const LLM_API_URL = 'http://localhost:1234/v1/chat/completions';

const gmailStatus = ref<{ status: string; authorized: boolean; message: string } | null>(null);
const gmailProfile = ref<{ profile: any; permissions: string[] } | null>(null);
const gmailLoading = ref(false);
const gmailError = ref('');
const gmailErrorDetails = ref('');
const isGmailAuthorized = computed(() => !!gmailStatus.value?.authorized);
const outlookStatus = ref<{ status: string; authorized: boolean; message: string } | null>(null);
const outlookProfile = ref<{ profile: any; permissions: string[] } | null>(null);
const outlookLoading = ref(false);
const outlookError = ref('');
const isOutlookAuthorized = computed(() => !!outlookStatus.value?.authorized);
type ImapConfig = {
   host: string;
   port: number;
   username: string;
   password: string;
   mailbox: string;
   use_ssl: boolean;
   enabled: boolean;
   has_password: boolean;
};
type ImapStatus = {
   status: string;
   configured: boolean;
   enabled: boolean;
   connected: boolean;
   message: string;
   config?: Partial<ImapConfig>;
};
const imapStatus = ref<ImapStatus | null>(null);
const imapLoading = ref(false);
const imapError = ref('');
const imapSuccess = ref('');
const imapForm = ref<ImapConfig>({
   host: '',
   port: 993,
   username: '',
   password: '',
   mailbox: 'INBOX',
   use_ssl: true,
   enabled: true,
   has_password: false,
});
const fetchLoopStatus = ref<{
   running: boolean;
   pid: number | null;
   started_at: number | null;
   last_heartbeat: number | null;
   mode: string | null;
} | null>(null);
const senderName = ref('');
const senderNameSaving = ref(false);
const senderNameSuccess = ref('');
const senderNameError = ref('');
const lastSavedSenderName = ref('');
let senderNameSuccessTimeout: ReturnType<typeof setTimeout> | null = null;
const fetchLoopCommandAll = computed(
   () =>
      'python -m src.command.fetch_emails_loop --interval 120 --max-results 50 --classify-limit 200'
);
const fetchLoopCommandUser = computed(() => {
   const userId = user.value?.id || '<USER_ID>';
   return `python -m src.command.fetch_emails_loop --user-id ${userId} --interval 120 --max-results 50 --classify-limit 200`;
});
const permissionItems = computed(() => {
   const scopes = gmailProfile.value?.permissions || [];
   if (!scopes.length) return [];

   const gmailScopes: string[] = [];
   let hasDrive = false;
   let hasSheets = false;
   let hasOther = false;

   for (const scope of scopes) {
      if (scope.includes('/auth/gmail.send')) gmailScopes.push('send');
      else if (scope.includes('/auth/gmail.readonly')) gmailScopes.push('readonly');
      else if (scope.includes('/auth/gmail')) gmailScopes.push('other');
      else if (scope.includes('/auth/drive')) hasDrive = true;
      else if (scope.includes('/auth/spreadsheets')) hasSheets = true;
      else hasOther = true;
   }

   const items: string[] = [];
   if (gmailScopes.length) {
      const unique = Array.from(new Set(gmailScopes));
      items.push(`Gmail (${unique.join(', ')})`);
   }
   if (hasDrive) items.push('Drive (full access)');
   if (hasSheets) items.push('Sheets (full access)');
   if (hasOther) items.push('Other');

   return items;
});

const outlookPermissionItems = computed(() => {
   const scopes = outlookProfile.value?.permissions || [];
   if (!scopes.length) return [];
   return scopes;
});

async function handleSignOut() {
   await signOut();
   router.push('/login');
}

const senderNameInputClass = computed(() => {
   if (senderNameSaving.value) {
      return 'border-blue-500 ring-2 ring-blue-200 animate-pulse';
   }
   if (senderNameError.value) {
      return 'border-red-500 ring-1 ring-red-200';
   }
   if (senderNameSuccess.value) {
      return 'border-green-500 ring-1 ring-green-200';
   }
   return 'border-gray-300 focus:border-blue-500 focus:ring-2 focus:ring-blue-200';
});

async function handleSaveSenderName() {
   const nextValue = senderName.value.trim();
   if (senderNameSaving.value || nextValue === lastSavedSenderName.value) {
      return;
   }

   senderName.value = nextValue;
   senderNameSaving.value = true;
   senderNameError.value = '';
   senderNameSuccess.value = '';
   if (senderNameSuccessTimeout) {
      clearTimeout(senderNameSuccessTimeout);
      senderNameSuccessTimeout = null;
   }

   try {
      await updateDisplayName(nextValue);
      lastSavedSenderName.value = nextValue;
      senderNameSuccess.value = t('settings.senderNameSaved');
      senderNameSuccessTimeout = setTimeout(() => {
         senderNameSuccess.value = '';
      }, 1600);
   } catch (error) {
      senderNameError.value = t('settings.senderNameSaveFailed');
   } finally {
      senderNameSaving.value = false;
   }
}

async function handleSenderNameBlur() {
   await handleSaveSenderName();
}

async function handleSenderNameEnter() {
   await handleSaveSenderName();
}

async function loadGmailStatus() {
   gmailError.value = '';
   gmailErrorDetails.value = '';
   try {
      const userId = user.value?.id;
      const url = new URL(apiUrl('gmail/status'), window.location.origin);
      url.searchParams.set('user_id', userId || '');
      const res = await fetch(url.toString());
      const data = await res.json();
      if (!res.ok) {
         setGmailError(data?.message, t('settings.gmailStatusLoadFailed'));
         gmailStatus.value = null;
         gmailProfile.value = null;
         return;
      }
      gmailStatus.value = data;
      if (data?.status === 'error' || (data?.authorized === false && data?.message)) {
         setGmailError(data?.message, t('settings.gmailAuthFailed'));
      }
      if (data?.authorized) {
         await loadGmailProfile();
      } else {
         gmailProfile.value = null;
      }
   } catch (error) {
      setGmailError(String(error), t('settings.gmailStatusLoadFailed'));
      gmailStatus.value = null;
      gmailProfile.value = null;
   }
}

async function loadGmailProfile() {
   try {
      const userId = user.value?.id;
      const url = new URL(apiUrl('gmail/profile'), window.location.origin);
      url.searchParams.set('user_id', userId || '');
      const res = await fetch(url.toString());
      const data = await res.json();
      if (!res.ok || data?.status !== 'ok') {
         gmailProfile.value = null;
         return;
      }
      gmailProfile.value = data;
   } catch (error) {
      gmailProfile.value = null;
   }
}

async function handleGmailAuthorize() {
   gmailLoading.value = true;
   gmailError.value = '';
   gmailErrorDetails.value = '';
   try {
      if (!user.value?.id) {
         setGmailError('', t('settings.gmailMissingUserId'));
         return;
      }
      const redirect_url = window.location.href;
      const url = new URL(apiUrl('gmail/oauth/start'), window.location.origin);
      url.searchParams.set('redirect_url', redirect_url);
      url.searchParams.set('user_id', user.value.id);
      const res = await fetch(url.toString());
      const data = await res.json();
      if (!res.ok || data?.status !== 'ok' || !data?.auth_url) {
         setGmailError(data?.message, t('settings.gmailAuthorizeFailed'));
         return;
      }
      window.location.href = data.auth_url;
   } catch (error) {
      setGmailError(String(error), t('settings.gmailAuthorizeFailed'));
   } finally {
      gmailLoading.value = false;
   }
}

async function handleGmailRevoke() {
   gmailLoading.value = true;
   gmailError.value = '';
   gmailErrorDetails.value = '';
   try {
      const userId = user.value?.id;
      const url = new URL(apiUrl('gmail/revoke'), window.location.origin);
      url.searchParams.set('user_id', userId || '');
      const res = await fetch(url.toString());
      const data = await res.json();
      if (!res.ok || data?.status !== 'ok') {
         setGmailError(data?.message, t('settings.gmailDisconnectFailed'));
         return;
      }
      await loadGmailStatus();
   } catch (error) {
      setGmailError(String(error), t('settings.gmailDisconnectFailed'));
   } finally {
      gmailLoading.value = false;
   }
}

async function loadOutlookStatus() {
   outlookError.value = '';
   try {
      const userId = user.value?.id || '';
      const data = await getOutlookStatus(userId);
      outlookStatus.value = data;
      if (data?.authorized) {
         await loadOutlookProfile();
      } else {
         outlookProfile.value = null;
      }
   } catch (error) {
      outlookError.value = (error as Error)?.message || 'Failed to load Outlook status.';
      outlookStatus.value = null;
      outlookProfile.value = null;
   }
}

async function loadOutlookProfile() {
   try {
      const userId = user.value?.id || '';
      const data = await getOutlookProfile(userId);
      outlookProfile.value = data;
   } catch (error) {
      outlookProfile.value = null;
   }
}

async function handleOutlookAuthorize() {
   outlookLoading.value = true;
   outlookError.value = '';
   try {
      if (!user.value?.id) {
         outlookError.value = 'Missing user_id';
         return;
      }
      const authUrl = await startOutlookOAuth(window.location.href, user.value.id);
      window.location.href = authUrl;
   } catch (error) {
      outlookError.value = (error as Error)?.message || 'Outlook authorization failed.';
   } finally {
      outlookLoading.value = false;
   }
}

async function handleOutlookRevoke() {
   outlookLoading.value = true;
   outlookError.value = '';
   try {
      const userId = user.value?.id || '';
      await revokeOutlook(userId);
      await loadOutlookStatus();
   } catch (error) {
      outlookError.value = (error as Error)?.message || 'Outlook disconnect failed.';
   } finally {
      outlookLoading.value = false;
   }
}

function setGmailError(rawMessage: unknown, fallback: string) {
   const raw = typeof rawMessage === 'string' ? rawMessage : '';
   const message = raw.trim();
   const lower = message.toLowerCase();

   gmailErrorDetails.value = message;

   if (!message) {
      gmailError.value = fallback;
      return;
   }

   if (lower.includes('invalid_grant') || lower.includes('expired or revoked')) {
      gmailError.value = t('settings.gmailAuthExpired');
      return;
   }
   if (lower.includes('access_denied')) {
      gmailError.value = t('settings.gmailAuthDenied');
      return;
   }
   if (lower.includes('invalid_client')) {
      gmailError.value = t('settings.gmailAuthClientConfigError');
      return;
   }
   if (lower.includes('connection error') || lower.includes('network')) {
      gmailError.value = t('settings.gmailAuthNetworkError');
      return;
   }

   if (lower.includes('gmail_auth_error') || lower.includes('failed to authenticate')) {
      gmailError.value = t('settings.gmailAuthFailed');
      return;
   }

   gmailError.value = fallback;
}

async function loadImapConfig() {
   imapError.value = '';
   try {
      const res = await authFetch(apiUrl('imap/config'));
      const data = await res.json();
      if (!res.ok || data?.status !== 'ok') {
         imapError.value = data?.message || 'Failed to load IMAP configuration.';
         return;
      }

      const config = data?.config || {};
      imapForm.value = {
         host: config.host || '',
         port: Number(config.port || 993),
         username: config.username || '',
         password: '',
         mailbox: config.mailbox || 'INBOX',
         use_ssl: Boolean(config.use_ssl ?? true),
         enabled: Boolean(config.enabled ?? true),
         has_password: Boolean(config.has_password),
      };
   } catch (error) {
      imapError.value = 'Failed to load IMAP configuration.';
   }
}

async function loadImapStatus() {
   try {
      const res = await authFetch(apiUrl('imap/status'));
      const data = await res.json();
      if (!res.ok) {
         imapStatus.value = null;
         imapError.value = data?.message || 'Failed to load IMAP status.';
         return;
      }
      imapStatus.value = data;
   } catch (error) {
      imapStatus.value = null;
      imapError.value = 'Failed to load IMAP status.';
   }
}

async function handleImapSave() {
   imapLoading.value = true;
   imapError.value = '';
   imapSuccess.value = '';
   try {
      const res = await authFetch(apiUrl('imap/config'), {
         method: 'POST',
         headers: {
            'Content-Type': 'application/json',
         },
         body: JSON.stringify({
            host: imapForm.value.host,
            port: imapForm.value.port,
            username: imapForm.value.username,
            password: imapForm.value.password,
            mailbox: imapForm.value.mailbox,
            use_ssl: imapForm.value.use_ssl,
            enabled: imapForm.value.enabled,
         }),
      });
      const data = await res.json();
      if (!res.ok || data?.status !== 'ok') {
         imapError.value = data?.message || 'Failed to save IMAP configuration.';
         return;
      }

      imapSuccess.value = t('settings.imapSaveSuccess');
      await loadImapConfig();
      await loadImapStatus();
   } catch (error) {
      imapError.value = 'Failed to save IMAP configuration.';
   } finally {
      imapLoading.value = false;
   }
}

async function handleImapTest() {
   imapLoading.value = true;
   imapError.value = '';
   imapSuccess.value = '';
   try {
      const res = await authFetch(apiUrl('imap/test'), {
         method: 'POST',
      });
      const data = await res.json();
      if (!res.ok || data?.status !== 'ok') {
         imapError.value = data?.message || 'Failed to connect to IMAP.';
         return;
      }
      imapSuccess.value = data?.message || t('settings.imapConnectionSuccess');
      await loadImapStatus();
   } catch (error) {
      imapError.value = 'Failed to connect to IMAP.';
   } finally {
      imapLoading.value = false;
   }
}

async function handleImapClear() {
   imapLoading.value = true;
   imapError.value = '';
   imapSuccess.value = '';
   try {
      const res = await authFetch(apiUrl('imap/config'), {
         method: 'DELETE',
      });
      const data = await res.json();
      if (!res.ok || data?.status !== 'ok') {
         imapError.value = data?.message || 'Failed to clear IMAP configuration.';
         return;
      }

      imapForm.value = {
         host: '',
         port: 993,
         username: '',
         password: '',
         mailbox: 'INBOX',
         use_ssl: true,
         enabled: true,
         has_password: false,
      };
      imapSuccess.value = data?.message || t('settings.clearImap');
      await loadImapStatus();
   } catch (error) {
      imapError.value = 'Failed to clear IMAP configuration.';
   } finally {
      imapLoading.value = false;
   }
}

onMounted(() => {
   const metadata = (user.value?.user_metadata || {}) as Record<string, any>;
   const initialSenderName = String(metadata.full_name || metadata.name || '').trim();
   senderName.value = initialSenderName;
   lastSavedSenderName.value = initialSenderName;
   loadGmailStatus();
   loadOutlookStatus();
   loadImapConfig();
   loadImapStatus();
   loadFetchLoopStatus();
});

async function loadFetchLoopStatus() {
   try {
      const res = await fetch(apiUrl('email-fetch-loop/status'));
      const data = await res.json();
      fetchLoopStatus.value = data;
   } catch (error) {
      fetchLoopStatus.value = null;
   }
}

function formatHeartbeat(timestamp: number) {
   if (!timestamp) return '';
   const date = new Date(timestamp * 1000);
   return date.toLocaleString();
}
</script>
