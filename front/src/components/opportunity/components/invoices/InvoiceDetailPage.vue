<template>
   <div class="opportunity-page">
      <OpportunityHeader :opportunityId="opportunityId" activeTab="invoices" />

      <div v-if="errorMessage" class="mb-4 p-4 bg-red-100 text-red-700 rounded-lg">
         {{ errorMessage }}
      </div>

      <div v-if="successMessage" class="mb-4 p-4 bg-green-100 text-green-700 rounded-lg">
         {{ successMessage }}
      </div>

      <div v-if="isLoading" class="flex justify-center items-center py-12">
         <div class="text-gray-500">{{ t('opportunities.loadingInvoice') }}</div>
      </div>

      <div
         v-else-if="invoice"
         class="opportunity-page-section grid grid-cols-1 lg:grid-cols-2 gap-6"
      >
         <!-- Left Column: Invoice Details & PDF -->
         <div class="bg-white rounded-lg shadow">
            <!-- Invoice Header -->
            <div class="border-b px-6 py-4">
               <div class="flex items-start justify-between">
                  <div>
                     <h2 class="text-2xl font-bold text-gray-900">
                        {{ invoice.external_ref || invoice.title }}
                     </h2>
                     <p class="text-sm text-gray-500 mt-1">
                        {{ t('opportunities.invoiceIdLabel') }}: {{ invoice.id }}
                     </p>
                  </div>
                  <div class="text-right">
                     <div class="text-sm text-gray-600">{{ t('opportunities.statusLabel') }}</div>
                     <span
                        class="inline-flex items-center px-2.5 py-0.5 rounded-full text-sm font-medium mt-1"
                        :class="getStatusColor(invoice.status)"
                     >
                        {{ formatStatus(invoice.status) }}
                     </span>
                  </div>
               </div>
            </div>

            <!-- Invoice Details -->
            <div class="px-6 py-4 grid grid-cols-2 gap-4 border-b bg-gray-50">
               <div>
                  <div class="text-xs font-medium text-gray-500 uppercase">
                     {{ t('opportunities.amountLabel') }}
                  </div>
                  <div class="text-lg font-semibold text-gray-900 mt-1">
                     {{ formatCurrency(invoice.total_incl_tax, invoice.currency) }}
                  </div>
               </div>
               <div>
                  <div class="text-xs font-medium text-gray-500 uppercase">
                     {{ t('opportunities.currencyLabel') }}
                  </div>
                  <div class="text-lg font-semibold text-gray-900 mt-1">{{ invoice.currency }}</div>
               </div>
               <div>
                  <div class="text-xs font-medium text-gray-500 uppercase">
                     {{ t('opportunities.issuedDateLabel') }}
                  </div>
                  <div class="text-lg font-semibold text-gray-900 mt-1">
                     {{ formatDate(invoice.issued_at) }}
                  </div>
               </div>
               <div>
                  <div class="text-xs font-medium text-gray-500 uppercase">
                     {{ t('opportunities.created') }}
                  </div>
                  <div class="text-lg font-semibold text-gray-900 mt-1">
                     {{ formatDate(invoice.created_at) }}
                  </div>
               </div>
            </div>

            <!-- Actions -->
            <div class="flex flex-wrap items-center gap-2 px-6 py-4 border-b">
               <button
                  v-if="!pdfFilename"
                  type="button"
                  class="px-4 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-300"
                  @click="generateInvoicePdf"
                  :disabled="isGeneratingPdf"
               >
                  {{
                     isGeneratingPdf
                        ? t('opportunities.generatingPdf')
                        : t('opportunities.generatePdf')
                  }}
               </button>
               <button
                  v-if="pdfFilename"
                  type="button"
                  class="px-4 py-2 text-sm bg-green-600 text-white rounded hover:bg-green-700"
                  @click="downloadInvoicePdf"
               >
                  {{ t('opportunities.downloadPdf') }}
               </button>
               <button
                  v-if="pdfFilename && invoice?.status !== 'SENT'"
                  type="button"
                  class="px-4 py-2 text-sm bg-emerald-600 text-white rounded hover:bg-emerald-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
                  @click="regenerateInvoicePdf"
                  :disabled="isGeneratingPdf || invoice?.status === 'SENT'"
                  :title="
                     invoice?.status === 'SENT' ? t('opportunities.cannotRegenerateAfterSent') : ''
                  "
               >
                  {{
                     isGeneratingPdf
                        ? t('opportunities.regeneratingPdf')
                        : t('opportunities.regeneratePdf')
                  }}
               </button>
            </div>

            <!-- PDF Viewer -->
            <div v-if="pdfFilename" style="height: 100%; min-height: 400px">
               <PdfViewer :pdfUrl="invoicePreviewUrl" />
            </div>
            <div v-else class="p-6 text-center text-gray-500">
               {{ t('opportunities.noPdfGeneratedYet') }}
            </div>

            <!-- Invoice Breakdown -->
         </div>

         <!-- Right Column: Send Invoice Form or Sent Email View -->
         <div class="bg-white rounded-lg shadow p-6">
            <EmailSentView
               v-if="invoice?.status === 'SENT'"
               :title="t('opportunities.invoiceSentTitle')"
               :description="t('opportunities.invoiceSentDescription')"
               from="maalls@gmail.com"
               :to="emailForm.to"
               :cc="emailForm.cc"
               :subject="emailForm.subject"
               :body="emailForm.body"
               :attachmentName="`${invoice.external_ref || invoice.title}.pdf`"
               :downloadUrl="invoiceDownloadUrl"
               :sentAtText="
                  sentEmail?.sent_at
                     ? t('opportunities.invoiceSentOn', { date: formatDate(sentEmail.sent_at) })
                     : ''
               "
            />

            <!-- Send Invoice Form -->
            <div v-else>
               <h3 class="text-xl font-semibold text-gray-900 mb-4">
                  {{ t('opportunities.sendInvoiceTitle') }}
               </h3>

               <div
                  v-if="!pdfFilename"
                  class="p-4 bg-yellow-50 border border-yellow-200 rounded-lg mb-4"
               >
                  <p class="text-sm text-yellow-800">
                     {{ t('opportunities.generatePdfBeforeSending') }}
                  </p>
               </div>

               <div v-if="errorMessage" class="p-4 bg-red-50 border border-red-200 rounded-lg mb-4">
                  <p class="text-sm text-red-700">{{ errorMessage }}</p>
               </div>

               <form @submit.prevent="submitSendInvoice" class="space-y-4">
                  <div>
                     <label class="block text-sm font-medium text-gray-700 mb-2">
                        {{ t('opportunities.fromLabel') }}
                     </label>
                     <input
                        type="text"
                        value="maalls@gmail.com"
                        disabled
                        class="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-100 text-gray-600 cursor-not-allowed"
                     />
                  </div>

                  <div>
                     <label class="block text-sm font-medium text-gray-700 mb-2">
                        {{ t('opportunities.toLabelRequired') }} <span class="text-red-500">*</span>
                     </label>
                     <input
                        v-model="emailForm.to"
                        type="text"
                        required
                        :disabled="!pdfFilename"
                        :placeholder="t('opportunities.toPlaceholderDetailed')"
                        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
                     />
                     <p class="text-xs text-gray-500 mt-1">
                        {{ t('opportunities.separateMultipleEmails') }}
                     </p>
                  </div>

                  <div>
                     <label class="block text-sm font-medium text-gray-700 mb-2">
                        {{ t('opportunities.ccLabelSimple') }}
                     </label>
                     <input
                        v-model="emailForm.cc"
                        type="text"
                        :disabled="!pdfFilename"
                        :placeholder="t('opportunities.ccPlaceholderSimple')"
                        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
                     />
                  </div>

                  <div>
                     <label class="block text-sm font-medium text-gray-700 mb-2">
                        {{ t('opportunities.subjectLabelSimple') }}
                        <span class="text-red-500">*</span>
                     </label>
                     <input
                        v-model="emailForm.subject"
                        type="text"
                        required
                        :disabled="!pdfFilename"
                        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
                     />
                  </div>

                  <div>
                     <label class="block text-sm font-medium text-gray-700 mb-2">
                        {{ t('opportunities.messageLabelSimple') }}
                        <span class="text-red-500">*</span>
                     </label>
                     <textarea
                        v-model="emailForm.body"
                        rows="10"
                        required
                        :disabled="!pdfFilename"
                        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
                     ></textarea>
                  </div>

                  <div class="border border-gray-300 rounded-lg p-4 bg-gray-50">
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
                        <span>{{ invoice.external_ref || invoice.title }}.pdf</span>
                     </div>
                  </div>

                  <div class="flex justify-end pt-4">
                     <button
                        type="submit"
                        :disabled="isSending || !pdfFilename"
                        class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 font-medium"
                     >
                        {{
                           isSending
                              ? t('opportunities.sending')
                              : t('opportunities.sendInvoiceTitle')
                        }}
                     </button>
                  </div>
               </form>
            </div>
         </div>
      </div>

      <div v-else class="bg-white rounded-lg shadow p-6 text-center text-gray-500">
         {{ t('opportunities.invoiceNotFound') }}
      </div>
   </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { getOpportunityInvoiceView } from '../../../../api/invoice';
