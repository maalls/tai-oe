<template>
   <div class="mt-2 flex items-center gap-2 flex-wrap">
      <div v-if="message.hasAttachments" class="flex items-center gap-1">
         <svg class="w-4 h-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
               stroke-linecap="round"
               stroke-linejoin="round"
               stroke-width="2"
               d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.415a6 6 0 108.486 8.486L7.172 11"
            ></path>
         </svg>
         <span class="text-xs text-gray-600">
            {{ message.attachmentCount }}
            {{
               message.attachmentCount === 1
                  ? t('mail.attachmentSingular')
                  : t('mail.attachmentPlural')
            }}
         </span>
      </div>
   </div>
   <div class="border-t border-gray-200 bg-white p-4">
      <!-- Trust Score Section -->
      <!--div
         v-if="message.auth_score !== undefined"
         class="bg-white rounded p-4 border-2"
         :class="trustBorderClass"
      >
         <div class="flex items-center justify-between mb-2">
            <h4 class="font-semibold" :class="trustTextClass">Sender Trust & Security</h4>
            <TrustBadge
               :authScore="message.auth_score"
               :isVerified="message.is_verified"
               :spfStatus="message.spf_status"
               :dkimStatus="message.dkim_status"
               :dmarcStatus="message.dmarc_status"
               :showScore="true"
               :showDot="false"
            />
         </div>
         <div class="grid grid-cols-3 gap-3 text-sm">
            <div :class="['p-2 rounded', getAuthStatusClass(message.spf_status)]">
               <p class="font-semibold">SPF</p>
               <p class="text-xs">{{ message.spf_status || 'Unknown' }}</p>
            </div>
            <div :class="['p-2 rounded', getAuthStatusClass(message.dkim_status)]">
               <p class="font-semibold">DKIM</p>
               <p class="text-xs">{{ message.dkim_status || 'Unknown' }}</p>
            </div>
            <div :class="['p-2 rounded', getAuthStatusClass(message.dmarc_status)]">
               <p class="font-semibold">DMARC</p>
               <p class="text-xs">{{ message.dmarc_status || 'Unknown' }}</p>
            </div>
         </div>
      </div-->

      <!--div v-if="message.category" class="bg-green-50 rounded p-4 border border-green-200">
         <h4 class="font-semibold text-gray-800 mb-2">Classification Result</h4>
         <div class="space-y-2">
            <div>
               <p class="text-xs text-gray-600">Category</p>
               <p class="font-semibold text-green-700">{{ message.category }}</p>
            </div>
            <div>
               <p class="text-xs text-gray-400">suggested: {{ message.category_suggestion }}</p>
            </div>
            <div v-if="message.classification_reason">
               <p class="text-xs text-gray-600">Reason</p>
               <p class="text-sm text-gray-800">{{ message.classification_reason }}</p>
            </div>
            <div v-if="message.classified_at" class="text-xs text-gray-600">
               Classified: {{ formatDate(message.classified_at) }}
            </div>
         </div>
      </div-->

      <!-- Extracted Contact & Account Info -->
      <div v-if="extractedContactInfo" class="pt-4">
         <div class="flex items-center justify-between mb-3">
            <h4 class="font-semibold text-green-800">{{ t('mail.contactAccountExtracted') }}</h4>
            <router-link
               to="/contacts"
               class="px-3 py-1 text-xs bg-green-600 text-white rounded hover:bg-green-700 transition-colors"
            >
               {{ t('mail.viewInContacts') }}
            </router-link>
         </div>
         <div class="grid grid-cols-2 gap-4">
            <!-- Contact Info -->
            <div class="bg-blue-50 rounded p-3">
               <h5 class="text-sm font-bold text-blue-900 mb-2">{{ t('mail.contact') }}</h5>
               <div class="space-y-1 text-sm">
                  <p v-if="extractedContactInfo.contact?.name">
                     <span class="font-semibold">{{ t('mail.nameLabel') }}:</span>
                     {{ extractedContactInfo.contact.name }}
                  </p>
                  <p v-if="extractedContactInfo.contact?.email" class="text-blue-600 truncate">
                     <span class="font-semibold">{{ t('mail.emailLabel') }}:</span>
                     {{ extractedContactInfo.contact.email }}
                  </p>
                  <p v-if="extractedContactInfo.contact?.phone">
                     <span class="font-semibold">{{ t('mail.phoneLabel') }}:</span>
                     {{ extractedContactInfo.contact.phone }}
                  </p>
                  <p v-if="extractedContactInfo.contact?.title">
                     <span class="font-semibold">{{ t('mail.titleLabel') }}:</span>
                     {{ extractedContactInfo.contact.title }}
                  </p>
                  <p v-if="extractedContactInfo.contact?.id" class="text-xs text-gray-600">
                     {{ t('mail.idLabel') }}:
                     {{ extractedContactInfo.contact.id.substring(0, 8) }}...
                  </p>
               </div>
            </div>
            <!-- Account Info -->
            <div class="bg-purple-50 rounded p-3">
               <h5 class="text-sm font-bold text-purple-900 mb-2">{{ t('mail.company') }}</h5>
               <div class="space-y-1 text-sm">
                  <p v-if="extractedContactInfo.account?.name">
                     <span class="font-semibold">{{ t('mail.nameLabel') }}:</span>
                     {{ extractedContactInfo.account.name }}
                  </p>
                  <p v-if="extractedContactInfo.account?.industry">
                     <span class="font-semibold">{{ t('mail.industryLabel') }}:</span>
                     {{ extractedContactInfo.account.industry }}
                  </p>
                  <p v-if="extractedContactInfo.account?.website" class="text-purple-600 truncate">
                     <span class="font-semibold">{{ t('mail.websiteLabel') }}:</span>
                     {{ extractedContactInfo.account.website }}
                  </p>
                  <p v-if="extractedContactInfo.account?.phone">
                     <span class="font-semibold">{{ t('mail.phoneLabel') }}:</span>
                     {{ extractedContactInfo.account.phone }}
                  </p>
                  <p v-if="extractedContactInfo.account?.id" class="text-xs text-gray-600">
                     {{ t('mail.idLabel') }}:
                     {{ extractedContactInfo.account.id.substring(0, 8) }}...
                  </p>
               </div>
            </div>
         </div>
      </div>

      <!-- Message Body -->
      <div v-if="isLoadingBody" class="pt-4 flex justify-center py-8">
         <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
      <div v-else-if="messageBody" class="pt-4">
         <!--div class="flex items-center justify-between mb-3">
            <h4 class="font-semibold text-gray-800">Email Body</h4>
            <button
               @click.stop="extractContactFromBody"
               :disabled="isExtractingContact"
               class="px-3 py-1 text-xs bg-purple-600 text-white rounded hover:bg-purple-700 disabled:bg-gray-400 transition-colors"
            >
               {{ isExtractingContact ? 'Extracting...' : '✦ Extract Contact' }}
            </button>
         </div-->
         <div
            class="text-sm text-gray-800"
            :class="{ 'whitespace-pre-wrap': !isHtmlContent(messageBody.body) }"
         >
            <div
               v-if="isHtmlContent(messageBody.body)"
               class="prose prose-sm max-w-none"
               v-html="sanitizeHtml(messageBody.body)"
            ></div>
            <div v-else>{{ messageBody.body }}</div>
            <!--div class="mt-4">
               <span
                  v-for="label in message.labels"
                  :key="label"
                  class="px-2 py-1 mr-2 text-xs bg-gray-100 text-gray-700 rounded"
               >
                  {{ label }}
               </span>
            </div-->
         </div>
      </div>
      <div v-else class="pt-4 text-center text-gray-600">
         <p class="text-sm">{{ t('mail.clickClassifyHint') }}</p>
      </div>

      <!-- Attachments -->
      <div v-if="isLoadingAttachments" class="pt-4 flex justify-center py-4">
         <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
      </div>
      <div v-else-if="(localAttachments ?? []).length > 0" class="pt-4">
         <h4 class="font-semibold text-gray-800 mb-3">
            {{ t('mail.attachmentsTitle', { count: localAttachments?.length || 0 }) }}
         </h4>
         <div class="space-y-2">
            <div
               v-for="attachment in localAttachments"
               :key="attachment.id"
               class="flex items-center gap-3 p-3 rounded border border-gray-100 bg-white hover:bg-white cursor-pointer transition-colors"
               @click="handleAttachmentClick(attachment)"
            >
               <img
                  v-if="isImageAttachment(attachment)"
                  :src="getAttachmentPreviewUrl(attachment)"
                  :alt="attachment.filename"
                  class="w-10 h-10 rounded object-cover border border-gray-200"
                  loading="lazy"
               />
               <svg
                  v-else
                  class="w-4 h-4 text-gray-500 shrink-0"
                  fill="currentColor"
                  viewBox="0 0 20 20"
               >
                  <path
                     d="M12.586 4.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z"
                  />
               </svg>
               <div class="flex-1 min-w-0">
                  <p class="text-sm font-medium text-gray-900 truncate">
                     {{ attachment.filename }}
                  </p>
                  <p v-if="attachment.mime_type" class="text-xs text-gray-600">
                     {{ attachment.mime_type }}
                  </p>
               </div>
               <div class="flex items-center gap-2 shrink-0">
                  <span v-if="attachment.size" class="text-xs text-gray-500">{{
                     formatFileSize(attachment.size)
                  }}</span>
                  <svg
                     class="w-4 h-4 text-blue-600"
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
               </div>
            </div>
         </div>

         <div
            v-if="selectedPdfUrl"
            class="mt-4 rounded border border-gray-200 bg-white overflow-hidden"
         >
            <div style="height: 560px">
               <PdfViewer :pdfUrl="selectedPdfUrl" />
            </div>
         </div>
      </div>

      <!-- Related Opportunities -->
      <div v-if="messageBody?.opportunities && messageBody.opportunities.length" class="pt-4">
         <h4 class="font-semibold text-gray-800 mb-2">{{ t('mail.relatedOpportunities') }}</h4>
         <ul class="space-y-2">
            <li
               v-for="opportunity in messageBody.opportunities"
               :key="opportunity.id"
               class="flex items-center justify-between text-sm"
            >
               <div class="min-w-0">
                  <router-link
                     class="text-blue-600 hover:text-blue-700 font-medium truncate"
                     :to="`/opportunities/${opportunity.id}/quote`"
                  >
                     {{ opportunity.name || opportunity.id }}
                  </router-link>
                  <div class="text-xs text-gray-500">
                     <span v-if="opportunity.stage">{{ getStageLabel(opportunity.stage) }}</span>
                     <span v-if="opportunity.stage && opportunity.status"> · </span>
                     <span v-if="opportunity.status">{{ getStatusLabel(opportunity.status) }}</span>
                  </div>
               </div>
            </li>
         </ul>
      </div>
   </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import type { MailMessage } from '../../types/mail';
