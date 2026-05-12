<template>
   <div class="opportunity-page">
      <OpportunityHeader :opportunityId="opportunityId" activeTab="documents" />

      <div v-if="errorMessage" class="mb-4 p-4 bg-red-100 text-red-700 rounded-lg">
         {{ errorMessage }}
      </div>

      <div v-if="isLoading" class="flex justify-center items-center py-12">
         <div class="text-gray-500">{{ t('opportunities.loadingDocuments') }}</div>
      </div>

      <div v-else class="opportunity-page-section m-4 bg-white rounded-lg shadow">
         <div class="p-6">
            <div class="flex items-center justify-between mb-6">
               <h2 class="text-xl font-semibold text-gray-900">
                  {{ t('opportunities.documentsTitle') }}
               </h2>
               <span class="text-sm text-gray-500">
                  {{ documents.length }}
                  {{
                     documents.length === 1
                        ? t('opportunities.documentSingular')
                        : t('opportunities.documentPlural')
                  }}
               </span>
            </div>

            <div v-if="isNewOpportunity" class="text-center py-12 text-gray-500">
               {{ t('opportunities.noDocumentsFound') }}
            </div>

            <div v-else-if="documents.length === 0" class="text-center py-12 text-gray-500">
               {{ t('opportunities.noDocumentsFound') }}
            </div>

            <div v-else class="overflow-x-auto">
               <table class="min-w-full divide-y divide-gray-200">
                  <thead class="bg-gray-50">
                     <tr>
                        <th
                           class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                        >
                           {{ t('opportunities.documentType') }}
                        </th>
                        <th
                           class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                        >
                           {{ t('opportunities.documentTitle') }}
                        </th>
                        <th
                           class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                        >
                           {{ t('opportunities.documentStatus') }}
                        </th>
                        <th
                           class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                        >
                           {{ t('opportunities.documentAmount') }}
                        </th>
                        <th
                           class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                        >
                           {{ t('opportunities.documentDate') }}
                        </th>
                        <th
                           class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                        >
                           {{ t('opportunities.documentFile') }}
                        </th>
                        <th
                           class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                        >
                           Actions
                        </th>
                     </tr>
                  </thead>
                  <tbody class="bg-white divide-y divide-gray-200">
                     <tr v-for="doc in documents" :key="doc.id" class="hover:bg-gray-50">
                        <td class="px-6 py-4 whitespace-nowrap">
                           <span
                              class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
                              :class="getTypeColor(doc.type)"
                           >
                              {{ doc.type }}
                           </span>
                        </td>
                        <td class="px-6 py-4">
                           <div v-if="doc.type === 'INVOICE'" class="text-sm font-medium">
                              <router-link
                                 :to="`/opportunities/${opportunityId}/invoices/${doc.id}`"
                                 class="text-blue-600 hover:text-blue-800 hover:underline"
                              >
                                 {{ doc.title }}
                              </router-link>
                           </div>
                           <div v-else class="text-sm font-medium text-gray-900">
                              {{ doc.title }}
                           </div>
                           <div v-if="doc.external_ref" class="text-sm text-gray-500">
                              {{ t('opportunities.documentRef') }}: {{ doc.external_ref }}
                           </div>
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap">
                           <span
                              class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
                              :class="getStatusColor(doc.status)"
                           >
                              {{ formatStatus(doc.status) }}
                           </span>
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                           <div v-if="doc.total_incl_tax">
                              {{ formatCurrency(doc.total_incl_tax, doc.currency) }}
                           </div>
                           <div v-else class="text-gray-400">—</div>
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                           {{ formatDate(doc.created_at) }}
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm">
                           <router-link
                              v-if="doc.storage_key"
                              :to="`/opportunities/${opportunityId}/documents/${doc.id}`"
                              class="text-blue-600 hover:text-blue-800 flex items-center gap-1"
                           >
                              <svg
                                 class="w-4 h-4"
                                 fill="none"
                                 stroke="currentColor"
                                 viewBox="0 0 24 24"
                              >
                                 <path
                                    stroke-linecap="round"
                                    stroke-linejoin="round"
                                    stroke-width="2"
                                    d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                                 />
                              </svg>
                              {{ t('opportunities.view') }}
                           </router-link>
                           <span v-else class="text-gray-400">
                              {{ t('opportunities.noFile') }}
                           </span>
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm">
                           <button
                              @click="deleteDocument(doc)"
                              :disabled="deletingIds.has(doc.id)"
                              class="text-red-600 hover:text-red-800 disabled:opacity-50 disabled:cursor-not-allowed"
                              :title="t('common.delete')"
                           >
                              <svg
                                 class="w-5 h-5"
                                 fill="none"
                                 stroke="currentColor"
                                 viewBox="0 0 24 24"
                              >
                                 <path
                                    stroke-linecap="round"
                                    stroke-linejoin="round"
                                    stroke-width="2"
                                    d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                                 />
                              </svg>
                           </button>
                        </td>
                     </tr>
                  </tbody>
               </table>
            </div>
         </div>
      </div>
   </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRoute } from 'vue-router';
