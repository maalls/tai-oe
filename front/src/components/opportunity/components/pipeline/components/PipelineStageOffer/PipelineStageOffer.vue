<template>
   <div class="bg-white rounded-lg space-y-6">
      <div>
         <div class="text-sm text-gray-500">{{ t('opportunities.pipeline.stage') }}</div>
         <div class="text-lg font-semibold text-gray-900">
            {{
               stage === 'NEGOTIATION'
                  ? t('opportunities.pipeline.negotiationTitle')
                  : t('opportunities.pipeline.offerSentTitle')
            }}
         </div>
         <div class="text-sm text-gray-600">
            {{
               stage === 'NEGOTIATION'
                  ? t('opportunities.pipeline.negotiationDescription')
                  : t('opportunities.pipeline.offerSentDescription')
            }}
         </div>
      </div>

      <div class="border border-gray-200 rounded-lg p-4 bg-gray-50">
         <div class="text-sm font-medium text-gray-700 mb-3">
            {{ t('opportunities.pipeline.nextActions') }}
         </div>
         <ul class="text-sm text-gray-600 space-y-2">
            <template v-if="stage === 'NEGOTIATION'">
               <li>• {{ t('opportunities.pipeline.negotiationSteps.followUp') }}</li>
               <li>• {{ t('opportunities.pipeline.negotiationSteps.handleObjections') }}</li>
               <li>• {{ t('opportunities.pipeline.negotiationSteps.finalDecision') }}</li>
            </template>
            <template v-else>
               <li>• {{ t('opportunities.pipeline.offerSentSteps.confirmDelivery') }}</li>
               <li>• {{ t('opportunities.pipeline.offerSentSteps.awaitResponse') }}</li>
               <li>• {{ t('opportunities.pipeline.offerSentSteps.planNext') }}</li>
            </template>
         </ul>
         <div v-if="stage === 'NEGOTIATION'" class="mt-4">
            <button
               type="button"
               @click="goToQuotePage"
               class="px-3 py-2 rounded-lg bg-blue-600 text-white text-sm font-medium hover:bg-blue-700"
            >
               {{ t('opportunities.pipeline.negotiationEditQuote') }}
            </button>
         </div>
      </div>

      <div>
         <div class="text-sm text-gray-600">{{ t('opportunities.pipeline.expectedClose') }}</div>
         <div class="font-medium text-gray-900">
            {{ opportunity?.expected_close_date || '-' }}
         </div>
      </div>
   </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router';
import { useI18n } from '../../../../../../i18n/useI18n';

const props = defineProps<{
   opportunity: any | null;
   account: any | null;
   contacts: any[];
   isLoading: boolean;
   stage?: string | null;
}>();

const { t } = useI18n();
const router = useRouter();

const goToQuotePage = () => {
   if (props.opportunity?.id) {
      router.push(`/opportunities/${props.opportunity.id}/quote`);
   }
};
</script>
