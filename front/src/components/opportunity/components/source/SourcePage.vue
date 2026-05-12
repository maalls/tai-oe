<template>
   <div class="opportunity-page h-full flex flex-col">
      <OpportunityHeader :opportunityId="opportunityId" activeTab="source" />

      <div
         class="opportunity-page-section m-4 rounded-lg shadow flex gap-0 flex-1 min-h-0 overflow-hidden"
      >
         <!-- Chat Panel on the left -->
         <div
            :class="[
               isChatCollapsed ? 'w-10' : 'w-96',
               'flex-shrink-0  border-gray-300 flex flex-col h-full overflow-hidden transition-[width] duration-200',
            ]"
         >
            <ChatPanel
               ref="chatPanelRef"
               v-model:collapsed="isChatCollapsed"
               :context="{ opportunity_id: opportunityId, section: 'source' }"
               :systemPrompt="systemPrompt"
               :placeholder="t('opportunities.askAboutSource')"
            />
         </div>

         <!-- Content Panel on the right -->
         <div class="flex-1 h-full overflow-y-auto pl-6 pr-3">
            <div v-if="isLoading" class="flex justify-center items-center py-12">
               <div class="text-gray-500">{{ t('opportunities.loadingDots') }}</div>
            </div>

            <div v-else>
               <label
                  for="opportunity-name`"
                  class="block mt-4 text-sm font-medium text-gray-700 mb-1"
               >
                  {{ t('opportunities.description') }}
               </label>
               <div class="mb-2">
                  <label class="flex flex-col gap-1 w-full">
                     <input
                        ref="titleInputRef"
                        v-model="opportunityName"
                        type="text"
                        :id="`opportunity-name`"
                        name="opportunity-name"
                        class="ao w-full px-2 py-1 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                        :placeholder="t('opportunities.opportunityNamePlaceholder')"
                        :disabled="isSavingName"
                        @blur="saveOpportunityName"
                        @keydown.enter.prevent="saveOpportunityName"
                     />
                  </label>
                  <div v-if="nameError" class="text-xs text-red-600 mt-1">{{ nameError }}</div>
               </div>

               <SourceViewer
                  v-if="sourceEmail || sourceDocument"
                  :source="source"
                  :isExtracting="isExtracting"
                  :isScanning="isScanning"
                  :onExtractAuthorAsContact="extractAuthorAsContact"
                  :onScanAttachmentForRFQ="scanAttachmentForRFQ"
                  :onSaveContent="saveDocumentContent"
               />
               <SourceNewDocumentTemplate
                  ref="sourceFormRef"
                  v-else
                  :rfqForm="rfqForm"
                  :isCreatingRFQ="isCreatingRFQ"
                  :rfqErrorMessage="rfqErrorMessage"
                  :rfqSuccessMessage="rfqSuccessMessage"
                  @submitRFQ="submitRFQ"
                  @onFileSelected="onFileSelected"
               />
               <div>
                  <button
                     type="button"
                     class="mt-2 text-xs text-gray-600 hover:text-gray-800 underline"
                     @click="runTrackedElementsTool"
                  >
                     {{ t('opportunities.debugListTrackedElements') }}
                  </button>
               </div>
            </div>
         </div>
      </div>
   </div>
</template>

<script setup lang="ts">
import OpportunityHeader from '../../OpportunityHeader.vue';
import SourceViewer from './SourceViewer.vue';
import SourceNewDocumentTemplate from './SourceNewDocumentTemplate.vue';
import ChatPanel from '../../../chat/ChatPanel.vue';
import { useSourcePage } from './SourcePage';
import { ref, watch, nextTick } from 'vue';

const {
   t,
   opportunityId,
   isLoading,
   isExtracting,
   isScanning,
   opportunityName,
   isSavingName,
   nameError,
   source,
   sourceEmail,
   sourceDocument,
   rfqForm,
   isCreatingRFQ,
   rfqErrorMessage,
   rfqSuccessMessage,
   systemPrompt,
   extractAuthorAsContact,
   scanAttachmentForRFQ,
   saveOpportunityName,
   saveDocumentContent,
   submitRFQ,
   onFileSelected,
} = useSourcePage();

const chatPanelRef = ref<{ runTrackedElementsTool?: (className?: string) => void } | null>(null);
const isChatCollapsed = ref(false);
const titleInputRef = ref<HTMLInputElement | null>(null);
const sourceFormRef = ref<{ focusMessageEnd?: () => void } | null>(null);
const hasAutoFocused = ref(false);

const runTrackedElementsTool = () => {
   chatPanelRef.value?.runTrackedElementsTool?.('.ao');
};

const focusOnOpen = async () => {
   if (isLoading.value || hasAutoFocused.value) return;
   await nextTick();
   if (!opportunityName.value.trim()) {
      titleInputRef.value?.focus();
      hasAutoFocused.value = true;
      return;
   }
   if (sourceDocument.value) {
      hasAutoFocused.value = true;
      return;
   }
   if (!sourceEmail.value && !sourceDocument.value) {
      sourceFormRef.value?.focusMessageEnd?.();
      hasAutoFocused.value = true;
   }
};

watch(
   () => [isLoading.value, opportunityName.value, sourceEmail.value, sourceDocument.value],
   () => {
      focusOnOpen();
   },
   { immediate: true }
);
</script>
