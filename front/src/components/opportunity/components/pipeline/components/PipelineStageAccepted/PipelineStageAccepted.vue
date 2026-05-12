<template>
   <div class="bg-white rounded-lg shadow p-6 space-y-6">
      <div>
         <div class="text-sm text-gray-500">{{ t('opportunities.pipeline.stage') }}</div>
         <div class="text-lg font-semibold text-gray-900">
            {{ t('opportunities.pipeline.acceptedTitle') }}
         </div>
         <div class="text-sm text-gray-600">
            {{ t('opportunities.pipeline.acceptedDescription') }}
         </div>
      </div>

      <div class="border border-gray-200 rounded-lg p-4 bg-gray-50">
         <div class="text-sm font-medium text-gray-700 mb-3">
            {{ t('opportunities.pipeline.acceptedFocusTitle') }}
         </div>
         <ul class="text-sm text-gray-600 space-y-2">
            <li>• {{ t('opportunities.pipeline.acceptedFocusSteps.confirmDocs') }}</li>
            <li>• {{ t('opportunities.pipeline.acceptedFocusSteps.issueFinalInvoice') }}</li>
            <li>• {{ t('opportunities.pipeline.acceptedFocusSteps.captureFeedback') }}</li>
         </ul>
      </div>

      <div class="border border-gray-200 rounded-lg p-4">
         <div class="text-sm font-medium text-gray-700 mb-3">
            {{ t('opportunities.pipeline.acceptedInvoiceTitle') }}
         </div>
         <div class="text-sm text-gray-600 mb-4">
            {{ t('opportunities.pipeline.acceptedInvoiceDescription') }}
         </div>

         <div v-if="invoiceMessage" class="mb-3 p-3 bg-green-50 text-green-700 text-sm rounded">
            {{ invoiceMessage }}
         </div>
         <div v-if="invoiceError" class="mb-3 p-3 bg-red-50 text-red-700 text-sm rounded">
            {{ invoiceError }}
         </div>

         <!-- Status indicators -->
         <div v-if="hasExistingInvoice" class="mb-4 space-y-2">
            <div class="flex items-center gap-2 text-sm">
               <svg
                  class="w-5 h-5 text-green-600"
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
               <span class="text-gray-700">
                  {{ t('opportunities.pipeline.acceptedInvoiceGenerated') }}
               </span>
            </div>
            <div v-if="invoiceIsSent" class="flex items-center gap-2 text-sm">
               <svg
                  class="w-5 h-5 text-green-600"
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
               <span class="text-gray-700">
                  {{ t('opportunities.pipeline.acceptedInvoiceSent') }}
               </span>
            </div>
         </div>

         <div class="flex flex-wrap gap-2">
            <button
               v-if="!hasExistingInvoice"
               type="button"
               @click="generateInvoice"
               :disabled="isGeneratingInvoice"
               class="px-3 py-2 rounded-lg bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 disabled:bg-gray-400"
            >
               {{
                  isGeneratingInvoice
                     ? t('opportunities.pipeline.acceptedGenerating')
                     : t('opportunities.pipeline.acceptedGenerateInvoice')
               }}
            </button>
            <button
               v-if="hasExistingInvoice"
               type="button"
               @click="viewOrSendInvoice"
               :class="[
                  'px-3 py-2 rounded-lg text-white text-sm font-medium',
                  invoiceIsSent
                     ? 'bg-green-600 hover:bg-green-700'
                     : 'bg-gray-900 hover:bg-gray-800',
               ]"
            >
               {{
                  invoiceIsSent
                     ? t('opportunities.pipeline.acceptedSeeInvoice')
                     : t('opportunities.pipeline.acceptedSendInvoice')
               }}
            </button>
         </div>
      </div>
   </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import { useRouter } from 'vue-router';
import { useAuth } from '../../../../../../stores/auth';
import { supabase } from '../../../../../../lib/supabase';
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

const { getValidToken } = useAuth();
const router = useRouter();
const { t } = useI18n();
const isGeneratingInvoice = ref(false);
const hasExistingInvoice = ref(false);
const invoiceIsSent = ref(false);
const existingInvoiceId = ref<string | null>(null);
const invoiceMessage = ref('');
const invoiceError = ref('');

const loadExistingInvoice = async () => {
   if (!props.opportunity?.id) {
      hasExistingInvoice.value = false;
      return;
   }

   try {
      const { data, error } = await supabase
         .from('document')
         .select('id, status')
         .eq('opportunity_id', props.opportunity.id)
         .eq('type', 'INVOICE')
         .limit(1);

      if (error) {
         console.error('[PipelineStageAccepted] Error checking invoices:', error);
         return;
      }

      hasExistingInvoice.value = !!(data && data.length > 0);
      if (data && data.length > 0) {
         const invoice = data[0] as any;
         existingInvoiceId.value = invoice?.id || null;
         invoiceIsSent.value = invoice?.status === 'SENT';
      } else {
         existingInvoiceId.value = null;
         invoiceIsSent.value = false;
      }
   } catch (error) {
      console.error('[PipelineStageAccepted] Unexpected error checking invoices:', error);
   }
};

const buildAuthHeaders = async (includeContent = false) => {
   const token = await getValidToken();
   const headers: Record<string, string> = {
      Authorization: `Bearer ${token}`,
   };
   if (includeContent) {
      headers['Content-Type'] = 'application/json';
   }
   return headers;
};

const generateInvoice = async () => {
   if (!props.opportunity?.id) return;

   isGeneratingInvoice.value = true;
   invoiceError.value = '';
   invoiceMessage.value = '';

   try {
      const headers = await buildAuthHeaders();

      const response = await fetch(`/api/quote/${props.opportunity.id}/invoice`, {
         method: 'POST',
         headers,
      });

      const result = await response.json();
      if (!response.ok) {
         throw new Error(result?.message || t('opportunities.errors.failedToGenerateInvoice'));
      }

      invoiceMessage.value = t('opportunities.pipeline.messages.invoiceCreatedSuccess', {
         reference: result.invoice.external_ref,
      });
      hasExistingInvoice.value = true;
      existingInvoiceId.value = result.invoice.id;

      // Update opportunity stage to INVOICED
      await (supabase.from('opportunity') as any)
         .update({ stage: 'INVOICED' })
         .eq('id', props.opportunity.id);

      // Emit stage update event
      emit('stageUpdated', 'INVOICED', 'OPEN');

      setTimeout(() => {
         invoiceMessage.value = '';
      }, 4000);
   } catch (error: any) {
      invoiceError.value = error?.message || t('opportunities.errors.failedToGenerateInvoice');
   } finally {
      isGeneratingInvoice.value = false;
   }
};

onMounted(() => {
   loadExistingInvoice();
});

watch(
   () => props.opportunity?.id,
   () => {
      loadExistingInvoice();
   }
);

const viewOrSendInvoice = async () => {
   if (!props.opportunity?.id) return;

   if (invoiceIsSent.value && existingInvoiceId.value) {
      // Navigate directly to invoice detail page
      router.push(`/opportunities/${props.opportunity.id}/invoices/${existingInvoiceId.value}`);
   } else {
      // Navigate to invoices list
      router.push(`/opportunities/${props.opportunity.id}/invoices`);
   }
};
</script>