import { useI18n } from '../../i18n/useI18n';
import PdfViewer from '../PdfViewer.vue';

interface Opportunity {
   id: string;
   name?: string;
   stage?: string;
   status?: string;
   account_id?: string;
   source_reference_id?: string;
}

interface MessageBody {
   body: string;
   opportunities?: Opportunity[];
}

interface Attachment {
   id: string;
   filename: string;
   mime_type?: string;
   size?: number;
}

const { message, messageBody, isLoadingBody, attachments, isLoadingAttachments } = defineProps<{
   message: MailMessage;
   messageBody: MessageBody | null;
   isLoadingBody: boolean;
   attachments?: Attachment[];
   isLoadingAttachments?: boolean;
}>();

const { t, te } = useI18n();

const getStageLabel = (stage?: string) => {
   if (!stage) return '';
   const key = `opportunities.stages.${stage}` as const;
   return te(key) ? t(key) : stage;
};

const getStatusLabel = (status?: string) => {
   if (!status) return '';
   const key = `opportunities.statuses.${status}` as const;
   return te(key) ? t(key) : status;
};

const formatFileSize = (bytes: number): string => {
   if (bytes === 0) return '0 B';
   const k = 1024;
   const sizes = ['B', 'KB', 'MB', 'GB'];
   const i = Math.floor(Math.log(bytes) / Math.log(k));
   return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
};

