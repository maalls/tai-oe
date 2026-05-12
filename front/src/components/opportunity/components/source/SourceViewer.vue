<template>
   <div class="pt-4"></div>
   <div class="">
      <!-- Email Source -->
      <div v-if="sourceEmail">
         <h3 v-if="true" class="text-sm font-semibold text-gray-700">
            {{ sourceEmail ? t('opportunities.email') : t('opportunities.userForm') }}

            <span v-if="sourceDocument" class="ml-2 font-normal">
               <span class="text-gray-900">{{
                  sourceDocument.title || t('opportunities.untitled')
               }}</span>
               <span class="text-gray-900">{{ formatEmailDate(sourceDocument.created_at) }}</span>
            </span>

            <span
               v-if="sourceType"
               class="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-700"
            >
               {{ sourceType }}
            </span>
         </h3>
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

            <div class="mt-4 pt-4 border-gray-300">
               <div
                  class="bg-white p-3 rounded border border-gray-200 max-h-96 overflow-y-auto text-gray-800"
               >
                  <div
                     v-if="isHtmlContent(sourceEmail.body_full || sourceEmail.body_preview)"
                     class="prose prose-sm max-w-none"
                     v-html="sanitizeHtml(sourceEmail.body_full || sourceEmail.body_preview)"
                  ></div>
                  <div
                     v-else
                     class="whitespace-pre-wrap"
                     v-html="
                        linkifyContent(
                           sourceEmail.body_full ||
                              sourceEmail.body_preview ||
                              t('opportunities.noContent')
                        )
                     "
                  ></div>
               </div>
            </div>
         </div>

         <!-- Participants -->
         <div v-if="participants.length > 0" class="mt-4 pt-4 border-t border-gray-200">
            <span class="font-medium text-gray-700"
               >{{ t('opportunities.participantsLabel') }}:</span
            >
            <div class="ml-2 mt-2 space-y-1">
               <div
                  v-for="participant in participants"
                  :key="participant.id"
                  class="flex items-center gap-2 text-sm text-gray-700"
               >
                  <span class="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs font-medium">
                     {{ formatRole(participant.role) }}
                  </span>
                  <span>
                     {{
                        participant.contact?.name ||
                        participant.name ||
                        participant.contact?.email ||
                        participant.email
                     }}
                  </span>
                  <span
                     v-if="participant.contact?.email || participant.email"
                     class="text-gray-500"
                  >
                     ({{ participant.contact?.email || participant.email }})
                  </span>
               </div>
            </div>
         </div>

         <!-- Attachments -->
         <div v-if="nonPdfAttachments.length > 0" class="mt-4 pt-4 border-t border-gray-200">
            <span class="font-medium text-gray-700"
               >{{ t('opportunities.attachmentsLabel') }}:</span
            >
            <div class="ml-2 mt-2 space-y-2">
               <div
                  v-for="attachment in nonPdfAttachments"
                  :key="attachment.id"
                  class="flex items-center justify-between gap-2 text-sm text-gray-700 bg-gray-50 p-2 rounded hover:bg-gray-100"
               >
                  <div class="flex items-center gap-2">
                     <svg class="w-4 h-4 text-gray-500" fill="currentColor" viewBox="0 0 24 24">
                        <path
                           d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0013.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z"
                        />
                     </svg>
                     <span>{{ attachment.filename }}</span>
                     <span class="text-xs text-gray-500">
                        ({{ formatFileSize(attachment.size ?? attachment.file_size ?? 0) }})
                     </span>
                     <div
                        v-if="
                           attachment.filename?.toLowerCase().endsWith('.pdf') &&
                           hasGeneratedRFQ(attachment.id)
                        "
                        class="px-2 py-1 bg-green-100 text-green-700 text-xs font-medium rounded"
                     >
                        ✓ {{ t('opportunities.rfqGenerated') }}
                     </div>
                  </div>
                  <a
                     v-if="attachment.storage_key || attachment.storage_path"
                     :href="getAttachmentUrl(attachment)"
                     target="_blank"
                     class="text-xs px-2 py-1 bg-blue-600 text-white rounded hover:bg-blue-700"
                  >
                     {{ t('opportunities.download') }}
                  </a>
               </div>
            </div>
         </div>

         <!-- PDF Preview -->
         <div v-if="pdfAttachments.length > 0" class="mt-4 pt-4 border-gray-200 space-y-4">
            <div v-for="pdf in pdfAttachments" :key="pdf.id" class="space-y-2">
               <div class="flex items-center justify-between gap-2">
                  <h4 class="text-sm font-medium text-gray-700">
                     {{ t('opportunities.pdfPreviewLabel') }}: {{ pdf.filename }}
                  </h4>
                  <div class="flex items-center gap-2">
                     <button
                        v-if="onScanAttachmentForRFQ"
                        type="button"
                        :disabled="isScanning"
                        @click="onScanAttachmentForRFQ(pdf.id)"
                        class="text-xs px-3 py-1 bg-purple-600 text-white rounded hover:bg-purple-700 disabled:bg-gray-400"
                     >
                        {{ isScanning ? t('opportunities.scanning') : t('opportunities.scanRfq') }}
                     </button>
                  </div>
               </div>
               <div>
                  <PdfAnnotator
                     v-if="getAttachmentUrl(pdf)"
                     :pdfUrl="getAttachmentUrl(pdf)"
                     :pdfFilename="pdf.filename"
                  />
               </div>
            </div>
         </div>
      </div>

      <!-- Document Source -->
      <div v-else-if="sourceDocument">
         <div class="text-sm">
            <div v-if="isExpanded" class="border-gray-300">
               <!-- Edit mode -->
               <div v-show="isEditingContent" class="space-y-2">
                  <div class="flex items-center justify-between">
                     <span class="text-xs text-gray-500">{{
                        t('opportunities.contentLabel')
                     }}</span>
                     <span
                        v-if="sourceType"
                        :id="`source-${sourceDocument.id}-type`"
                        name="source-type"
                        class="ao inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-700"
                     >
                        {{ sourceType }}
                     </span>

                     <span v-else class="text-xs text-blue-600">{{
                        t('opportunities.saving')
                     }}</span>
                  </div>
                  <RichTextEditor
                     ref="editorRef"
                     v-model="editedContent"
                     @blur="handleBlur"
                     @keydown.esc="handleBlur"
                     name="opportunity-source-content"
                     :id="`source-content`"
                     rows="4"
                     class="ao w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent outline-none font-mono text-sm"
                     :placeholder="t('opportunities.enterDocumentContent')"
                  />
               </div>
               <!-- Display mode -->
               <div v-show="!isEditingContent">
                  <div class="flex items-center justify-between mb-2">
                     <span class="text-xs text-gray-500">
                        {{ t('opportunities.documentContentClickToEdit') }}
                     </span>
                     <span
                        v-if="sourceType"
                        :id="`source-type`"
                        name="source-type"
                        class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-700"
                     >
                        {{ sourceType }}
                     </span>
                  </div>
                  <div
                     @click="handleContentClick"
                     class="bg-white p-3 rounded border border-gray-200 max-h-96 overflow-y-auto text-gray-800 whitespace-pre-wrap cursor-text hover:border-blue-300 hover:bg-blue-50/30 transition-colors"
                  >
                     <span v-if="!sourceDocument.content" class="text-gray-400">
                        {{ t('opportunities.noContentYetClickToAdd') }}
                     </span>
                     <span v-else v-html="linkifyContent(sourceDocument.content)"></span>
                  </div>
               </div>
            </div>
         </div>

         <!-- Attachments -->

         <!-- PDF Preview -->
         <div v-if="pdfAttachments.length > 0" class="border-gray-200 space-y-4">
            <div v-for="pdf in pdfAttachments" :key="pdf.id" class="space-y-2">
               <div class="flex items-center justify-between gap-2">
                  <div class="flex items-center gap-2 text-sm font-medium text-gray-700">
                     <svg
                        class="w-4 h-4 text-gray-500 flex-shrink-0"
                        fill="currentColor"
                        viewBox="0 0 24 24"
                     >
                        <path
                           d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0013.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z"
                        />
                     </svg>
                     <span>{{ pdf.filename }}</span>

                     <a
                        v-if="pdf.storage_key || pdf.storage_path"
                        :href="getAttachmentUrl(pdf)"
                        target="_blank"
                        class="p-2 text-black font-bold hover:text-blue-700"
                        :title="t('opportunities.downloadPdf')"
                     >
                        <svg
                           style="display: inline"
                           class="w-4 h-4"
                           fill="none"
                           stroke="currentColor"
                           viewBox="0 0 24 24"
                        >
                           <path
                              stroke-linecap="round"
                              stroke-linejoin="round"
                              stroke-width="2"
                              d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                           />
                        </svg>
                     </a>
                  </div>
                  <div class="flex gap-2">
                     <div
                        v-if="hasGeneratedRFQ(pdf.id)"
                        class="px-2 py-1 bg-green-100 text-green-700 text-xs font-medium rounded"
                     >
                        ✓ {{ t('opportunities.rfqGenerated') }}
                     </div>
                  </div>
               </div>
               <div
                  class="bg-gray-100 rounded border border-gray-300 overflow-hidden"
                  style="height: 500px"
               >
                  <PdfAnnotator
                     v-if="getAttachmentUrl(pdf)"
                     :pdfUrl="getAttachmentUrl(pdf)"
                     :pdfFilename="pdf.filename"
                  />
               </div>
            </div>
         </div>
         <div v-if="nonPdfAttachments.length > 0" class="mt-4 pt-4 border-t border-gray-200">
            <span class="font-medium text-gray-700"
               >{{ t('opportunities.attachmentsLabel') }}:</span
            >
            <div class="ml-2 mt-2 space-y-2">
               <div
                  v-for="attachment in nonPdfAttachments"
                  :key="attachment.id"
                  class="flex items-center justify-between gap-2 text-sm text-gray-700 bg-gray-50 p-2 rounded hover:bg-gray-100"
               >
                  <div>
                     <div class="flex items-center gap-2">
                        <svg class="w-4 h-4 text-gray-500" fill="currentColor" viewBox="0 0 24 24">
                           <path
                              d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0013.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z"
                           />
                        </svg>
                        <span>{{ attachment.filename }}</span>
                        <span class="text-xs text-gray-500">
                           ({{ formatFileSize(attachment.size ?? attachment.file_size ?? 0) }})
                        </span>
                        <div
                           v-if="
                              attachment.filename?.toLowerCase().endsWith('.pdf') &&
                              hasGeneratedRFQ(attachment.id)
                           "
                           class="px-2 py-1 bg-green-100 text-green-700 text-xs font-medium rounded"
                        >
                           ✓ {{ t('opportunities.rfqGenerated') }}
                        </div>
                     </div>
                     <a
                        v-if="attachment.storage_key || attachment.storage_path"
                        :href="getAttachmentUrl(attachment)"
                        target="_blank"
                        class="text-xs px-2 py-1 bg-blue-600 text-white rounded hover:bg-blue-700"
                     >
                        {{ t('opportunities.download') }}
                     </a>
                  </div>
               </div>
            </div>
         </div>
         <div class="hidden text-xs m-6 rounded-2xl bg-amber-50 p-4">
            <p>Debug</p>
            <p>/api/opportunity/new/rfq/create-from-text</p>
            <p>business_handler.handle_create_opportunity_from_rfp</p>
            <p>
               if extracted again, it use a different path way (depends on if opportunity exist or
               not).
            </p>
            <p>
               Generate quote calls: /api/quote/${quoteDocument.value.id}/pdf
            </p>
            <p>and it's handled by business_handlers.handle_generate_quote_pdf</p>
         </div>
      </div>

      <!-- No source -->
      <div v-else class="text-sm text-gray-600 bg-gray-50 border border-gray-200 rounded p-4">
         {{ t('opportunities.noSourceDocument') }}
      </div>
   </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, watch } from 'vue';