import { authFetch } from '../../../../api/authFetch';
import PdfViewer from '../../../PdfViewer.vue';
import OpportunityHeader from '../../OpportunityHeader.vue';
import EmailSentView from '../../../shared/EmailSentView.vue';
import { useI18n } from '../../../../i18n/useI18n';

const { t, te, locale } = useI18n();

const route = useRoute();
const router = useRouter();
const opportunityId = route.params.id as string;
const invoiceId = route.params.invoiceId as string;
const { getValidToken } = useAuth();
const invoice = ref<any>(null);
const isLoading = ref(true);
const isGeneratingPdf = ref(false);
const isSending = ref(false);
const errorMessage = ref('');
const successMessage = ref('');
const pdfFilename = ref<string | null>(null);
const emailForm = ref({
   to: '',
   cc: '',
   subject: '',
   body: '',
});
const sentEmail = ref<any>(null);

const invoiceDownloadUrl = computed(() => {
   return pdfFilename.value ? `/api/documents/download/${pdfFilename.value}` : '';
});

const invoicePreviewUrl = computed(() => {
   return pdfFilename.value ? `/api/documents/download/${pdfFilename.value}?inline=1` : '';
});

const loadInvoice = async () => {
   try {
      const view = await getOpportunityInvoiceView(opportunityId, invoiceId);
      const data = view.invoice;

      if (!data || data.type !== 'INVOICE') {
         errorMessage.value = t('opportunities.invoiceNotFound');
         console.error('[InvoiceDetailPage] Error loading invoice: invalid invoice payload');
         return;
      }

      invoice.value = data;
      pdfFilename.value = data.storage_key || null;

      // Load sent email data if invoice was sent
      if (data.status === 'SENT') {
         if (view.sent_email) {
            sentEmail.value = view.sent_email;
            emailForm.value = {
               to: view.sent_email.to_emails?.join(', ') || '',
               cc: view.sent_email.cc_emails?.join(', ') || '',
               subject: view.sent_email.subject || '',
               body: view.sent_email.body || '',
            };
         }
      }

      // If not sent, initialize email form with default values
      if (data.status !== 'SENT') {
         // Initialize email form with default values
         emailForm.value = {
            to: '',
            cc: '',
            subject: t('opportunities.invoiceEmailSubject', {
               reference: invoice.value.external_ref || invoice.value.id,
            }),
            body: t('opportunities.invoiceEmailBody', {
               reference: invoice.value.external_ref || invoice.value.id,
               amount: formatCurrency(invoice.value.total_incl_tax, invoice.value.currency),
            }),
         };

         if (view.default_contact?.email) {
            emailForm.value.to = view.default_contact.email;
         }
      }
   } catch (error: any) {
      errorMessage.value = error?.message || t('opportunities.failedToLoadInvoice');
      console.error('[InvoiceDetailPage] Error:', error);
   } finally {
      isLoading.value = false;
   }
};

