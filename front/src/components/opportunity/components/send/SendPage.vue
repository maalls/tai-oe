<template>
   <div class="opportunity-page">
      <OpportunityHeader :opportunityId="opportunityId" activeTab="send" />

      <div v-if="errorMessage" class="mb-4 p-4 bg-red-100 text-red-700 rounded-lg">
         {{ errorMessage }}
      </div>

      <div v-if="successMessage" class="mb-4 p-4 bg-green-100 text-green-700 rounded-lg">
         {{ successMessage }}
      </div>

      <div v-if="isLoading" class="flex justify-center items-center py-12">
         <div class="text-gray-500">{{ t('opportunities.loadingDots') }}</div>
      </div>

      <div v-else class="opportunity-page-section bg-white rounded-lg shadow m-4 p-6">
         <!-- Show sent email details if stage is OFFER_SENT or later (including closed stages) -->
         <div
            v-if="opportunityStage === 'QUOTE_SENT' || opportunityStage === 'OFFER_SENT'"
            class="space-y-6"
         >
            <EmailSentView
               :title="t('opportunities.quoteSent')"
               :description="t('opportunities.quoteSentToClient')"
               :from="sentEmail?.from_email || 'maalls@gmail.com'"
               :to="emailForm.to"
               :cc="emailForm.cc"
               :subject="emailForm.subject"
               :body="emailForm.body"
               :attachmentName="quoteDocument?.title ? `${quoteDocument.title}.pdf` : ''"
               :downloadUrl="quoteDownloadUrl"
               :sentAtText="
                  sentEmail?.sent_at
                     ? t('opportunities.quoteSentOn', {
                          date: formatDate(sentEmail.sent_at),
                       })
                     : ''
               "
            />
            <!-- Display PDF when quote is sent -->
            <div
               v-if="quoteDocument && quoteDocument.storage_key"
               class="m-10 bg-white rounded-lg shadow border border-gray-200"
               style="height: calc(100vh - 500px); min-height: 400px"
            >
               <PdfViewer :pdfUrl="quotePreviewUrl" />
            </div>
         </div>

         <!-- Sender info -->
         <div
            v-if="user?.email || senderDisplayName"
            class="mb-6 p-4 bg-gray-50 border border-gray-200 rounded flex items-center gap-3"
         >
            <svg
               class="w-6 h-6 text-gray-400"
               fill="none"
               stroke="currentColor"
               viewBox="0 0 24 24"
            >
               <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M5.121 17.804A13.937 13.937 0 0112 15c2.5 0 4.847.655 6.879 1.804M15 10a3 3 0 11-6 0 3 3 0 016 0z"
               />
            </svg>
            <div>
               <div class="font-medium text-gray-800">
                  {{ senderDisplayName || t('opportunities.senderUnknown') }}
               </div>
               <div class="text-xs text-gray-600">{{ user?.email }}</div>
            </div>
         </div>

         <!-- Send form (always available) -->
         <form
            v-if="opportunityStage !== 'QUOTE_SENT' && opportunityStage !== 'OFFER_SENT'"
            @submit.prevent="sendEmail"
            class="space-y-4"
         >
            <div class="mb-4">
               <h3 class="text-lg font-semibold text-gray-900">
                  {{
                     opportunityStage === 'NEGOTIATION'
                        ? t('opportunities.sendNegotiationFollowUp')
                        : t('opportunities.sendQuote')
                  }}
               </h3>
               <p class="text-sm text-gray-600 mt-1">
                  {{
                     opportunityStage === 'NEGOTIATION'
                        ? t('opportunities.sendNegotiationDescription')
                        : t('opportunities.sendQuoteDescription')
                  }}
               </p>
            </div>

            <div>
               <label class="block text-sm font-medium text-gray-700 mb-2">
                  {{ t('opportunities.toLabel') }}
               </label>
               <input
                  v-model="emailForm.to"
                  type="text"
                  required
                  :placeholder="t('opportunities.toPlaceholder', { at: '@' })"
                  class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
               />
            </div>

            <div>
               <label class="block text-sm font-medium text-gray-700 mb-2">
                  {{ t('opportunities.ccLabel') }}
               </label>
               <input
                  v-model="emailForm.cc"
                  type="text"
                  :placeholder="t('opportunities.ccPlaceholder', { at: '@' })"
                  class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
               />
            </div>

            <div>
               <label class="block text-sm font-medium text-gray-700 mb-2">
                  {{ t('opportunities.subjectLabel') }}
               </label>
               <input
                  v-model="emailForm.subject"
                  type="text"
                  required
                  :placeholder="subjectPlaceholder"
                  class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
               />
            </div>

            <div>
               <label class="block text-sm font-medium text-gray-700 mb-2">
                  {{ t('opportunities.messageLabel') }}
               </label>
               <textarea
                  v-model="emailForm.body"
                  rows="8"
                  required
                  :placeholder="bodyPlaceholder"
                  class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
               ></textarea>
            </div>

            <div
               v-if="quoteDocument?.storage_key"
               class="border border-gray-300 rounded-lg p-4 bg-gray-50"
            >
               <div class="flex items-center gap-2 text-sm text-gray-700">
                  <svg
                     class="w-5 h-5 text-gray-500"
                     fill="none"
                     stroke="currentColor"
                     viewBox="0 0 24 24"
                  >
                     <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13"
                     />
                  </svg>
                  <span class="font-medium">{{ t('opportunities.attachment') }}</span>
                  <span
                     >{{ quoteDocument.title || t('opportunities.quoteTitleFallback') }}.pdf</span
                  >
                  <span
                     v-if="opportunityStage === 'NEGOTIATION'"
                     class="text-xs ml-2 px-2 py-1 bg-blue-100 text-blue-700 rounded"
                  >
                     {{ t('opportunities.updated') }}
                  </span>
               </div>
            </div>

            <div
               v-if="quoteDocument && quoteDocument.storage_key"
               class="bg-white rounded-lg shadow"
               style="height: calc(100vh - 450px); min-height: 400px"
            >
               <PdfViewer :pdfUrl="quoteDocument.pdf_url" />
            </div>

            <div
               v-if="!quoteDocument || !quoteDocument.storage_key"
               class="text-center py-3 text-gray-500"
            >
               {{ t('opportunities.quotePdfNotGenerated') }}

               <button @click="generateQuotePdf()" class="btn btn-primary ml-2">
                  {{ t('opportunities.generatePdf') }}
               </button>
            </div>

            <div class="flex gap-3 pt-4">
               <button type="submit" :disabled="isSending" class="btn btn-primary">
                  {{ isSending ? t('opportunities.sending') : t('opportunities.sendEmail') }}
               </button>
               <router-link :to="`/opportunities/${opportunityId}/quote`" class="btn btn-secondary">
                  {{ t('common.cancel') }}
               </router-link>
            </div>
         </form>
      </div>
   </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useAuth } from '../../../../stores/auth';