const downloadAttachment = (attachment: any) => {
   if (!attachment.id) {
      console.warn('No attachment ID:', attachment.filename);
      return;
   }

   try {
      // Use backend endpoint to download attachment
      const downloadUrl = `/api/email-attachment/${attachment.id}/download`;
      window.open(downloadUrl, '_blank');
   } catch (error) {
      console.error('Error downloading attachment:', error);
   }
};

const isPdfAttachment = (attachment: Attachment): boolean => {
   if (attachment.mime_type?.toLowerCase() === 'application/pdf') {
      return true;
   }
   const filename = attachment.filename?.toLowerCase() || '';
   return filename.endsWith('.pdf');
};

const selectedPdfUrl = ref<string>('');

const handleAttachmentClick = (attachment: Attachment) => {
   if (isPdfAttachment(attachment)) {
      const pdfUrl = `/api/email-attachment/${attachment.id}/download`;
      selectedPdfUrl.value = selectedPdfUrl.value === pdfUrl ? '' : pdfUrl;
      return;
   }
   downloadAttachment(attachment);
};

const localAttachments = ref<Attachment[]>([]);

// Sync local attachments with prop changes
watch(
   () => attachments,
   (newAttachments) => {
      if (newAttachments) {
         localAttachments.value = [...newAttachments];
      }
   },
   { immediate: true }
);

