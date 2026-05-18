<template>
   <div class="bg-white rounded-lg shadow p-6 space-y-6">
      <div>
         <div class="text-sm text-gray-500">{{ t('opportunities.pipeline.stage') }}</div>
         <div class="text-lg font-semibold text-gray-900">
            {{ t('opportunities.pipeline.paidTitle') }}
         </div>
         <div class="text-sm text-gray-600">
            {{ t('opportunities.pipeline.paidDescription') }}
         </div>
      </div>

      <div class="border border-gray-200 rounded-lg p-4 bg-green-50">
         <div class="text-sm font-medium text-gray-700 mb-3">
            {{ t('opportunities.pipeline.paidFocusTitle') }}
         </div>
         <ul class="text-sm text-gray-600 space-y-2">
            <li>• {{ t('opportunities.pipeline.paidFocusSteps.confirmPayment') }}</li>
            <li>• {{ t('opportunities.pipeline.paidFocusSteps.updateAccounting') }}</li>
            <li>• {{ t('opportunities.pipeline.paidFocusSteps.closeWon') }}</li>
            <li>• {{ t('opportunities.pipeline.paidFocusSteps.documentLessons') }}</li>
         </ul>
      </div>

      <div class="border border-gray-200 rounded-lg p-4">
         <div class="text-sm font-medium text-gray-700 mb-3">
            {{ t('opportunities.pipeline.paymentSummaryTitle') }}
         </div>

         <div v-if="isLoadingInvoice" class="text-sm text-gray-500">
            {{ t('opportunities.pipeline.loadingPaymentDetails') }}
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
                        class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800"
                     >
                        <svg
                           class="w-4 h-4 mr-1"
                           fill="none"
                           stroke="currentColor"
                           viewBox="0 0 24 24"
                        >
                           <path
                              stroke-linecap="round"
                              stroke-linejoin="round"
                              stroke-width="2"
                              d="M5 13l4 4L19 7"
                           />
                        </svg>
                        {{ t('opportunities.pipeline.paidStatus') }}
                     </span>
                  </div>
               </div>
               <div>
                  <div class="text-sm text-gray-600">
                     {{ t('opportunities.pipeline.amountPaidLabel') }}
                  </div>
                  <div class="font-semibold text-green-700 text-lg">
                     {{ formatCurrency(invoice.total_incl_tax, invoice.currency) }}
                  </div>
               </div>
               <div>
                  <div class="text-sm text-gray-600">
                     {{ t('opportunities.pipeline.paymentDateLabel') }}
                  </div>
                  <div class="font-medium text-gray-900">{{ formatDate(invoice.updated_at) }}</div>
               </div>
            </div>

            <div class="pt-4 border-t">
               <button
                  v-if="invoice.storage_key"
                  type="button"
                  @click="viewInvoice"
                  class="px-3 py-2 rounded-lg bg-blue-600 text-white text-sm font-medium hover:bg-blue-700"
               >
                  {{ t('opportunities.pipeline.viewInvoice') }}
               </button>
            </div>
         </div>

         <div v-else class="text-sm text-gray-500">
            {{ t('opportunities.pipeline.noInvoiceFoundShort') }}
         </div>
      </div>

      <div class="border border-gray-200 rounded-lg p-4 bg-blue-50">
         <div class="text-sm font-medium text-gray-700 mb-3">
            {{ t('opportunities.pipeline.closeOpportunityTitle') }}
         </div>
         <div class="text-sm text-gray-600 mb-4">
            {{ t('opportunities.pipeline.closeOpportunityDescription') }}
         </div>

         <div v-if="closeMessage" class="mb-3 p-3 bg-green-50 text-green-700 text-sm rounded">
            {{ closeMessage }}
         </div>
         <div v-if="closeError" class="mb-3 p-3 bg-red-50 text-red-700 text-sm rounded">
            {{ closeError }}
         </div>

         <button
            type="button"
            @click="closeAsWon"
            :disabled="isClosing"
            class="px-4 py-2 rounded-lg bg-green-600 text-white text-sm font-medium hover:bg-green-700 disabled:bg-gray-400"
         >
            {{
               isClosing
                  ? t('opportunities.pipeline.closing')
                  : t('opportunities.pipeline.closeAsWon')
            }}
         </button>
      </div>

      <div v-if="opportunity" class="border border-gray-200 rounded-lg p-4 bg-gray-50">
         <div class="text-sm font-medium text-gray-700 mb-3">
            {{ t('opportunities.pipeline.opportunityTimelineTitle') }}
         </div>
         <div class="grid grid-cols-2 gap-4 text-sm">
            <div>
               <div class="text-gray-600">{{ t('opportunities.pipeline.createdLabel') }}</div>
               <div class="text-gray-900">{{ formatDate(opportunity.created_at) }}</div>
            </div>
            <div>
               <div class="text-gray-600">{{ t('opportunities.pipeline.lastUpdatedLabel') }}</div>
               <div class="text-gray-900">{{ formatDate(opportunity.updated_at) }}</div>
            </div>
         </div>
      </div>
   </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import { useRouter } from 'vue-router';
import { listOpportunityDocuments } from '../../../../../../api/document';
import { advanceOpportunityStage } from '../../../../../../api/opportunity';
import { useI18n } from '../../../../../../i18n/useI18n';

const props = defineProps<{
   opportunity: any | null;
   account: any | null;
   contacts: any[];
   isLoading: boolean;
   stage?: string | null;
}>();

const emit = defineEmits<{
   (e: 'stageUpdated', stage: string, status: string): void;
}>();

const router = useRouter();
const { t } = useI18n();
const isLoadingInvoice = ref(true);
const isClosing = ref(false);
const invoice = ref<any | null>(null);
const closeMessage = ref('');
const closeError = ref('');

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
      console.error('[PipelineStagePaid] Unexpected error loading invoice:', error);
   } finally {
      isLoadingInvoice.value = false;
   }
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

const closeAsWon = async () => {
   if (!props.opportunity?.id) return;

   isClosing.value = true;
   closeError.value = '';
   closeMessage.value = '';

   try {
      await advanceOpportunityStage(props.opportunity.id, 'CLOSED_WON');

      closeMessage.value = t('opportunities.pipeline.messages.closedWonSuccess');

      // Emit event to update parent
      emit('stageUpdated', 'CLOSED_WON', 'WON');
   } catch (error: any) {
      closeError.value = error?.message || t('opportunities.errors.failedToCloseOpportunity');
      console.error('[PipelineStagePaid] Error closing opportunity:', error);
   } finally {
      isClosing.value = false;
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
