<template>
   <div class="bg-white rounded-lg shadow p-6">
      <div class="border border-gray-300 rounded-lg p-4 bg-gray-50">
         <div class="flex items-center justify-between mb-3">
            <h3 class="text-sm font-semibold text-gray-700">
               {{ t('opportunities.sourceDocumentTitle') }}
            </h3>
            <button
               type="button"
               @click="$emit('toggleDocumentExpanded')"
               class="text-xs text-blue-600 hover:text-blue-700"
            >
               {{ isDocumentExpanded ? t('opportunities.collapse') : t('opportunities.expand') }}
            </button>
         </div>

         <div class="space-y-2 text-sm">
            <div>
               <span class="font-medium text-gray-700">{{ t('opportunities.typeLabel') }}:</span>
               <span
                  name="source_type"
                  id="source-type"
                  description="The document type"
                  class="ao ml-2 text-gray-900"
                  >{{ sourceDocument.type || 'RFP' }}</span
               >
            </div>
            <div v-if="sourceDocument.created_at">
               <span class="font-medium text-gray-700">{{ t('opportunities.dateLabel') }}:</span>
               <span class="ml-2 text-gray-900">{{
                  formatEmailDate(sourceDocument.created_at)
               }}</span>
            </div>
            <div v-if="sourceDocument.content">
               <span class="font-medium text-gray-700"
                  >{{ t('opportunities.contentSizeLabel') }}:</span
               >
               <span class="ml-2 text-gray-900">{{ formatBodySize(sourceDocument.content) }}</span>
            </div>

            <div v-if="attachments.length > 0">
               <span class="font-medium text-gray-700"
                  >{{ t('opportunities.attachmentsLabel') }}:</span
               >
               <div class="ml-2 mt-2 space-y-1">
                  <div
                     v-for="attachment in attachments"
                     :key="attachment.id"
                     class="flex items-center gap-2 text-sm text-gray-700 bg-gray-50 p-2 rounded hover:bg-gray-100"
                  >
                     <svg class="w-4 h-4 text-gray-500" fill="currentColor" viewBox="0 0 20 20">
                        <path
                           d="M12.586 4.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z"
                        />
                     </svg>
                     <a
                        v-if="attachment.storage_key || attachment.storage_path"
                        :href="getAttachmentUrl(attachment)"
                        target="_blank"
                        class="font-medium text-blue-600 hover:underline"
                     >
                        {{ attachment.filename }}
                     </a>
                     <span v-else class="font-medium">{{ attachment.filename }}</span>
                     <span v-if="attachment.size" class="text-xs text-gray-500">
                        ({{ formatFileSize(attachment.size) }})
                     </span>
                     <button
                        v-if="attachment.storage_key && attachment.id"
                        type="button"
                        @click="$emit('scanAttachmentForRFQ', attachment.id)"
                        :disabled="isScanning"
                        class="ml-auto text-xs px-2 py-1 bg-green-600 text-white rounded hover:bg-green-700 disabled:bg-gray-400 whitespace-nowrap"
                     >
                        {{ isScanning ? t('opportunities.scanning') : t('opportunities.scanRfq') }}
                     </button>
                  </div>
               </div>
            </div>

            <div v-if="pdfAttachments.length > 0" class="mt-4">
               <span class="font-medium text-gray-700"
                  >{{ t('opportunities.pdfPreviewLabel') }}:</span
               >
               <div class="mt-2 space-y-4">
                  <div v-for="pdf in pdfAttachments" :key="pdf.id" class="space-y-2">
                     <div class="text-xs text-gray-600">{{ pdf.filename }}</div>
                     <iframe
                        :src="getAttachmentUrl(pdf)"
                        class="w-full h-[600px] border border-gray-200 rounded"
                     ></iframe>
                  </div>
               </div>
            </div>

            <div
               v-if="isDocumentExpanded && sourceDocument.content"
               class="mt-4 pt-4 border-gray-300"
            >
               <div
                  class="bg-white p-3 rounded border border-gray-200 max-h-96 overflow-y-auto text-gray-800 whitespace-pre-wrap"
               >
                  {{ sourceDocument.content }}
               </div>
            </div>
         </div>
      </div>

      <div v-if="participants.length > 0" class="mt-6 border-t pt-6">
         <h3 class="text-sm font-semibold text-gray-700 mb-3">
            {{ t('opportunities.participantsLabel') }}
         </h3>
         <div class="space-y-2">
            <div
               v-for="participant in participants"
               :key="participant.contact_id"
               class="flex items-center justify-between p-3 bg-gray-50 rounded border border-gray-200"
            >
               <div>
                  <p class="text-sm font-medium text-gray-900">
                     {{ participant.contact.name }}
                  </p>
                  <p class="text-xs text-gray-600">{{ participant.contact.email }}</p>
               </div>
               <div class="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                  {{ formatRole(participant.role) }}
               </div>
            </div>
         </div>
      </div>
   </div>
</template>

<script setup lang="ts">
import { useI18n } from '../../../../i18n/useI18n';

const { t } = useI18n();

type Attachment = {
   id: string;
   filename: string;
   size?: number;
   storage_key?: string;
   storage_path?: string;
};

type Participant = {
   contact_id: string;
   role?: string;
   contact: { name?: string; email?: string };
};

const props = defineProps<{
   sourceDocument: Record<string, any>;
   isDocumentExpanded: boolean;
   isScanning: boolean;
   attachments: Attachment[];
   pdfAttachments: Attachment[];
   participants: Participant[];
   formatEmailDate: (value: string) => string;
   formatBodySize: (value: string) => string;
   formatFileSize: (value: number) => string;
   formatRole: (value?: string) => string;
   getAttachmentUrl: (value: Attachment) => string;
}>();

defineEmits(['toggleDocumentExpanded', 'scanAttachmentForRFQ']);
</script>