import PdfAnnotator from '../../../PdfAnnotator.vue';
import RichTextEditor from '../../../../utils/RichTextEditor.vue';
import { linkifyWithLineBreaks } from '../../../../utils/linkify';
import { useI18n } from '../../../../i18n/useI18n';
const { t } = useI18n();
interface OpportunitySourceView {
   sourceType?: string;
   email?: any;
   document?: any;
   attachments: any[];
   pdfAttachments: any[];
   participants: any[];
   formatEmailDate: (date: string) => string;
   formatBodySize: (content: string | number) => string;
   formatFileSize: (bytes: number) => string;
   formatRole: (role: string) => string;
   isHtmlContent: (content: string) => boolean;
   sanitizeHtml: (html: string) => string;
   getAttachmentUrl: (attachment: any) => string;
}

const props = defineProps<{
   source: OpportunitySourceView | null;
   isExtracting?: boolean;
   isScanning?: boolean;
   onExtractAuthorAsContact?: () => void;
   onScanAttachmentForRFQ?: (attachmentId: string) => void;
   generatedAttachmentIds?: string[];
   onSaveContent?: (documentId: string, content: string) => Promise<void>;
}>();

const sourceEmail = computed(() => props.source?.email ?? null);
const sourceDocument = computed(() => props.source?.document ?? null);
const sourceType = computed(() => props.source?.sourceType ?? null);
const attachments = computed(() => props.source?.attachments ?? []);
const nonPdfAttachments = computed(() =>
   attachments.value.filter((a) => !a.filename?.toLowerCase().endsWith('.pdf'))
);
const pdfAttachments = computed(() => props.source?.pdfAttachments ?? []);
const participants = computed(() => props.source?.participants ?? []);
const isScanning = computed(() => props.isScanning ?? false);
const onScanAttachmentForRFQ = computed(() => props.onScanAttachmentForRFQ);