const isImageAttachment = (attachment: Attachment): boolean => {
   if (attachment.mime_type?.startsWith('image/')) {
      return true;
   }
   const filename = attachment.filename?.toLowerCase() || '';
   return ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp', '.svg'].some((ext) =>
      filename.endsWith(ext)
   );
};

const getAttachmentPreviewUrl = (attachment: Attachment): string => {
   return `/api/email-attachment/${attachment.id}/download`;
};

const isHtmlContent = (content: string): boolean => {
   if (!content) return false;
   return /<[^>]*>/.test(content);
};

const extractedContactInfo = ref<any>(null);

onMounted(() => {
   if (message?.id) {
      const key = `extracted_contact_${message.id}`;
      const stored = localStorage.getItem(key);
      if (stored) {
         try {
            extractedContactInfo.value = JSON.parse(stored);
         } catch (e) {
            console.error('Failed to parse stored extraction data:', e);
         }
      }
   }
});

const sanitizeHtml = (html: string): string => {
   const temp = document.createElement('div');
   temp.innerHTML = html;

   const dangerousTags = ['script', 'iframe', 'object', 'embed', 'form'];
   dangerousTags.forEach((tag) => {
      const elements = temp.querySelectorAll(tag);
      elements.forEach((el) => el.remove());
   });

   const styleTags = temp.querySelectorAll('style');
   styleTags.forEach((tag) => tag.remove());

   temp.querySelectorAll('*').forEach((el) => {
      Array.from(el.attributes).forEach((attr) => {
         if (attr.name.startsWith('on')) {
            el.removeAttribute(attr.name);
         }
      });

      // Remove inline styles to avoid overlays blocking clicks
      if (el instanceof HTMLElement && el.hasAttribute('style')) {
         el.removeAttribute('style');
      }
   });

   return temp.innerHTML;
};
</script>
