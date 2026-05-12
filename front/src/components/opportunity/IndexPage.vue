<template>
   <div class="opportunity-page">
      <div class="mb-6">
         <!-- Breadcrumb and Actions -->
         <div class="flex items-center justify-between mb-4">
            <div class="flex gap-2">
               <!-- Batch Actions Menu -->
               <div v-if="selectedOpportunities.size > 0" class="relative">
                  <button
                     @click="showBatchMenu = !showBatchMenu"
                     class="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg font-medium text-sm"
                  >
                     {{ t('opportunities.actions') }} ({{ selectedOpportunities.size }})
                  </button>
                  <div
                     v-if="showBatchMenu"
                     class="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg z-10"
                  >
                     <button
                        @click="batchDeleteConfirm"
                        class="w-full text-left px-4 py-2 hover:bg-red-50 text-red-600 font-medium text-sm"
                     >
                        {{ t('opportunities.deleteSelected') }}
                     </button>
                  </div>
               </div>
               <!-- Create Button -->
               <router-link
                  to="/opportunities/new"
                  class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium text-sm"
               >
                  {{ t('opportunities.createOpportunity') }}
               </router-link>
            </div>
         </div>
      </div>

      <!-- Error Message -->
      <div
         v-if="errorMessage"
         class="mb-4 p-4 bg-red-100 text-red-700 rounded-lg flex items-center justify-between"
      >
         <span>{{ errorMessage }}</span>
         <button
            @click="loadOpportunities"
            class="px-3 py-1 bg-red-600 hover:bg-red-700 text-white rounded text-sm font-medium"
         >
            {{ t('opportunities.retry') }}
         </button>
      </div>

      <!-- Search Filter -->
      <div class="mb-4 flex gap-4">
         <div class="flex-1">
            <label for="sourceRefSearch" class="block text-sm font-medium text-gray-700 mb-2">
               {{ t('opportunities.searchLabel') }}
            </label>
            <input
               id="sourceRefSearch"
               v-model="sourceReferenceFilter"
               @input="searchOpportunities"
               type="text"
               :placeholder="t('opportunities.searchPlaceholder')"
               class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
         </div>
         <div class="flex items-end">
            <button
               v-if="shouldShowAddButton"
               @click="createOpportunityFromSearch"
               class="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg font-medium text-sm"
            >
               {{ t('opportunities.add') }}
            </button>
            <button
               v-else-if="sourceReferenceFilter"
               @click="clearSearch"
               class="px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-700 rounded-lg font-medium text-sm"
            >
               {{ t('opportunities.clear') }}
            </button>
         </div>
      </div>

      <!-- Loading State -->
      <div v-if="isLoading" class="flex justify-center items-center py-12">
         <div class="text-gray-500">{{ t('opportunities.loading') }}</div>
      </div>

      <!-- Opportunities Table -->
      <div v-else class="bg-white rounded-lg shadow overflow-hidden">
         <div v-if="opportunities.length === 0" class="p-6 text-center text-gray-500">
            {{
               sourceReferenceFilter
                  ? t('opportunities.noOpportunitiesFiltered')
                  : t('opportunities.noOpportunities')
            }}
         </div>
         <table v-else class="w-full">
            <thead class="bg-gray-50 border-b">
               <tr>
                  <th class="px-4 py-3 text-left w-10">
                     <input
                        type="checkbox"
                        @change="toggleSelectAll"
                        :checked="
                           selectedOpportunities.size === opportunities.length &&
                           opportunities.length > 0
                        "
                        class="w-4 h-4 rounded"
                     />
                  </th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">
                     {{ t('opportunities.tableHeaders.name') }}
                  </th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">
                     {{ t('opportunities.tableHeaders.account') }}
                  </th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">
                     {{ t('opportunities.tableHeaders.stage') }}
                  </th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">
                     {{ t('opportunities.tableHeaders.status') }}
                  </th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">
                     {{ t('opportunities.tableHeaders.amount') }}
                  </th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">
                     {{ t('opportunities.source') }}
                  </th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">
                     {{ t('opportunities.tableHeaders.sourceRef') }}
                  </th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">
                     {{ t('opportunities.tableHeaders.created') }}
                  </th>
               </tr>
            </thead>
            <tbody class="divide-y">
               <tr
                  v-for="opportunity in opportunities"
                  :key="opportunity.id"
                  @click="goToDetail(opportunity.id)"
                  class="hover:bg-gray-50 transition-colors cursor-pointer"
               >
                  <td class="px-4 py-4 w-10" @click.stop>
                     <input
                        type="checkbox"
                        @change="toggleSelect(opportunity.id)"
                        :checked="selectedOpportunities.has(opportunity.id)"
                        class="w-4 h-4 rounded"
                     />
                  </td>
                  <td class="px-6 py-4 text-sm font-medium text-gray-900">
                     {{ opportunity.name }}
                  </td>
                  <td class="px-6 py-4 text-sm text-gray-600">
                     {{ opportunity.account_name || opportunity.account_id || '-' }}
                  </td>
                  <td class="px-6 py-4 text-sm">
                     <span
                        class="inline-block px-3 py-1 rounded-full text-xs font-medium"
                        :class="getStageColor(opportunity.stage)"
                     >
                        {{ getStageLabel(opportunity.stage) }}
                     </span>
                  </td>
                  <td class="px-6 py-4 text-sm">
                     <span
                        class="inline-block px-3 py-1 rounded-full text-xs font-medium"
                        :class="getStatusColor(opportunity.status)"
                     >
                        {{ getStatusLabel(opportunity.status) }}
                     </span>
                  </td>
                  <td class="px-6 py-4 text-sm text-gray-600">
                     {{
                        opportunity.amount_estimated
                           ? `${
                                opportunity.currency || 'EUR'
                             } ${opportunity.amount_estimated.toLocaleString()}`
                           : '-'
                     }}
                  </td>
                  <td class="px-6 py-4 text-sm text-gray-600">
                     {{ getSourceLabel(opportunity.source) }}
                  </td>
                  <td class="px-6 py-4 text-gray-500 font-mono text-xs">
                     {{
                        opportunity.source_reference_id
                           ? opportunity.source_reference_id.substring(0, 8) + '...'
                           : '-'
                     }}
                  </td>
                  <td class="px-6 py-4 text-sm text-gray-600">
                     {{ formatDate(opportunity.created_at) }}
                  </td>
               </tr>
            </tbody>
         </table>
      </div>

      <!-- Batch Delete Confirmation Modal -->
      <div
         v-if="showBatchDeleteConfirmation"
         class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
         @click.self="showBatchDeleteConfirmation = false"
      >
         <div class="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 p-6">
            <h3 class="text-lg font-semibold text-gray-900 mb-4">
               {{ t('opportunities.batchDelete.confirmTitle') }}
            </h3>
            <p class="text-sm text-gray-600 mb-4">
               {{
                  t('opportunities.batchDelete.confirmMessage', {
                     count: selectedOpportunities.size,
                  })
               }}
            </p>
            <div class="flex gap-3 justify-end">
               <button
                  @click="showBatchDeleteConfirmation = false"
                  class="px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-700 rounded-lg font-medium text-sm transition-colors"
               >
                  {{ t('common.cancel') }}
               </button>
               <button
                  @click="batchDelete"
                  :disabled="isDeleting"
                  class="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium text-sm transition-colors disabled:opacity-50"
               >
                  {{
                     isDeleting
                        ? t('opportunities.batchDelete.deleting')
                        : t('opportunities.batchDelete.deleteAll')
                  }}
               </button>
            </div>
         </div>
      </div>
   </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useAuth } from '../../stores/auth';