import OpportunityHeader from '../../OpportunityHeader.vue';
import PdfViewer from '../../../PdfViewer.vue';
import EmailSentView from '../../../shared/EmailSentView.vue';
import { useI18n } from '../../../../i18n/useI18n';
import { listContacts } from '../../../../api/contact';
import { listOpportunityDocuments } from '../../../../api/document';
import { getOpportunitySentEmail, getOpportunitySummary } from '../../../../api/opportunity';
import { getOpportunitySource } from '../../../../api/opportunitySource';
const route = useRoute();
const router = useRouter();
const { session, user } = useAuth();
const { t, locale } = useI18n();
const opportunityId = route.params.id as string;

const isLoading = ref(true);
const isSending = ref(false);
const errorMessage = ref('');
const successMessage = ref('');
const quoteDocument = ref<any>(null);
const sentEmail = ref<any>(null);
const opportunityStage = ref('');

const senderDisplayName = computed(() => {
   const metadata = (user.value?.user_metadata || {}) as Record<string, any>;
   return String(metadata.full_name || metadata.name || '');
});

const emailForm = ref({
   to: '',
   cc: '',
   subject: '',
   body: '',
});

const subjectPlaceholder = computed(() => {
   return opportunityStage.value === 'NEGOTIATION'
      ? t('opportunities.subjectPlaceholderNegotiation')
      : t('opportunities.subjectPlaceholderQuote');
});

const bodyPlaceholder = computed(() => {
   if (opportunityStage.value === 'NEGOTIATION') {
      return t('opportunities.bodyPlaceholderNegotiation');
   }
   return t('opportunities.bodyPlaceholderQuote');
});

