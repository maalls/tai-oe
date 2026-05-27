<template>
   <div class="opportunity-page">
      <!-- Opportunity Header with Tabs -->
      <OpportunityHeader :opportunityId="opportunityId" activeTab="settings" />

      <!-- Error Message -->
      <div v-if="errorMessage" class="mb-4 p-4 bg-red-100 text-red-700 rounded-lg">
         {{ errorMessage }}
      </div>

      <!-- Success Message -->
      <div v-if="successMessage" class="mb-4 p-4 bg-green-100 text-green-700 rounded-lg">
         {{ successMessage }}
      </div>

      <!-- Loading State -->
      <div v-if="isLoading" class="flex justify-center items-center py-12">
         <div class="text-gray-500">{{ t('opportunities.loadingDots') }}</div>
      </div>

      <!-- Settings Content -->
      <div v-else class="opportunity-page-section m-4 space-y-6">
         <!-- Danger Zone -->
         <div v-if="!isNewOpportunity" class="bg-white rounded-lg shadow p-6">
            <h2 class="text-lg font-semibold text-gray-900 mb-4">
               {{ t('opportunities.dangerZone') }}
            </h2>

            <div class="border border-red-300 rounded-lg p-4 bg-red-50">
               <div class="flex items-start justify-between">
                  <div class="flex-1">
                     <h3 class="text-sm font-semibold text-red-900 mb-1">
                        {{ t('opportunities.deleteThisOpportunity') }}
                     </h3>
                     <p class="text-sm text-red-700">
                        {{ t('opportunities.deleteOpportunityDescription') }}
                     </p>
                  </div>
                  <ActionButton
                     type="button"
                     variant="danger"
                     class="ml-4"
                     @click="showDeleteConfirmation = true"
                  >
                     {{ t('opportunities.deleteOpportunity') }}
                  </ActionButton>
               </div>
            </div>
         </div>
      </div>

      <!-- Delete Confirmation Modal -->
      <div
         v-if="showDeleteConfirmation && !isNewOpportunity"
         class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
         @click.self="showDeleteConfirmation = false"
      >
         <div class="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 p-6">
            <h3 class="text-lg font-semibold text-gray-900 mb-4">
               {{ t('opportunities.confirmDeletion') }}
            </h3>
            <p class="text-sm text-gray-600 mb-6">
               {{ t('opportunities.confirmDeletionBody') }}
            </p>
            <ul class="text-sm text-gray-600 mb-6 list-disc list-inside space-y-1">
               <li>{{ t('opportunities.deleteListItemOpportunityDetails') }}</li>
               <li>{{ t('opportunities.deleteListItemQuotesDocuments') }}</li>
               <li>{{ t('opportunities.deleteListItemRelatedData') }}</li>
            </ul>
            <div class="flex gap-3 justify-end">
               <ActionButton
                  type="button"
                  variant="neutral"
                  @click="showDeleteConfirmation = false"
               >
                  {{ t('common.cancel') }}
               </ActionButton>
               <ActionButton
                  type="button"
                  variant="danger"
                  :disabled="isDeleting"
                  @click="deleteOpportunity"
               >
                  {{
                     isDeleting ? t('opportunities.deleting') : t('opportunities.deleteOpportunity')
                  }}
               </ActionButton>
            </div>
         </div>
      </div>
   </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useAuth } from '../../../../stores/auth';
import OpportunityHeader from '../../OpportunityHeader.vue';
import { useI18n } from '../../../../i18n/useI18n';
import { useApiQuery } from '../../../../composables/useApiQuery';
import { authFetch } from '../../../../api/authFetch';
import ActionButton from '../../../common/ActionButton.vue';

const route = useRoute();
const router = useRouter();
const { session } = useAuth();
const { t } = useI18n();
const { fetchApiJson } = useApiQuery();

const opportunityId = ref(route.params.id as string);
const opportunity = ref<any>(null);
const isLoading = ref(false);
const isDeleting = ref(false);
const errorMessage = ref('');
const successMessage = ref('');
const showDeleteConfirmation = ref(false);
const isNewOpportunity = computed(() => opportunityId.value === 'new');

const loadOpportunity = async () => {
   if (isNewOpportunity.value) {
      opportunity.value = null;
      return;
   }
   isLoading.value = true;
   errorMessage.value = '';

   try {
      const result = await fetchApiJson<{ status: string; opportunity?: any }>('opportunity', {
         opportunity_id: opportunityId.value,
      });

      if (result?.status !== 'ok' || !result?.opportunity) {
         throw new Error('Failed loading opportunity');
      }

      opportunity.value = result.opportunity;
   } catch (error: any) {
      errorMessage.value = t('opportunities.errorLoadingOpportunity', {
         message: error.message,
      });
      console.error('[SettingsPage] Error loading opportunity:', error);
   } finally {
      isLoading.value = false;
   }
};

const deleteOpportunity = async () => {
   isDeleting.value = true;
   errorMessage.value = '';

   try {
      const url = `/api/opportunities/${opportunityId.value}`;
      console.log('[SettingsPage] DELETE request to:', url);
      console.log(
         '[SettingsPage] Session token:',
         session.value?.access_token?.substring(0, 20) + '...'
      );

      const response = await authFetch(url, {
         method: 'DELETE',
         headers: {
            'Content-Type': 'application/json',
         },
      });

      console.log('[SettingsPage] Response status:', response.status);
      console.log(
         '[SettingsPage] Response headers:',
         Object.fromEntries(response.headers.entries())
      );

      const result = await response.json();
      console.log('[SettingsPage] Response body:', result);

      if (response.ok && result.status === 'ok') {
         successMessage.value = t('opportunities.opportunityDeletedSuccess');
         showDeleteConfirmation.value = false;

         // Redirect to opportunities list after a short delay
         setTimeout(() => {
            router.push('/opportunities');
         }, 1000);
      } else {
         throw new Error(result.message || t('opportunities.failedToDeleteOpportunity'));
      }
   } catch (error: any) {
      errorMessage.value = t('opportunities.errorDeletingOpportunity', {
         message: error.message,
      });
      console.error('[SettingsPage] Error deleting opportunity:', error);
      showDeleteConfirmation.value = false;
   } finally {
      isDeleting.value = false;
   }
};

onMounted(() => {
   loadOpportunity();
});
</script>