import { useI18n } from '../../i18n/useI18n';
import { supabase } from '../../lib/supabase';
import { apiUrl } from '../../utils/api';

const { t, te } = useI18n();

interface Opportunity {
   id: string;
   name: string;
   stage: string;
   status: string;
   amount_estimated?: number;
   currency?: string;
   created_at: string;
   account_id?: string;
   account_name?: string;
   source?: string;
   source_reference_id?: string;
}

const opportunities = ref<Opportunity[]>([]);
const isLoading = ref(false);
const isDeleting = ref(false);
const errorMessage = ref('');
const sourceReferenceFilter = ref('');
const selectedOpportunities = ref(new Set<string>());
const showBatchMenu = ref(false);
const showBatchDeleteConfirmation = ref(false);
const { user, session } = useAuth();
const router = useRouter();
const route = useRoute();

let searchTimeout: ReturnType<typeof setTimeout> | null = null;

const getStageColor = (stage: string) => {
   const stageColors: Record<string, string> = {
      NEW_LEAD: 'bg-blue-100 text-blue-700',
      QUALIFYING: 'bg-cyan-100 text-cyan-700',
      NEEDS_DEFINED: 'bg-indigo-100 text-indigo-700',
      RFP_IN_PROGRESS: 'bg-purple-100 text-purple-700',
      RFQ_IN_PROGRESS: 'bg-fuchsia-100 text-fuchsia-700',
      OFFER_SENT: 'bg-pink-100 text-pink-700',
      NEGOTIATION: 'bg-rose-100 text-rose-700',
      COMMITMENT: 'bg-orange-100 text-orange-700',
      PREPARATION: 'bg-amber-100 text-amber-700',
      DELIVERY_IN_PROGRESS: 'bg-amber-100 text-amber-700',
      ACCEPTED: 'bg-green-100 text-green-700',
      INVOICED: 'bg-emerald-100 text-emerald-700',
      PAID: 'bg-lime-100 text-lime-700',
      CLOSED_WON: 'bg-teal-100 text-teal-700',
      CLOSED_LOST: 'bg-gray-100 text-gray-700',
      ON_HOLD: 'bg-slate-100 text-slate-700',
   };
   return stageColors[stage] || 'bg-gray-100 text-gray-700';
};