import { supabase } from '../../../../lib/supabase';
import OpportunityHeader from '../../OpportunityHeader.vue';
import { useI18n } from '../../../../i18n/useI18n';
import { useAuth } from '../../../../stores/auth';

const route = useRoute();
const opportunityId = route.params.id as string;
const isNewOpportunity = computed(() => opportunityId === 'new');
const { t, locale } = useI18n();
const { getValidToken } = useAuth();

const isLoading = ref(true);
const errorMessage = ref('');
const documents = ref<any[]>([]);
const deletingIds = ref(new Set<string>());

const loadDocuments = async () => {
   if (isNewOpportunity.value) {
      documents.value = [];
      isLoading.value = false;
      return;
   }
   try {
      const { data, error } = await supabase
         .from('document')
         .select(
            'id, type, status, title, external_ref, currency, total_excl_tax, total_tax, total_incl_tax, storage_key, issued_at, received_at, created_at'
         )
         .eq('opportunity_id', opportunityId)
         .order('created_at', { ascending: false });

      if (error) {
         throw error;
      }

      documents.value = data || [];
   } catch (error: any) {
      errorMessage.value = error?.message || t('opportunities.failedToLoadDocuments');
      console.error('[DocumentsPage] Error loading documents:', error);
   } finally {
      isLoading.value = false;
   }
};

const getTypeColor = (type: string) => {
   const colors: Record<string, string> = {
      RFI: 'bg-purple-100 text-purple-800',
      RFP: 'bg-purple-100 text-purple-800',
      RFQ: 'bg-blue-100 text-blue-800',
      PROPOSAL: 'bg-indigo-100 text-indigo-800',
      QUOTE: 'bg-green-100 text-green-800',
      PO: 'bg-yellow-100 text-yellow-800',
      CONTRACT: 'bg-orange-100 text-orange-800',
      DELIVERY_NOTE: 'bg-teal-100 text-teal-800',
      ACCEPTANCE: 'bg-emerald-100 text-emerald-800',
      INVOICE: 'bg-red-100 text-red-800',
      CREDIT_NOTE: 'bg-pink-100 text-pink-800',
      NDA: 'bg-gray-100 text-gray-800',
      DPA: 'bg-gray-100 text-gray-800',
      SLA: 'bg-gray-100 text-gray-800',
      CGV: 'bg-gray-100 text-gray-800',
   };
   return colors[type] || 'bg-gray-100 text-gray-800';
};

const getStatusColor = (status: string) => {
   const colors: Record<string, string> = {
      DRAFT: 'bg-gray-100 text-gray-800',
      SENT: 'bg-blue-100 text-blue-800',
      RECEIVED: 'bg-blue-100 text-blue-800',
      SUBMITTED: 'bg-indigo-100 text-indigo-800',
      SHORTLISTED: 'bg-purple-100 text-purple-800',
      ACCEPTED: 'bg-green-100 text-green-800',
      REJECTED: 'bg-red-100 text-red-800',
      CONFIRMED: 'bg-emerald-100 text-emerald-800',
      FULFILLED: 'bg-teal-100 text-teal-800',
      CANCELLED: 'bg-red-100 text-red-800',
      EXPIRED: 'bg-orange-100 text-orange-800',
      PAID: 'bg-green-100 text-green-800',
      PARTIALLY_PAID: 'bg-yellow-100 text-yellow-800',
      OVERDUE: 'bg-red-100 text-red-800',
      DISPUTED: 'bg-orange-100 text-orange-800',
      APPLIED: 'bg-blue-100 text-blue-800',
   };
   return colors[status] || 'bg-gray-100 text-gray-800';
};

const formatStatus = (status: string) => {
   return status.replace(/_/g, ' ');
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

const deleteDocument = async (doc: any) => {
   if (!confirm(`Are you sure you want to delete "${doc.title || doc.external_ref}"?`)) {
      return;
   }

   deletingIds.value.add(doc.id);
   errorMessage.value = '';

   try {
      const token = await getValidToken();
      const response = await fetch(`/api/document/${doc.id}`, {
         method: 'DELETE',
         headers: {
            Authorization: `Bearer ${token}`,
         },
      });

      const result = await response.json();

      if (!response.ok) {
         throw new Error(result?.message || 'Failed to delete document');
      }

      // Remove from list
      documents.value = documents.value.filter((d) => d.id !== doc.id);
   } catch (error: any) {
      errorMessage.value = error?.message || 'Failed to delete document';
      console.error('[DocumentsPage] Error deleting document:', error);
   } finally {
      deletingIds.value.delete(doc.id);
   }
};

onMounted(() => {
   loadDocuments();
});
</script>