const generateInvoicePdf = async () => {
   if (!invoice.value?.id) return;

   isGeneratingPdf.value = true;
   errorMessage.value = '';
   successMessage.value = '';

   try {
      const response = await authFetch(`/api/invoice/${invoice.value.id}/pdf`, {
         method: 'POST',
         headers: {
            'Content-Type': 'application/json',
         },
      });

      const result = await response.json();

      if (!response.ok) {
         throw new Error(result?.message || t('opportunities.failedToGeneratePdf'));
      }

      pdfFilename.value = result.storage_key;
      successMessage.value = t('opportunities.invoicePdfGeneratedSuccess');

      // Reload invoice to get updated storage_key
      await loadInvoice();

      setTimeout(() => {
         successMessage.value = '';
      }, 3000);
   } catch (error: any) {
      errorMessage.value = error?.message || t('opportunities.failedToGeneratePdf');
      console.error('[InvoiceDetailPage] Error generating PDF:', error);
   } finally {
      isGeneratingPdf.value = false;
   }
};

const regenerateInvoicePdf = async () => {
   if (!confirm(t('opportunities.confirmRegenerateInvoicePdf'))) {
      return;
   }
   await generateInvoicePdf();
};

const downloadInvoicePdf = () => {
   if (invoiceDownloadUrl.value) {
      window.open(invoiceDownloadUrl.value, '_blank');
   }
};