const quoteDownloadUrl = computed(() => {
   return quoteDocument.value?.storage_key
      ? `/api/quotes/download/${quoteDocument.value.storage_key}`
      : '';
});

const quotePreviewUrl = computed(() => {
   return quoteDocument.value?.storage_key
      ? `/api/quotes/download/${quoteDocument.value.storage_key}?inline=1`
      : '';
});

const loadQuoteDocument = async () => {
   try {
      const documents = await listOpportunityDocuments(opportunityId);
      const latestQuote =
         documents.find(
            (doc) => doc.type === 'QUOTE' && (doc.status === 'DRAFT' || doc.status === 'SENT')
         ) || null;

      if (latestQuote) {
         quoteDocument.value = latestQuote as any;
         quoteDocument.value.pdf_url = `/api/quotes/download/${quoteDocument.value.storage_key}`;
         // Set default subject
         if (!emailForm.value.subject) {
            emailForm.value.subject = t('opportunities.quoteSubjectPrefix', {
               title: quoteDocument.value.title || t('opportunities.yourRequest'),
            });
         }
      } else {
         quoteDocument.value = null;
      }
   } catch (error) {
      console.error('[SendPage] Unexpected error loading quote document:', error);
   }
};

const generateQuotePdf = async () => {
   console.log('[SendPage] Generating quote PDF...', quoteDocument.value.id);
   const headers: HeadersInit = { 'Content-Type': 'application/json' };
   if (session.value?.access_token) {
      headers['Authorization'] = `Bearer ${session.value.access_token}`;
   }

   const response = await fetch(`/api/quote/${quoteDocument.value.id}/pdf`, {
      method: 'POST',
      headers,
   });

   if (!response.ok) {
      throw new Error(t('opportunities.errors.failedToGenerateQuotePdf'));
   } else {
      await loadQuoteDocument();
   }
};

const loadSentEmailRecord = async () => {
   try {
      if (!quoteDocument.value?.id) {
         sentEmail.value = null;
         return;
      }

      const data = await getOpportunitySentEmail(opportunityId, quoteDocument.value.id);

      if (data) {
         sentEmail.value = data as any;
         console.log('[SendPage] Loaded sent email record:', data);
         emailForm.value = {
            to: (data as any).to_emails?.join(', ') || '',
            cc: (data as any).cc_emails?.join(', ') || '',
            subject: (data as any).subject || '',
            body: (data as any).body || '',
         };
      } else {
         console.log('[SendPage] No sent email record found');
      }
   } catch (error) {
      console.error('[SendPage] Unexpected error loading sent email record:', error);
   }
};

const loadRecipientEmail = async () => {
   try {
      const [oppData, sourceData] = await Promise.all([
         getOpportunitySummary(opportunityId),
         getOpportunitySource(opportunityId),
      ]);

      if (!oppData) {
         console.error('[SendPage] Error loading opportunity: empty payload');
         return;
      }

      // Store the stage
      opportunityStage.value = oppData.stage || '';
      console.log('[SendPage] Opportunity stage:', opportunityStage.value);
      console.log('[SendPage] Opportunity source:', oppData.source);

      // First, try to load BUYER participant email
      const buyerContact = (sourceData?.participants || []).find(
         (participant) => participant?.role === 'BUYER' && participant?.contact?.email
      )?.contact as any;

      if (buyerContact) {
         if (buyerContact?.email && !emailForm.value.to) {
            emailForm.value.to = buyerContact.email;
            console.log('[SendPage] Auto-filled "To" from BUYER participant:', buyerContact.email);

            // Auto-fill message body
            if (!emailForm.value.body) {
               const customerName = buyerContact.name || t('opportunities.customer');
               const opportunityName = oppData.name || t('opportunities.yourRequest');

               emailForm.value.body = t('opportunities.emailBodyTemplate', {
                  customerName,
                  opportunityName,
               });
            }
            return; // Exit early if we found a buyer participant
         }
      }

      // Fallback: load first account contact
      if (oppData.account_id) {
         const contacts = await listContacts();
         const accountContact = contacts.find(
            (contact) => contact.account_id === oppData.account_id
         ) as any;
         if (accountContact) {
            if (accountContact?.email && !emailForm.value.to) {
               emailForm.value.to = accountContact.email;
               console.log(
                  '[SendPage] Auto-filled "To" from account contact:',
                  accountContact.email
               );

               if (!emailForm.value.body) {
                  const customerName = accountContact.name || t('opportunities.customer');
                  const opportunityName = oppData.name || t('opportunities.yourRequest');

                  emailForm.value.body = t('opportunities.emailBodyTemplate', {
                     customerName,
                     opportunityName,
                  });
               }
               return;
            }
         }
      }

      // Fallback: If source is email, load the email details
      if (oppData.source === 'email') {
         const emailData = sourceData?.email as any;
         if (!emailData) return;

         // Auto-fill "To" field only (not CC)
         if (emailData.from_email && !emailForm.value.to) {
            emailForm.value.to = emailData.from_email;
         }

         // Auto-fill message body
         if (!emailForm.value.body) {
            const customerName = emailData.from_name || t('opportunities.customer');
            const opportunityName = oppData.name || t('opportunities.yourRequest');

            emailForm.value.body = t('opportunities.emailBodyTemplate', {
               customerName,
               opportunityName,
            });
         }
      }
   } catch (error) {
      console.error('[SendPage] Unexpected error loading recipient email:', error);
   }
};