const getStageLabel = (stage?: string) => {
   if (!stage) return '-';
   const key = `opportunities.stages.${stage}` as const;
   return te(key) ? t(key) : stage;
};

const getStatusColor = (status: string) => {
   const statusColors: Record<string, string> = {
      OPEN: 'bg-green-100 text-green-700',
      WON: 'bg-emerald-100 text-emerald-700',
      LOST: 'bg-red-100 text-red-700',
      ON_HOLD: 'bg-yellow-100 text-yellow-700',
   };
   return statusColors[status] || 'bg-gray-100 text-gray-700';
};

const getStatusLabel = (status?: string) => {
   if (!status) return '-';
   const key = `opportunities.statuses.${status}` as const;
   return te(key) ? t(key) : status;
};

const getSourceLabel = (source?: string) => {
   if (!source) return '-';
   const normalized = source.toLowerCase();
   const key = `opportunities.sourceTypes.${normalized}` as const;
   return te(key) ? t(key) : source;
};

const formatDate = (dateString: string) => {
   try {
      const date = new Date(dateString);
      return (
         date.toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
         }) +
         ' ' +
         date
            .toLocaleTimeString('en-US', {
               hour: 'numeric',
               minute: '2-digit',
               hour12: true,
            })
            .toLowerCase()
      );
   } catch {
      return dateString;
   }
};

const loadAccountNames = async (items: Opportunity[]) => {
   const accountIds = Array.from(
      new Set(items.map((opp) => opp.account_id).filter((id): id is string => !!id))
   );
   if (accountIds.length === 0) return;

   try {
      const { data, error } = await supabase
         .from('account')
         .select('id, name')
         .in('id', accountIds);

      if (error) {
         console.warn('[OpportunityPage] Failed to load account names:', error);
         return;
      }

      const accountMap = new Map<string, string>();
      (data || []).forEach((account: any) => {
         if (account?.id) accountMap.set(account.id, account.name || '');
      });

      items.forEach((opp) => {
         if (opp.account_id && accountMap.has(opp.account_id)) {
            opp.account_name = accountMap.get(opp.account_id) || '';
         }
      });
   } catch (error) {
      console.warn('[OpportunityPage] Error fetching account names:', error);
   }
};

const loadOpportunities = async () => {
   isLoading.value = true;
   errorMessage.value = '';

   if (!user.value?.id) {
      errorMessage.value = t('opportunities.errors.userNotAuthenticated');
      isLoading.value = false;
      return;
   }

   console.log(`[OpportunityPage] Loading opportunities for user ${user.value.id}`);

   try {
      const headers: HeadersInit = {
         'Content-Type': 'application/json',
      };
      if (session.value?.access_token) {
         headers['Authorization'] = `Bearer ${session.value.access_token}`;
      }

      // Build query params
      let url = apiUrl('opportunities/search');
      if (sourceReferenceFilter.value.trim()) {
         const trimmedValue = sourceReferenceFilter.value.trim();
         const isUuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(
            trimmedValue
         );
         url += isUuid
            ? `?source_reference_id=${encodeURIComponent(trimmedValue)}`
            : `?name=${encodeURIComponent(trimmedValue)}`;
      }

      const response = await fetch(url, { headers });

      // Some backend errors may return an empty body or non-JSON payload.
      const responseText = await response.text();
      let result: any = null;
      if (responseText) {
         try {
            result = JSON.parse(responseText);
         } catch {
            throw new Error(`Invalid backend response (HTTP ${response.status})`);
         }
      }

      if (response.status === 204) {
         opportunities.value = [];
         return;
      }

      if (!response.ok) {
         throw new Error(result?.message || `HTTP ${response.status}`);
      }

      if (result?.status === 'ok') {
         opportunities.value = result.opportunities || [];
         await loadAccountNames(opportunities.value);
         console.log('[OpportunityPage] Fetched opportunities:', opportunities.value.length);
      } else {
         throw new Error(result?.message || 'Failed to load opportunities');
      }
   } catch (error: any) {
      errorMessage.value = `Error loading opportunities: ${error.message}. Please try refreshing the page.`;
      console.error('[OpportunityPage] Error during fetch:', error);
   } finally {
      isLoading.value = false;
   }
};