const submitSendInvoice = async () => {
   isSending.value = true;
   errorMessage.value = '';
   successMessage.value = '';

   try {
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
      };

      const response = await authFetch(`/api/invoice/${invoice.value.id}/send`, {
         method: 'POST',
         headers: {
            'Content-Type': 'application/json',
         },
         body: JSON.stringify(payload),
      });

      const result = await response.json();

      if (!response.ok) {
         throw new Error(result?.message || t('opportunities.failedToSendInvoice'));
      }

      successMessage.value = t('opportunities.invoiceSentSuccess');

      // Reload invoice to get updated status and sent email data
      await loadInvoice();

      await router.push(`/opportunities/${opportunityId}/pipeline`);

      // Scroll to top to show success message
      window.scrollTo({ top: 0, behavior: 'smooth' });

      setTimeout(() => {
         successMessage.value = '';
      }, 4000);
   } catch (error: any) {
      errorMessage.value = error?.message || t('opportunities.failedToSendInvoice');
      console.error('[InvoiceDetailPage] Error sending invoice:', error);

      // Scroll to top to show error message
      window.scrollTo({ top: 0, behavior: 'smooth' });
   } finally {
      isSending.value = false;
   }
};

const getStatusColor = (status: string) => {
   const colors: Record<string, string> = {
      DRAFT: 'bg-gray-100 text-gray-800',
      SENT: 'bg-blue-100 text-blue-800',
      RECEIVED: 'bg-blue-100 text-blue-800',
      PAID: 'bg-green-100 text-green-800',
      PARTIALLY_PAID: 'bg-yellow-100 text-yellow-800',
      OVERDUE: 'bg-red-100 text-red-800',
      DISPUTED: 'bg-orange-100 text-orange-800',
      CANCELLED: 'bg-red-100 text-red-800',
   };
   return colors[status] || 'bg-gray-100 text-gray-800';
};

const formatStatus = (status: string) => {
   const key = `opportunities.invoiceStatuses.${status}` as const;
   return te(key) ? t(key) : status.replace(/_/g, ' ');
};

const formatCurrency = (value: number, currency: string = 'EUR') => {
   const amount = Number(value) || 0;
   const resolvedLocale = locale.value === 'fr' ? 'fr-FR' : 'en-US';
   return new Intl.NumberFormat(resolvedLocale, {
      style: 'currency',
      currency: currency,
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
   }).format(amount);
};

const formatDate = (dateString: string) => {
   if (!dateString) return '—';
   const date = new Date(dateString);
   const resolvedLocale = locale.value === 'fr' ? 'fr-FR' : 'en-US';
   return new Intl.DateTimeFormat(resolvedLocale, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
   }).format(date);
};

onMounted(() => {
   loadInvoice();
});
</script>
