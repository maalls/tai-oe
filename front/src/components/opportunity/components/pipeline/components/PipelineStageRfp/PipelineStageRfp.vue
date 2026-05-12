<template>
   <div class="bg-white space-y-6">
      <div>
         <div class="text-sm text-gray-500">{{ t('opportunities.pipeline.stage') }}</div>
         <div class="text-lg font-semibold text-gray-900">
            {{
               stage === 'RFQ_IN_PROGRESS'
                  ? t('opportunities.pipeline.rfqInProgress')
                  : t('opportunities.pipeline.rfpRfqInProgress')
            }}
         </div>
         <div class="text-sm text-gray-600">
            {{
               stage === 'RFQ_IN_PROGRESS'
                  ? t('opportunities.pipeline.rfqDescription')
                  : t('opportunities.pipeline.rfpDescription')
            }}
         </div>
      </div>

      <div class="border border-gray-200 rounded-lg p-4 bg-gray-50">
         <div class="text-sm font-medium text-gray-700 mb-3">
            {{
               stage === 'RFQ_IN_PROGRESS'
                  ? t('opportunities.pipeline.nextSteps')
                  : t('opportunities.pipeline.checklist')
            }}
         </div>
         <ul class="text-sm text-gray-600 space-y-2">
            <template v-if="stage === 'RFQ_IN_PROGRESS'">
               <li>• {{ t('opportunities.pipeline.rfqSteps.reviewRequirements') }}</li>
               <li>• {{ t('opportunities.pipeline.rfqSteps.defineLineItems') }}</li>
               <li>• {{ t('opportunities.pipeline.rfqSteps.generateQuote') }}</li>
               <li>• {{ t('opportunities.pipeline.rfqSteps.sendQuote') }}</li>
            </template>
            <template v-else>
               <li>• {{ t('opportunities.pipeline.rfpSteps.confirmScope') }}</li>
               <li>• {{ t('opportunities.pipeline.rfpSteps.validateConstraints') }}</li>
               <li>• {{ t('opportunities.pipeline.rfpSteps.identifyStakeholders') }}</li>
            </template>
         </ul>
      </div>

      <div v-if="stage === 'RFQ_IN_PROGRESS'" class="border border-gray-200 rounded-lg p-4">
         <div class="text-sm font-medium text-gray-700 mb-3">
            {{ t('opportunities.pipeline.quoteGenerationTitle') }}
         </div>
         <div class="text-sm text-gray-600 mb-4">
            {{ t('opportunities.pipeline.quoteGenerationDescription') }}
         </div>

         <div v-if="quoteMessage" class="mb-3 p-3 bg-green-50 text-green-700 text-sm rounded">
            {{ quoteMessage }}
         </div>
         <div v-if="quoteError" class="mb-3 p-3 bg-red-50 text-red-700 text-sm rounded">
            {{ quoteError }}
         </div>

         <div v-if="hasExistingQuote" class="mb-4 flex items-center gap-2 text-sm">
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
            <span class="text-gray-700">{{ t('opportunities.pipeline.quoteExists') }}</span>
         </div>

         <div class="flex gap-2">
            <button
               type="button"
               @click="goToQuotePage"
               class="px-3 py-2 rounded-lg bg-blue-600 text-white text-sm font-medium hover:bg-blue-700"
            >
               {{
                  hasExistingQuote
                     ? t('opportunities.pipeline.editQuote')
                     : t('opportunities.pipeline.createQuote')
               }}
            </button>
            <button
               v-if="hasExistingQuote"
               type="button"
               @click="generateQuotePdf"
               :disabled="isGeneratingPdf"
               class="px-3 py-2 rounded-lg bg-green-600 text-white text-sm font-medium hover:bg-green-700 disabled:bg-gray-400"
            >
               {{
                  isGeneratingPdf
                     ? t('opportunities.pipeline.generatingPdf')
                     : t('opportunities.pipeline.generatePdf')
               }}
            </button>
         </div>
      </div>
   </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import { useRouter } from 'vue-router';
import { supabase } from '../../../../../../lib/supabase';
import { useAuth } from '../../../../../../stores/auth';
import { useI18n } from '../../../../../../i18n/useI18n';

const props = defineProps<{
   opportunity: any | null;
   account: any | null;
   contacts: any[];
   isLoading: boolean;
   stage?: string | null;
}>();

const router = useRouter();
const { t } = useI18n();
const { getValidToken } = useAuth();
const isGeneratingPdf = ref(false);
const hasExistingQuote = ref(false);
const quoteMessage = ref('');
const quoteError = ref('');

const checkExistingQuote = async () => {
   if (!props.opportunity?.id) return;

   try {
      const { data, error } = await supabase
         .from('document')
         .select('id')
         .eq('opportunity_id', props.opportunity.id)
         .eq('type', 'QUOTE')
         .limit(1);

      if (error) {
         console.error('[PipelineStageRfp] Error checking quote:', error);
         return;
      }

      hasExistingQuote.value = !!(data && data.length > 0);
   } catch (error) {
      console.error('[PipelineStageRfp] Unexpected error checking quote:', error);
   }
};

const goToQuotePage = () => {
   if (props.opportunity?.id) {
      router.push(`/opportunities/${props.opportunity.id}/quote`);
   }
};

const generateQuotePdf = async () => {
   if (!props.opportunity?.id) return;

   isGeneratingPdf.value = true;
   quoteError.value = '';
   quoteMessage.value = '';

   try {
      const token = await getValidToken();
      const response = await fetch(
         `/api/quote/${props.opportunity.id}/generate`,
         {
            method: 'POST',
            headers: {
               Authorization: `Bearer ${token}`,
            },
         }
      );

      const result = await response.json();
      if (!response.ok) {
         throw new Error(result?.message || t('opportunities.pipeline.failedGeneratePdf'));
      }

      quoteMessage.value = t('opportunities.pipeline.generatedPdf');
      setTimeout(() => {
         quoteMessage.value = '';
      }, 4000);
   } catch (error: any) {
      quoteError.value = error?.message || t('opportunities.pipeline.failedGeneratePdf');
   } finally {
      isGeneratingPdf.value = false;
   }
};

onMounted(() => {
   if (props.stage === 'RFQ_IN_PROGRESS') {
      checkExistingQuote();
   }
});

watch(
   () => [props.opportunity?.id, props.stage],
   () => {
      if (props.stage === 'RFQ_IN_PROGRESS') {
         checkExistingQuote();
      }
   }
);
</script>
