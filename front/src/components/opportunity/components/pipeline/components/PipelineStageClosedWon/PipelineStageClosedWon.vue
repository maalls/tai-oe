<template>
   <div class="bg-white rounded-lg shadow p-6 space-y-6">
      <div
         class="bg-gradient-to-r from-green-50 to-emerald-50 rounded-lg p-6 border border-green-200"
      >
         <div class="flex items-center gap-3 mb-2">
            <svg
               class="w-8 h-8 text-green-600"
               fill="none"
               stroke="currentColor"
               viewBox="0 0 24 24"
            >
               <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
               />
            </svg>
            <div>
               <div class="text-sm text-green-700">{{ t('opportunities.pipeline.stage') }}</div>
               <div class="text-xl font-bold text-green-900">
                  {{ t('opportunities.pipeline.closedWonTitle') }}
               </div>
            </div>
         </div>
         <div class="text-sm text-green-700 mt-3">
            {{ t('opportunities.pipeline.closedWonDescription') }}
         </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
         <div class="border border-gray-200 rounded-lg p-4 bg-blue-50">
            <div class="text-sm text-blue-700 mb-1">
               {{ t('opportunities.pipeline.closedWonOpportunityValue') }}
            </div>
            <div class="text-2xl font-bold text-blue-900">
               {{
                  formatCurrency(
                     invoice?.total_incl_tax || opportunity?.amount_estimated || 0,
                     invoice?.currency || opportunity?.currency || 'EUR'
                  )
               }}
            </div>
         </div>
         <div class="border border-gray-200 rounded-lg p-4 bg-purple-50">
            <div class="text-sm text-purple-700 mb-1">
               {{ t('opportunities.pipeline.closedWonDuration') }}
            </div>
            <div class="text-2xl font-bold text-purple-900">
               {{ calculateDuration() }}
            </div>
         </div>
         <div class="border border-gray-200 rounded-lg p-4 bg-green-50">
            <div class="text-sm text-green-700 mb-1">
               {{ t('opportunities.pipeline.closedWonStatus') }}
            </div>
            <div class="text-2xl font-bold text-green-900">
               {{ t('opportunities.pipeline.paidStatus') }}
            </div>
         </div>
      </div>

      <div class="border border-gray-200 rounded-lg p-4">
         <div class="text-sm font-medium text-gray-700 mb-3">
            {{ t('opportunities.pipeline.closedWonSummaryTitle') }}
         </div>
         <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
               <div class="text-sm text-gray-600">
                  {{ t('opportunities.pipeline.closedWonCreatedDate') }}
               </div>
               <div class="font-medium text-gray-900">
                  {{ formatDate(opportunity?.created_at) }}
               </div>
            </div>
            <div>
               <div class="text-sm text-gray-600">
                  {{ t('opportunities.pipeline.closedWonClosedDate') }}
               </div>
               <div class="font-medium text-gray-900">
                  {{ formatDate(opportunity?.updated_at) }}
               </div>
            </div>
         </div>
      </div>

      <div v-if="invoice" class="border border-gray-200 rounded-lg p-4">
         <div class="text-sm font-medium text-gray-700 mb-3">
            {{ t('opportunities.pipeline.closedWonFinalInvoice') }}
         </div>
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
                  {{ t('opportunities.pipeline.paymentStatusLabel') }}
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
                  {{ t('opportunities.pipeline.amountLabel') }}
               </div>
               <div class="font-semibold text-gray-900">
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

         <div class="mt-4 pt-4 border-t">
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

      <div class="border border-gray-200 rounded-lg p-4 bg-gray-50">
         <div class="text-sm font-medium text-gray-700 mb-3">
            {{ t('opportunities.pipeline.closedWonNextStepsTitle') }}
         </div>
         <ul class="text-sm text-gray-600 space-y-2">
            <li>• {{ t('opportunities.pipeline.closedWonNextSteps.archiveDocs') }}</li>
            <li>• {{ t('opportunities.pipeline.closedWonNextSteps.requestFeedback') }}</li>
            <li>• {{ t('opportunities.pipeline.closedWonNextSteps.identifyUpsell') }}</li>
            <li>• {{ t('opportunities.pipeline.closedWonNextSteps.scheduleFollowUp') }}</li>
            <li>• {{ t('opportunities.pipeline.closedWonNextSteps.updateMetrics') }}</li>
         </ul>
      </div>
   </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import { useRouter } from 'vue-router';
import { listOpportunityDocuments, type OpportunityDocument } from '../../../../../../api/document';
import { useI18n } from '../../../../../../i18n/useI18n';

const props = defineProps<{
   opportunity: any | null;
   account: any | null;
   contacts: any[];
   isLoading: boolean;
   stage?: string | null;
}>();

const router = useRouter();
const invoice = ref<OpportunityDocument | null>(null);
const { t } = useI18n();

const loadInvoice = async () => {
   if (!props.opportunity?.id) return;

   try {
      const documents = await listOpportunityDocuments(props.opportunity.id);
      const latestInvoice = documents
         .filter((document) => document.type === 'INVOICE')
         .sort((left, right) => {
            const leftTime = left.created_at ? new Date(left.created_at).getTime() : 0;
            const rightTime = right.created_at ? new Date(right.created_at).getTime() : 0;
            return rightTime - leftTime;
         })[0];

      invoice.value = latestInvoice ?? null;
   } catch (error) {
      console.error('[PipelineStageClosedWon] Unexpected error loading invoice:', error);
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

const calculateDuration = () => {
   if (!props.opportunity?.created_at || !props.opportunity?.updated_at) return '-';

   const start = new Date(props.opportunity.created_at);
   const end = new Date(props.opportunity.updated_at);
   const diffTime = Math.abs(end.getTime() - start.getTime());
   const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

   if (diffDays < 7) return `${diffDays} days`;
   if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks`;
   if (diffDays < 365) return `${Math.floor(diffDays / 30)} months`;
   return `${Math.floor(diffDays / 365)} years`;
};

const viewInvoice = () => {
   if (invoice.value?.id && props.opportunity?.id) {
      router.push(`/opportunities/${props.opportunity.id}/invoices/${invoice.value.id}`);
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
