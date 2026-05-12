<template>
   <div ref="menuRoot" class="relative">
      <button
         @click.stop="showMenu = !showMenu"
         class="p-1 text-gray-600 hover:bg-gray-100 rounded transition-colors"
         :title="t('mail.moreActions')"
      >
         <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path
               d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z"
            />
         </svg>
      </button>
      <div
         v-if="showMenu"
         @click.stop
         class="absolute right-0 mt-1 w-48 bg-white border border-gray-200 rounded-lg shadow-lg z-10"
      >
         <router-link
            v-if="contactId"
            :to="`/contacts/${contactId}`"
            @click.stop="showMenu = false"
            class="block w-full text-left px-4 py-2 text-sm hover:bg-gray-50 transition-colors border-b border-gray-100"
         >
            <span class="flex items-center gap-2">
               <span>👤</span>
               {{ t('mail.menuContact') }}
            </span>
         </router-link>
         <router-link
            v-if="accountId"
            :to="`/accounts/${accountId}`"
            @click.stop="showMenu = false"
            class="block w-full text-left px-4 py-2 text-sm hover:bg-gray-50 transition-colors border-b border-gray-100"
         >
            <span class="flex items-center gap-2">
               <span>🏢</span>
               {{ t('mail.menuAccount') }}
            </span>
         </router-link>
         <button
            @click.stop="handleClassify"
            :disabled="isClassifying"
            class="w-full text-left px-4 py-2 text-sm hover:bg-gray-50 disabled:bg-gray-100 disabled:cursor-not-allowed transition-colors border-b border-gray-100 last:border-b-0"
         >
            <span class="flex items-center gap-2">
               <span v-if="!isClassifying">✓</span>
               <span v-else class="animate-spin">↻</span>
               {{ isClassifying ? t('mail.classifying') : t('mail.classifyEmail') }}
            </span>
         </button>
         <button
            @click.stop="handleCreateOpportunity"
            :disabled="isCreatingOpportunity"
            class="w-full text-left px-4 py-2 text-sm hover:bg-gray-50 disabled:bg-gray-100 disabled:cursor-not-allowed transition-colors border-b border-gray-100"
         >
            <span class="flex items-center gap-2">
               <span v-if="!isCreatingOpportunity">→</span>
               <span v-else class="animate-spin">↻</span>
               {{
                  isCreatingOpportunity
                     ? t('mail.creatingOpportunity')
                     : t('mail.createOpportunity')
               }}
            </span>
         </button>
         <button
            @click.stop="handleResync"
            :disabled="isResyncing"
            class="w-full text-left px-4 py-2 text-sm hover:bg-gray-50 disabled:bg-gray-100 disabled:cursor-not-allowed transition-colors border-b border-gray-100 text-amber-600"
         >
            <span class="flex items-center gap-2">
               <span v-if="!isResyncing">🔄</span>
               <span v-else class="animate-spin">↻</span>
               {{ isResyncing ? t('mail.resyncing') : t('mail.resyncFromGmail') }}
            </span>
         </button>
         <button
            @click.stop="handleDelete"
            :disabled="isDeleting"
            class="w-full text-left px-4 py-2 text-sm hover:bg-gray-50 disabled:bg-gray-100 disabled:cursor-not-allowed transition-colors text-red-600"
         >
            <span class="flex items-center gap-2">
               <span v-if="!isDeleting">🗑️</span>
               <span v-else class="animate-spin">↻</span>
               {{ isDeleting ? t('mail.deleting') : t('mail.deleteEmail') }}
            </span>
         </button>
         <div
            v-if="messageId || provider || providerMessageId"
            class="px-4 py-2 text-xs text-gray-500 bg-gray-50"
         >
            <div
               v-if="messageId"
               @click="copyToClipboard(messageId, 'uuid')"
               class="truncate font-mono cursor-pointer hover:text-gray-700 hover:bg-gray-100 px-1 -mx-1 rounded transition-colors flex items-center justify-between gap-2"
               :title="`${messageId} (${t('mail.clickToCopy')})`"
            >
               <span class="truncate">{{ t('mail.uuidLabel') }}: {{ messageId }}</span>
               <svg
                  v-if="copiedId !== 'uuid'"
                  class="w-3 h-3 shrink-0"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
               >
                  <path
                     stroke-linecap="round"
                     stroke-linejoin="round"
                     stroke-width="2"
                     d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"
                  />
               </svg>
               <svg
                  v-else
                  class="w-3 h-3 shrink-0 text-green-600"
                  fill="currentColor"
                  viewBox="0 0 20 20"
               >
                  <path
                     fill-rule="evenodd"
                     d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                     clip-rule="evenodd"
                  />
               </svg>
            </div>
            <div v-if="provider" class="truncate">
               {{ t('mail.providerLabel') }}: {{ provider }}
            </div>
            <div
               v-if="providerMessageId"
               @click="copyToClipboard(providerMessageId, 'provider')"
               class="truncate font-mono cursor-pointer hover:text-gray-700 hover:bg-gray-100 px-1 -mx-1 rounded transition-colors flex items-center justify-between gap-2"
               :title="`${providerMessageId} (${t('mail.clickToCopy')})`"
            >
               <span class="truncate"
                  >{{ provider }} {{ t('mail.idShort') }}: {{ providerMessageId }}</span
               >
               <svg
                  v-if="copiedId !== 'provider'"
                  class="w-3 h-3 shrink-0"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
               >
                  <path
                     stroke-linecap="round"
                     stroke-linejoin="round"
                     stroke-width="2"
                     d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"
                  />
               </svg>
               <svg
                  v-else
                  class="w-3 h-3 shrink-0 text-green-600"
                  fill="currentColor"
                  viewBox="0 0 20 20"
               >
                  <path
                     fill-rule="evenodd"
                     d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                     clip-rule="evenodd"
                  />
               </svg>
            </div>
         </div>
      </div>
   </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue';
