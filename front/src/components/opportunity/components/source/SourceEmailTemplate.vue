<template>
   <div class="bg-white rounded-lg shadow p-6">
      <div class="border border-gray-300 rounded-lg p-4 bg-gray-50">
         <div class="flex items-center justify-between mb-3">
            <h3 class="text-sm font-semibold text-gray-700">
               {{ t('opportunities.sourceEmailTitle') }}
            </h3>
            <div class="flex gap-2">
               <button
                  type="button"
                  @click="$emit('extractAuthorAsContact')"
                  :disabled="isExtracting"
                  class="text-xs px-3 py-1 bg-green-600 text-white rounded hover:bg-green-700 disabled:bg-gray-400"
               >
                  {{
                     isExtracting ? t('opportunities.extracting') : t('opportunities.extractAuthor')
                  }}
               </button>
               <button
                  type="button"
                  @click="$emit('toggleEmailExpanded')"
                  class="text-xs text-blue-600 hover:text-blue-700"
               >
                  {{ isEmailExpanded ? t('opportunities.collapse') : t('opportunities.expand') }}
               </button>
            </div>
         </div>

         <div class="space-y-2 text-sm">
            <div>
               <span class="font-medium text-gray-700">{{ t('opportunities.fromLabel') }}:</span>
               <span class="ml-2 text-gray-900">
                  {{ sourceEmail.from_name || sourceEmail.from_email }}
               </span>
               <span
                  v-if="sourceEmail.from_email && sourceEmail.from_name"
                  class="ml-2 text-gray-600"
               >
                  (
                  <a
                     :href="`mailto:${sourceEmail.from_email}`"
                     class="hover:underline text-blue-600"
                  >
                     {{ sourceEmail.from_email }}
                  </a>
                  )
               </span>
            </div>
            <div>
               <span class="font-medium text-gray-700">{{ t('opportunities.subjectLabel') }}:</span>
               <span class="ml-2 text-gray-900">{{ sourceEmail.subject }}</span>
            </div>
            <div>
               <span class="font-medium text-gray-700">{{ t('opportunities.dateLabel') }}:</span>
               <span class="ml-2 text-gray-900">{{ formatEmailDate(sourceEmail.email_date) }}</span>
            </div>
            <!--div v-if="sourceEmail.body_full || sourceEmail.body_preview">
               <span class="font-medium text-gray-700">Body Size:</span>
               <span class="ml-2 text-gray-900">
                  {{ formatBodySize(sourceEmail.body_full || sourceEmail.body_preview) }}
               </span>
            </div-->

            <div v-if="isEmailExpanded" class="mt-4 pt-4 border-gray-300">
               <div
                  class="bg-white p-3 rounded border border-gray-200 max-h-96 overflow-y-auto text-gray-800"
                  :class="{
                     'whitespace-pre-wrap': !isHtmlContent(
                        sourceEmail.body_full || sourceEmail.body_preview
                     ),
                  }"
               >
                  <div
                     v-if="isHtmlContent(sourceEmail.body_full || sourceEmail.body_preview)"
                     class="prose prose-sm max-w-none"
                     v-html="sanitizeHtml(sourceEmail.body_full || sourceEmail.body_preview)"
                  ></div>
                  <div v-else>
                     {{
                        sourceEmail.body_full ||
                        sourceEmail.body_preview ||
                        t('opportunities.noContent')
                     }}
                  </div>
               </div>
            </div>
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
               </div>
            </div>
         </div>

         <div v-if="pdfAttachments.length > 0" class="mt-4">
            <span class="font-medium text-gray-700">{{ t('opportunities.pdfPreviewLabel') }}:</span>
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
   sourceEmail: Record<string, any>;
   isEmailExpanded: boolean;
   isExtracting: boolean;
   attachments: Attachment[];
   pdfAttachments: Attachment[];
   participants: Participant[];
   formatEmailDate: (value: string) => string;
   formatBodySize: (value: string) => string;
   formatFileSize: (value: number) => string;
   formatRole: (value?: string) => string;
   isHtmlContent: (value: string) => boolean;
   sanitizeHtml: (value: string) => string;
   getAttachmentUrl: (value: Attachment) => string;
}>();

defineEmits(['toggleEmailExpanded', 'extractAuthorAsContact']);
</script>