const isEditingContent = ref(true);
const editedContent = ref('');
const isSavingContent = ref(false);
const editorRef = ref<InstanceType<typeof RichTextEditor> | null>(null);

watch(
   () => sourceDocument.value?.content,
   (content) => {
      editedContent.value = content || '';
   },
   { immediate: true }
);

const handleContentClick = (event: MouseEvent) => {
   // Don't trigger edit mode if clicking on a link
   const target = event.target as HTMLElement;
   if (target.tagName === 'A' || target.closest('a')) {
      return;
   }
   startEditing();
};

const startEditing = async () => {
   editedContent.value = sourceDocument.value?.content || '';
   isEditingContent.value = true;

   // Auto-focus the textarea
   await nextTick();
   editorRef.value?.focus();
};

const focusContentEnd = async () => {
   await nextTick();
   const el = editorRef.value?.getTextarea();
   if (!el) return;
   const length = el.value.length;
   el.focus();
   el.setSelectionRange(length, length);
};

const handleBlur = async () => {
   // Auto-save on blur if content changed
   if (editedContent.value !== sourceDocument.value?.content) {
      await saveContent();
   }
};

const saveContent = async () => {
   if (!sourceDocument.value?.id || !props.onSaveContent) return;

   isSavingContent.value = true;
   try {
      await props.onSaveContent(sourceDocument.value.id, editedContent.value);
   } catch (error) {
      console.error('[SourceViewer] Error saving content:', error);
   } finally {
      isSavingContent.value = false;
   }
};

const formatEmailDate = (value: string) => props.source?.formatEmailDate?.(value) ?? '';
const formatFileSize = (value: number) => props.source?.formatFileSize?.(value) ?? '';
const formatRole = (value: string) => props.source?.formatRole?.(value) ?? value;
const isHtmlContent = (value: string) => props.source?.isHtmlContent?.(value) ?? false;
const sanitizeHtml = (value: string) => props.source?.sanitizeHtml?.(value) ?? value;
const getAttachmentUrl = (attachment: any) => props.source?.getAttachmentUrl?.(attachment) ?? '';

const isExpanded = ref(true);

const hasGeneratedRFQ = (attachmentId: string) => {
   return props.generatedAttachmentIds?.includes(attachmentId) ?? false;
};

const linkifyContent = (text: string) => {
   return linkifyWithLineBreaks(text);
};

defineExpose({ focusContentEnd });
</script>
