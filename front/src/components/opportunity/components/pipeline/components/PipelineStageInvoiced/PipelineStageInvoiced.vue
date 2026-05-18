<template>
   <div class="bg-white rounded-lg shadow p-6 space-y-6">
      <div>
         <div class="text-sm text-gray-500">{{ t('opportunities.pipeline.stage') }}</div>
         <div class="text-lg font-semibold text-gray-900">
            {{ t('opportunities.pipeline.invoicedTitle') }}
         </div>
         <div class="text-sm text-gray-600">
            {{ t('opportunities.pipeline.invoicedDescription') }}
         </div>
      </div>

      <div class="border border-gray-200 rounded-lg p-4 bg-gray-50">
         <div class="text-sm font-medium text-gray-700 mb-3">
            {{ t('opportunities.pipeline.invoicedFocusTitle') }}
         </div>
         <ul class="text-sm text-gray-600 space-y-2">
            <li>• {{ t('opportunities.pipeline.invoicedFocusSteps.trackPayment') }}</li>
            <li>• {{ t('opportunities.pipeline.invoicedFocusSteps.monitorDueDate') }}</li>
            <li>• {{ t('opportunities.pipeline.invoicedFocusSteps.processPayment') }}</li>
            <li>• {{ t('opportunities.pipeline.invoicedFocusSteps.updateAccounting') }}</li>
         </ul>
      </div>

      <div class="border border-gray-200 rounded-lg p-4">
         <div class="text-sm font-medium text-gray-700 mb-3">
            {{ t('opportunities.pipeline.invoiceDetailsTitle') }}
         </div>

         <div v-if="isLoadingInvoice" class="text-sm text-gray-500">
            {{ t('opportunities.pipeline.loadingInvoice') }}
         </div>

         <div v-else-if="invoice" class="space-y-4">
            <div class="grid grid-cols-2 gap-4">
               <div>
                  <div class="text-sm text-gray-600">
                     {{ t('opportunities.pipeline.invoiceNumberLabel') }}
                  </div>
                  <div class="font-medium text-gray-900">
                     {{ invoice.external_ref || invoice.title || '-' }}
                  </div>
               </div>
               <div>
                  <div class="text-sm text-gray-600">
                     {{ t('opportunities.pipeline.statusLabel') }}
                  </div>
                  <div>
                     <span
                        class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
                        :class="getStatusColor(invoice.status)"
                     >
                        {{ invoice.status }}
                     </span>
                  </div>
               </div>
               <div>
                  <div class="text-sm text-gray-600">
                     {{ t('opportunities.pipeline.amountLabel') }}
                  </div>
                  <div class="font-medium text-gray-900">
                     {{ formatCurrency(invoice.total_incl_tax, invoice.currency) }}
                  </div>
               </div>
               <div>
                  <div class="text-sm text-gray-600">
                     {{ t('opportunities.pipeline.issuedDateLabel') }}
                  </div>
                  <div class="font-medium text-gray-900">
                     {{ formatDate(invoice.issued_at || invoice.created_at) }}
                  </div>
               </div>
               <div v-if="invoice.status === 'SENT' && invoice.updated_at">
                  <div class="text-sm text-gray-600">
                     {{ t('opportunities.pipeline.sentDateLabel') }}
                  </div>
                  <div class="font-medium text-gray-900">
                     {{ formatDate(invoice.updated_at) }}
                  </div>
               </div>
            </div>

            <div class="pt-4 border-t flex gap-2">
               <button
                  v-if="invoice.storage_key"
                  type="button"
                  @click="viewInvoice"
                  class="px-3 py-2 rounded-lg bg-blue-600 text-white text-sm font-medium hover:bg-blue-700"
               >
                  {{ t('opportunities.pipeline.viewInvoice') }}
               </button>
               <button
                  type="button"
                  @click="markAsPaid"
                  :disabled="isUpdating || invoice.status === 'PAID'"
                  class="px-3 py-2 rounded-lg bg-green-600 text-white text-sm font-medium hover:bg-green-700 disabled:bg-gray-400"
               >
                  {{
                     isUpdating
                        ? t('opportunities.pipeline.updating')
                        : t('opportunities.pipeline.markAsPaid')
                  }}
               </button>
            </div>
         </div>

         <div v-else class="text-sm text-gray-500">
            {{ t('opportunities.pipeline.noInvoiceFound') }}
         </div>
      </div>

      <div v-if="paymentMessage" class="p-3 bg-green-50 text-green-700 text-sm rounded">
         {{ paymentMessage }}
      </div>
      <div v-if="paymentError" class="p-3 bg-red-50 text-red-700 text-sm rounded">
         {{ paymentError }}
      </div>
   </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import { useRouter } from 'vue-router';
