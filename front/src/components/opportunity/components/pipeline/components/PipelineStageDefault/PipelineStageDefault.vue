<template>
   <div class="bg-white rounded-lg shadow p-6">
      <h3 class="text-lg font-semibold text-gray-900 mb-4">
         {{ t('opportunities.opportunityDetails') }}
      </h3>

      <div v-if="isLoading" class="text-center py-4 text-gray-500">
         {{ t('opportunities.loadingDots') }}
      </div>

      <div v-else class="space-y-4">
         <div>
            <div class="text-sm text-gray-600">{{ t('opportunities.estimatedAmount') }}</div>
            <div class="font-medium text-gray-900">
               {{
                  opportunity?.amount_estimated
                     ? `${opportunity.currency || 'EUR'} ${opportunity.amount_estimated.toLocaleString(resolvedLocale)}`
                     : '-'
               }}
            </div>
         </div>

         <div>
            <div class="text-sm text-gray-600">{{ t('opportunities.probability') }}</div>
            <div class="font-medium text-gray-900">{{ opportunity?.probability || 0 }}%</div>
         </div>

         <div>
            <div class="text-sm text-gray-600">{{ t('opportunities.expectedCloseDate') }}</div>
            <div class="font-medium text-gray-900">
               {{
                  opportunity?.expected_close_date
                     ? new Date(opportunity.expected_close_date).toLocaleDateString(
                          resolvedLocale,
                          {
                             month: 'short',
                             day: 'numeric',
                             year: 'numeric',
                          }
                       )
                     : '-'
               }}
            </div>
         </div>

         <div>
            <div class="text-sm text-gray-600">{{ t('opportunities.created') }}</div>
            <div class="font-medium text-gray-900">
               {{
                  opportunity?.created_at
                     ? new Date(opportunity.created_at).toLocaleString(resolvedLocale, {
                          month: 'short',
                          day: 'numeric',
                          year: 'numeric',
                          hour: 'numeric',
                          minute: 'numeric',
                       })
                     : '-'
               }}
            </div>
         </div>

         <div>
            <div class="text-sm text-gray-600">{{ t('opportunities.lastUpdated') }}</div>
            <div class="font-medium text-gray-900">
               {{
                  opportunity?.updated_at
                     ? new Date(opportunity.updated_at).toLocaleDateString(resolvedLocale, {
                          month: 'short',
                          day: 'numeric',
                          year: 'numeric',
                          hour: 'numeric',
                          minute: 'numeric',
                       })
                     : '-'
               }}
            </div>
         </div>
      </div>
   </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useI18n } from '../../../../../../i18n/useI18n';

const props = defineProps<{
   opportunity: any | null;
   account: any | null;
   contacts: any[];
   isLoading: boolean;
   stage?: string | null;
}>();

const { t, locale } = useI18n();
const resolvedLocale = computed(() => (locale.value === 'fr' ? 'fr-FR' : 'en-US'));
</script>
