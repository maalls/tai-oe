<template>
   <div class="bg-white rounded-lg space-y-6">
      <div>
         <div class="text-sm text-gray-500">{{ t('opportunities.pipeline.stage') }}</div>
         <div class="text-lg font-semibold text-gray-900">
            {{ t('opportunities.pipeline.deliveryTitle') }}
         </div>
         <div class="text-sm text-gray-600">
            {{ t('opportunities.pipeline.deliveryDescription') }}
         </div>
      </div>

      <div class="border border-gray-200 rounded-lg p-4 bg-amber-50">
         <div class="text-sm font-medium text-amber-900 mb-3">
            {{ t('opportunities.pipeline.deliveryChecklistTitle') }}
         </div>
         <ul class="text-sm text-amber-800 space-y-2">
            <li>• {{ t('opportunities.pipeline.deliverySteps.trackShipment') }}</li>
            <li>• {{ t('opportunities.pipeline.deliverySteps.confirmLogistics') }}</li>
            <li>• {{ t('opportunities.pipeline.deliverySteps.notifyCustomer') }}</li>
            <li>• {{ t('opportunities.pipeline.deliverySteps.resolveIssues') }}</li>
         </ul>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
         <div>
            <div class="text-sm text-gray-600">{{ t('opportunities.pipeline.expectedClose') }}</div>
            <div class="font-medium text-gray-900">
               {{ opportunity?.expected_close_date || '-' }}
            </div>
         </div>
      </div>

      <div v-if="opportunity?.notes" class="border-t pt-4">
         <div class="text-sm text-gray-600 mb-2">{{ t('opportunities.pipeline.notes') }}</div>
         <div class="text-sm text-gray-900 bg-gray-50 rounded p-3">
            {{ opportunity.notes }}
         </div>
      </div>
   </div>
</template>

<script setup lang="ts">
import { useI18n } from '../../../../../../i18n/useI18n';

const props = defineProps<{
   opportunity: any | null;
   account: any | null;
   contacts: any[];
   isLoading: boolean;
   stage?: string | null;
}>();

const { t } = useI18n();
</script>