import { useAuth } from '../../../../../../stores/auth';
import { listOpportunityDocuments, updateDocumentStatus } from '../../../../../../api/document';
import { advanceOpportunityStage } from '../../../../../../api/opportunity';
import { useI18n } from '../../../../../../i18n/useI18n';

const props = defineProps<{
   opportunity: any | null;
   account: any | null;
   contacts: any[];
   isLoading: boolean;
   stage?: string | null;
}>();

const router = useRouter();
const { getValidToken } = useAuth();
const { t } = useI18n();
const isLoadingInvoice = ref(true);
const isUpdating = ref(false);
const invoice = ref<any | null>(null);
const paymentMessage = ref('');
const paymentError = ref('');

const loadInvoice = async () => {
   if (!props.opportunity?.id) {
      isLoadingInvoice.value = false;
      return;
   }

   try {
      isLoadingInvoice.value = true;
      const documents = await listOpportunityDocuments(props.opportunity.id);
      const invoices = documents.filter((document) => document.type === 'INVOICE');
      invoice.value = invoices.length > 0 ? (invoices[0] as any) : null;
   } catch (error) {
      console.error('[PipelineStageInvoiced] Unexpected error loading invoice:', error);
   } finally {
      isLoadingInvoice.value = false;
   }
};

const getStatusColor = (status: string) => {
   const colors: Record<string, string> = {
      SENT: 'bg-blue-100 text-blue-800',
      PAID: 'bg-green-100 text-green-800',
      PARTIALLY_PAID: 'bg-yellow-100 text-yellow-800',
      OVERDUE: 'bg-red-100 text-red-800',
      DISPUTED: 'bg-orange-100 text-orange-800',
   };
   return colors[status] || 'bg-gray-100 text-gray-800';
};

const formatCurrency = (value: number, currency: string = 'EUR') => {
   const amount = Number(value) || 0;
   return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
   }).format(amount);
};

const formatDate = (dateString: string) => {
   if (!dateString) return '-';
   const date = new Date(dateString);
   return new Intl.DateTimeFormat('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
   }).format(date);
};

const viewInvoice = () => {
   if (invoice.value?.id && props.opportunity?.id) {
      router.push(`/opportunities/${props.opportunity.id}/invoices/${invoice.value.id}`);
   }
};

const markAsPaid = async () => {
   if (!invoice.value?.id) return;

   isUpdating.value = true;
   paymentError.value = '';
   paymentMessage.value = '';

   try {
      const token = await getValidToken();
      if (!token) throw new Error('Unauthorized');

      await updateDocumentStatus(invoice.value.id, 'PAID', token);

      invoice.value.status = 'PAID';
      paymentMessage.value = t('opportunities.pipeline.messages.invoiceMarkedPaidSuccess');

      // Optionally update opportunity stage to PAID
      if (props.opportunity?.id) {
         await advanceOpportunityStage(props.opportunity.id, 'PAID');
      }
   } catch (error: any) {
      paymentError.value = error?.message || t('opportunities.errors.failedToUpdateInvoiceStatus');
      console.error('[PipelineStageInvoiced] Error marking as paid:', error);
   } finally {
      isUpdating.value = false;
   }
};

onMounted(() => {
   loadInvoice();
});

watch(
   () => props.opportunity?.id,
   () => {
      loadInvoice();
   }
);
</script>