import { useI18n } from '../../i18n/useI18n';

const { t } = useI18n();

const props = defineProps<{
   isClassifying?: boolean;
   isCreatingOpportunity?: boolean;
   messageId?: string;
   provider?: string;
   providerMessageId?: string;
   contactId?: string;
   accountId?: string;
}>();

const emit = defineEmits<{
   classify: [];
   'create-opportunity': [];
   resync: [messageId: string, providerMessageId: string];
   delete: [messageId: string];
}>();

const showMenu = ref(false);
const menuRoot = ref<HTMLElement | null>(null);
const copiedId = ref<string | null>(null);
const isResyncing = ref(false);
const isDeleting = ref(false);

const handleDocumentClick = (event: MouseEvent) => {
   const target = event.target as Node | null;
   if (showMenu.value && menuRoot.value && target && !menuRoot.value.contains(target)) {
      showMenu.value = false;
   }
};

onMounted(() => {
   document.addEventListener('click', handleDocumentClick);
});

onBeforeUnmount(() => {
   document.removeEventListener('click', handleDocumentClick);
});

const handleClassify = () => {
   showMenu.value = false;
   emit('classify');
};

const handleCreateOpportunity = () => {
   showMenu.value = false;
   emit('create-opportunity');
};

const handleResync = async () => {
   if (!props.messageId || !props.providerMessageId) {
      console.error('Missing messageId or providerMessageId');
      return;
   }
   showMenu.value = false;
   isResyncing.value = true;
   try {
      emit('resync', props.messageId, props.providerMessageId);
   } finally {
      // The parent component will handle the actual resync
      // We'll update isResyncing when done
   }
};

const handleDelete = () => {
   if (!props.messageId) {
      console.error('Missing messageId');
      return;
   }
   showMenu.value = false;
   emit('delete', props.messageId);
};

const copyToClipboard = async (text: string, id: string) => {
   try {
      await navigator.clipboard.writeText(text);
      copiedId.value = id;
      setTimeout(() => {
         copiedId.value = null;
      }, 2000);
   } catch (err) {
      console.error('Failed to copy to clipboard:', err);
   }
};
</script>