const searchOpportunities = () => {
   // Debounce search to avoid excessive API calls
   if (searchTimeout) {
      clearTimeout(searchTimeout);
   }
   searchTimeout = setTimeout(() => {
      loadOpportunities();
   }, 500);
};

const isUuid = (value: string) =>
   /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(value);

const shouldShowAddButton = computed(() => {
   const trimmedValue = sourceReferenceFilter.value.trim();
   if (!trimmedValue || isLoading.value) return false;
   if (opportunities.value.length > 0) return false;
   return !isUuid(trimmedValue);
});

const createOpportunityFromSearch = async () => {
   const trimmedValue = sourceReferenceFilter.value.trim();
   if (!trimmedValue) return;

   errorMessage.value = '';
   isLoading.value = true;

   try {
      const headers: HeadersInit = {
         'Content-Type': 'application/json',
      };
      if (session.value?.access_token) {
         headers['Authorization'] = `Bearer ${session.value.access_token}`;
      }

      const response = await fetch('/api/opportunities/create-manual', {
         method: 'POST',
         headers,
         body: JSON.stringify({ name: trimmedValue }),
      });

      const result = await response.json();
      if (!response.ok || result.status !== 'ok') {
         throw new Error(result.message || 'Failed to create opportunity');
      }

      const createdId = result.opportunity?.id;
      if (createdId) {
         router.push(`/opportunities/${createdId}/source`);
         return;
      }

      await loadOpportunities();
   } catch (error: any) {
      errorMessage.value = `Error creating opportunity: ${error.message}`;
      console.error('[OpportunityPage] Error creating opportunity:', error);
   } finally {
      isLoading.value = false;
   }
};

const clearSearch = () => {
   sourceReferenceFilter.value = '';
   loadOpportunities();
};

const toggleSelect = (opportunityId: string) => {
   if (selectedOpportunities.value.has(opportunityId)) {
      selectedOpportunities.value.delete(opportunityId);
   } else {
      selectedOpportunities.value.add(opportunityId);
   }
   showBatchMenu.value = false;
};

const toggleSelectAll = () => {
   if (selectedOpportunities.value.size === opportunities.value.length) {
      selectedOpportunities.value.clear();
   } else {
      selectedOpportunities.value.clear();
      opportunities.value.forEach((opp) => selectedOpportunities.value.add(opp.id));
   }
};

const batchDeleteConfirm = () => {
   showBatchDeleteConfirmation.value = true;
   showBatchMenu.value = false;
};

const batchDelete = async () => {
   isDeleting.value = true;
   errorMessage.value = '';

   try {
      const headers: HeadersInit = {
         'Content-Type': 'application/json',
      };
      if (session.value?.access_token) {
         headers['Authorization'] = `Bearer ${session.value.access_token}`;
      }

      // Convert Set to comma-separated string of IDs
      const idsToDelete = Array.from(selectedOpportunities.value).join(',');
      const url = `/api/opportunities/${idsToDelete}`;

      console.log('[OpportunityPage] Batch delete:', Array.from(selectedOpportunities.value));

      const response = await fetch(url, {
         method: 'DELETE',
         headers,
      });

      const result = await response.json();

      if (response.ok && result.status === 'ok') {
         // Remove deleted opportunities from the list
         const deletedIds = new Set(selectedOpportunities.value);
         opportunities.value = opportunities.value.filter((opp) => !deletedIds.has(opp.id));
         selectedOpportunities.value.clear();
         showBatchDeleteConfirmation.value = false;

         // Show success message
         errorMessage.value = `Successfully deleted ${result.deleted_count || selectedOpportunities.value.size} opportunity(ies)`;
         setTimeout(() => {
            errorMessage.value = '';
         }, 3000);
      } else {
         throw new Error(result.message || 'Failed to delete opportunities');
      }
   } catch (error: any) {
      errorMessage.value = `Error deleting opportunities: ${error.message}`;
      console.error('[OpportunityPage] Error during batch delete:', error);
   } finally {
      isDeleting.value = false;
   }
};

onMounted(() => {
   // Check if source_reference_id is provided in query parameters
   const sourceRefParam = route.query.source_reference_id as string;
   if (sourceRefParam) {
      sourceReferenceFilter.value = sourceRefParam;
   }
   loadOpportunities();
});

const goToDetail = (id: string) => {
   router.push(`/opportunities/${id}/source`);
};
</script>