const sendEmail = async () => {
   // For initial quote send (OFFER_SENT), require PDF
   // For negotiation (NEGOTIATION), allow sending with or without PDF
   // If PDF exists, send it regardless of stage
   if (!quoteDocument.value?.storage_key && opportunityStage.value !== 'NEGOTIATION') {
      errorMessage.value = t('opportunities.quotePdfMissingError');
      return;
   }

   isSending.value = true;
   errorMessage.value = '';
   successMessage.value = '';

   try {
      const headers: HeadersInit = { 'Content-Type': 'application/json' };
      if (session.value?.access_token) {
         headers['Authorization'] = `Bearer ${session.value.access_token}`;
      }

      // Parse comma-separated emails
      const toEmails = emailForm.value.to
         .split(',')
         .map((e) => e.trim())
         .filter((e) => e);
      const ccEmails = emailForm.value.cc
         ? emailForm.value.cc
              .split(',')
              .map((e) => e.trim())
              .filter((e) => e)
         : [];

      const payload = {
         to: toEmails,
         cc: ccEmails,
         subject: emailForm.value.subject,
         body: emailForm.value.body,
         // Include PDF if it exists (newly generated during negotiation, or initial quote)
         storage_key: quoteDocument.value?.storage_key || null,
         quote_id: quoteDocument.value?.id || null,
      };

      const response = await fetch(`/api/opportunity/${opportunityId}/send-quote`, {
         method: 'POST',
         headers,
         body: JSON.stringify(payload),
      });

      const result = await response.json();
      if (!response.ok) {
         throw new Error(result?.message || t('opportunities.failedToSendEmail'));
      }

      //successMessage.value = 'Email sent successfully!';

      // Reload to show sent email view (with timeout to prevent hanging)
      const reloadPromise = Promise.all([
         loadQuoteDocument(),
         loadSentEmailRecord(),
         loadRecipientEmail(), // This updates opportunityStage
      ]);

      const timeoutPromise = new Promise((resolve) => setTimeout(resolve, 3000));

      await Promise.race([reloadPromise, timeoutPromise]);
      await router.push(`/opportunities/${opportunityId}/pipeline`);
   } catch (error: any) {
      errorMessage.value = error?.message || t('opportunities.failedToSendEmail');
   } finally {
      isSending.value = false;
   }
};

const formatDate = (dateStr: string) => {
   if (!dateStr) return '-';
   const date = new Date(dateStr);
   const resolvedLocale = locale.value === 'fr' ? 'fr-FR' : 'en-US';
   return date.toLocaleDateString(resolvedLocale, {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: 'numeric',
      minute: 'numeric',
   });
};

// Watch for stage changes and reload email view if quote was sent
watch(opportunityStage, async (newStage) => {
   if (newStage === 'OFFER_SENT') {
      // Stage changed to OFFER_SENT, reload sent email details
      await loadSentEmailRecord();
   }
});

onMounted(async () => {
   isLoading.value = true;
   await loadQuoteDocument();
   await Promise.all([loadSentEmailRecord(), loadRecipientEmail()]);
   isLoading.value = false;
});
</script>
