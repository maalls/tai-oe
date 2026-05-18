<template>
   <div class="p-4 pb-0">
      <!-- Breadcrumb and Stage -->
      <div class="flex items-center justify-between mb-4">
         <div class="flex items-center gap-2">
            <div class="relative">
               <button
                  @click="showDropdown = !showDropdown"
                  class="min-w-96 px-2 py-1 border border-gray-300 rounded bg-white text-gray-600 hover:text-gray-900 cursor-pointer focus:outline-none focus:ring-2 focus:ring-blue-500 flex items-center justify-between"
               >
                  <span v-if="opportunityData" class="text-left flex-1">
                     {{ opportunityData.name || t('opportunities.untitled') }}
                  </span>
                  <span v-else-if="loadingRecent">{{ t('opportunities.loadingDots') }}</span>
                  <span v-else>{{ t('opportunities.selectOpportunity') }}</span>
                  <svg
                     class="w-4 h-4 ml-2 shrink-0"
                     :class="{ 'transform rotate-180': showDropdown }"
                     fill="none"
                     stroke="currentColor"
                     viewBox="0 0 24 24"
                  >
                     <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M19 9l-7 7-7-7"
                     />
                  </svg>
               </button>
               <div
                  v-if="showDropdown"
                  class="absolute top-full left-0 mt-1 w-full bg-white border border-gray-300 rounded shadow-lg max-h-96 overflow-y-auto z-50"
               >
                  <div class="p-2 border-b border-gray-100">
                     <input
                        ref="searchInput"
                        v-model="searchQuery"
                        type="text"
                        :placeholder="t('opportunities.searchOpportunities')"
                        class="w-full px-3 py-2 border border-gray-200 rounded text-sm text-gray-700 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                     />
                  </div>
                  <div v-if="loadingRecent" class="px-4 py-2 text-gray-500 text-sm">
                     {{ t('opportunities.loadingDots') }}
                  </div>
                  <div v-else-if="loadingSearch" class="px-4 py-2 text-gray-500 text-sm">
                     {{ t('opportunities.searching') }}
                  </div>
                  <div
                     v-else-if="searchQuery && filteredOpportunities.length === 0"
                     class="px-4 py-2 text-gray-500 text-sm"
                  >
                     {{ t('opportunities.noMatches') }}
                  </div>
                  <button
                     v-for="opp in filteredOpportunities"
                     :key="opp.id"
                     @click="selectOpportunity(opp.id)"
                     class="w-full text-left px-4 py-2 hover:bg-gray-100 text-gray-900 text-sm border-b border-gray-100 last:border-b-0"
                     :class="{ 'bg-blue-50': opp.id === selectedOpportunityId }"
                  >
                     <div class="font-medium">{{ opp.name || t('opportunities.untitled') }}</div>
                     <div class="text-xs text-gray-500">
                        {{ opp.source || t('opportunities.notAvailable') }} ·
                        {{ formatDate(opp.updated_at) }}
                     </div>
                  </button>
               </div>
            </div>
            <button
               @click="createNewOpportunity"
               class="px-2 py-1 border border-gray-300 rounded bg-white text-gray-600 hover:text-gray-900 hover:bg-gray-50 cursor-pointer focus:outline-none focus:ring-2 focus:ring-blue-500 flex items-center justify-center"
               :title="t('opportunities.createNewOpportunity')"
            >
               <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                     stroke-linecap="round"
                     stroke-linejoin="round"
                     stroke-width="2"
                     d="M12 4v16m8-8H4"
                  />
               </svg>
            </button>
         </div>
         <div v-if="opportunityData" class="flex items-center gap-2">
            <div class="px-3 py-1 bg-blue-100 text-blue-800 text-sm font-medium rounded-full">
               {{ getStageLabel(opportunityData.stage) }}
            </div>
            <div class="px-3 py-1 bg-gray-100 text-gray-700 text-sm font-medium rounded-full">
               {{ getSourceLabel(opportunityData.source) }}
            </div>
         </div>
      </div>
      <!-- Tab Navigation -->
      <div class="border-b border-gray-300">
         <div class="flex gap-2">
            <!--router-link
               :to="`/opportunities/${opportunityId}/chat`"
               :class="[
                  'px-4 py-2 text-sm font-medium border-b-2 transition-colors',
                  resolvedActiveTab === 'chat'
                     ? 'border-blue-600 text-blue-600'
                     : 'border-transparent text-gray-600 hover:text-gray-900',
               ]"
            >
               {{ t('opportunities.chat') }}
            </router-link-->
            <router-link
               :to="`/opportunities/${opportunityId}/pipeline`"
               :class="[
                  'px-4 py-2 text-sm font-medium border-b-2 transition-colors',
                  resolvedActiveTab === 'pipeline'
                     ? 'border-blue-600 text-blue-600'
                     : 'border-transparent text-gray-600 hover:text-gray-900',
               ]"
            >
               {{ t('opportunities.pipelineTab') }}
            </router-link>
            <router-link
               :to="`/opportunities/${opportunityId}/source`"
               :class="[
                  'px-4 py-2 text-sm font-medium border-b-2 transition-colors',
                  resolvedActiveTab === 'source'
                     ? 'border-blue-600 text-blue-600'
                     : 'border-transparent text-gray-600 hover:text-gray-900',
               ]"
            >
               {{ t('opportunities.source') }}
            </router-link>
            <router-link
               :to="`/opportunities/${opportunityId}/account`"
               :class="[
                  'px-4 py-2 text-sm font-medium border-b-2 transition-colors',
                  resolvedActiveTab === 'account'
                     ? 'border-blue-600 text-blue-600'
                     : 'border-transparent text-gray-600 hover:text-gray-900',
               ]"
            >
               {{ t('opportunities.account') }}
            </router-link>
            <router-link
               :to="`/opportunities/${opportunityId}/quote`"
               :class="[
                  'px-4 py-2 text-sm font-medium border-b-2 transition-colors',
                  resolvedActiveTab === 'quote'
                     ? 'border-blue-600 text-blue-600'
                     : 'border-transparent text-gray-600 hover:text-gray-900',
               ]"
            >
               {{ t('opportunities.quote') }}
            </router-link>
            <router-link
               v-if="hasPdf"
               :to="`/opportunities/${opportunityId}/preview`"
               :class="[
                  'px-4 py-2 text-sm font-medium border-b-2 transition-colors',
                  resolvedActiveTab === 'preview'
                     ? 'border-blue-600 text-blue-600'
                     : 'border-transparent text-gray-600 hover:text-gray-900',
               ]"
            >
               {{ t('opportunities.preview') }}
            </router-link>
            <router-link
               :to="`/opportunities/${opportunityId}/send`"
               :class="[
                  'px-4 py-2 text-sm font-medium border-b-2 transition-colors',
                  resolvedActiveTab === 'send'
                     ? 'border-blue-600 text-blue-600'
                     : 'border-transparent text-gray-600 hover:text-gray-900',
               ]"
            >
               {{ t('opportunities.send') }}
            </router-link>

            <router-link
               :to="`/opportunities/${opportunityId}/invoices`"
               :class="[
                  'px-4 py-2 text-sm font-medium border-b-2 transition-colors',
                  resolvedActiveTab === 'invoices'
                     ? 'border-blue-600 text-blue-600'
                     : 'border-transparent text-gray-600 hover:text-gray-900',
               ]"
            >
               {{ t('opportunities.invoicesTitle') }}
            </router-link>
            <!--router-link
               :to="`/opportunities/${opportunityId}/actions`"
               :class="[
                  'px-4 py-2 text-sm font-medium border-b-2 transition-colors',
                  resolvedActiveTab === 'actions'
                     ? 'border-blue-600 text-blue-600'
                     : 'border-transparent text-gray-600 hover:text-gray-900',
               ]"
            >
               {{ t('opportunities.actions') }}
            </router-link-->
            <router-link
               :to="`/opportunities/${opportunityId}/documents`"
               :class="[
                  'px-4 py-2 text-sm font-medium border-b-2 transition-colors',
                  resolvedActiveTab === 'documents'
                     ? 'border-blue-600 text-blue-600'
                     : 'border-transparent text-gray-600 hover:text-gray-900',
               ]"
            >
               {{ t('opportunities.documents') }}
            </router-link>

            <router-link
               :to="`/opportunities/${opportunityId}/settings`"
               :class="[
                  'px-4 py-2 text-sm font-medium border-b-2 transition-colors',
                  resolvedActiveTab === 'settings'
                     ? 'border-blue-600 text-blue-600'
                     : 'border-transparent text-gray-600 hover:text-gray-900',
               ]"
            >
               {{ t('opportunities.settings') }}
            </router-link>
         </div>
      </div>
   </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, computed, nextTick } from 'vue';
import { supabase } from '../../lib/supabase';
import { createAccount, listAccounts } from '../../api/account';
import { useI18n } from '../../i18n/useI18n';
import { useApiQuery } from '../../composables/useApiQuery';

const { t, te } = useI18n();
const { fetchApiJson } = useApiQuery();

import { useRouter, useRoute } from 'vue-router';

const router = useRouter();
const route = useRoute();
const props = defineProps<{
   opportunityId: string;
   activeTab:
      | 'source'
      | 'account'
      | 'quote'
      | 'preview'
      | 'send'
      | 'pipeline'
      | 'documents'
      | 'invoices'
      | 'actions'
      | 'chat'
      | 'settings';
}>();

const validTabs = new Set([
   'source',
   'account',
   'quote',
   'preview',
   'send',
   'pipeline',
   'documents',
   'invoices',
   'actions',
   'chat',
   'settings',
]);

const resolvedActiveTab = computed(() => {
   const path = route.path || '';
   const lastSegment = path.split('/').pop() || '';
   return validTabs.has(lastSegment) ? lastSegment : props.activeTab;
});

const opportunityData = ref<any>(null);
const hasPdf = ref(false);
const recentOpportunities = ref<any[]>([]);
const loadingRecent = ref(false);
const selectedOpportunityId = ref('');
const showDropdown = ref(false);
const searchQuery = ref('');
const searchResults = ref<any[]>([]);
const loadingSearch = ref(false);
let searchTimeout: number | undefined;
const searchInput = ref<HTMLInputElement | null>(null);

const getStageLabel = (stage?: string) => {
   const resolvedStage = stage || 'NEW_LEAD';
   const key = `opportunities.stages.${resolvedStage}` as const;
   return te(key) ? t(key) : resolvedStage.replace(/_/g, ' ');
};

const getSourceLabel = (source?: string) => {
   if (!source) return t('opportunities.notAvailable');
   const normalized = source.toLowerCase();
   const key = `opportunities.sourceTypes.${normalized}` as const;
   return te(key) ? t(key) : source;
};

const createNewOpportunity = async () => {
   try {
      // Get current user
      const {
         data: { user },
      } = await supabase.auth.getUser();
      if (!user) {
         console.error('[OpportunityHeader] No authenticated user');
         return;
      }

      // Find or create a default account
      let accountId: string | null = null;

      // Try to find an existing "Default Account" for this user
      const accounts = await listAccounts();
      const existingAccount = accounts.find((account) => account.name === 'Default Account');

      if (existingAccount) {
         accountId = existingAccount.id;
      } else {
         // Create a default account
         const newAccount = await createAccount({
            name: 'Default Account',
         });
         accountId = newAccount.id;
      }

      // Create a new opportunity
      const { data, error } = await (supabase.from('opportunity') as any)
         .insert({
            name: '',
            stage: 'NEW_LEAD',
            source: 'user_form',
            account_id: accountId,
            owner_user_id: user.id,
         })
         .select()
         .single();

      if (error) {
         console.error('[OpportunityHeader] Error creating opportunity:', error);
         return;
      }

      if (data) {
         // Navigate to the new opportunity
         router.push(`/opportunities/${(data as any).id}/source`);
         // Reload recent opportunities to include the new one
         await loadRecentOpportunities();
      }
   } catch (error) {
      console.error('[OpportunityHeader] Error creating new opportunity:', error);
   }
};

const selectOpportunity = (opportunityId: string) => {
   showDropdown.value = false;
   if (opportunityId && opportunityId !== props.opportunityId) {
      router.push(`/opportunities/${opportunityId}/source`);
   }
};

const loadOpportunity = async () => {
   try {
      if (props.opportunityId === 'new') {
         opportunityData.value = null;
         hasPdf.value = false;
         selectedOpportunityId.value = '';
         return;
      }

      const result = await fetchApiJson<{ status: string; opportunity?: any }>('opportunity', {
         opportunity_id: props.opportunityId,
      });

      if (result?.status !== 'ok' || !result?.opportunity) {
         throw new Error('Failed loading opportunity');
      }

      const opp = result.opportunity;
      opportunityData.value = {
         name: opp.name,
         stage: opp.stage,
         source: opp.source,
      };
      selectedOpportunityId.value = props.opportunityId;

      // Check for PDF
      const { data: docData } = await supabase
         .from('document')
         .select('storage_key')
         .eq('opportunity_id', props.opportunityId)
         .eq('type', 'QUOTE')
         .not('storage_key', 'is', null)
         .limit(1);

      hasPdf.value = !!(docData && docData.length > 0);
   } catch (error) {
      console.error('[OpportunityHeader] Error loading opportunity:', error);
   }
};

const refreshOpportunity = async () => {
   await loadOpportunity();
   await loadRecentOpportunities();
};

const loadRecentOpportunities = async () => {
   loadingRecent.value = true;
   try {
      const { data, error } = await supabase
         .from('opportunity')
         .select('id, name, updated_at, source')
         .neq('stage', 'CLOSED_WON')
         .order('updated_at', { ascending: false })
         .limit(50);

      if (!error && data) {
         recentOpportunities.value = data;
         //console.log('[OpportunityHeader] Loaded recent opportunities:', data);
      }
   } catch (error) {
      console.error('[OpportunityHeader] Error loading recent opportunities:', error);
   } finally {
      loadingRecent.value = false;
   }
};

const searchOpportunities = async (query: string) => {
   if (!query.trim()) {
      searchResults.value = [];
      loadingSearch.value = false;
      return;
   }
   loadingSearch.value = true;
   try {
      const { data, error } = await supabase
         .from('opportunity')
         .select('id, name, updated_at, source')
         .neq('stage', 'CLOSED_WON')
         .ilike('name', `%${query.trim()}%`)
         .order('updated_at', { ascending: false })
         .limit(50);

      if (!error && data) {
         searchResults.value = data;
      } else {
         searchResults.value = [];
      }
   } catch (error) {
      console.error('[OpportunityHeader] Error searching opportunities:', error);
      searchResults.value = [];
   } finally {
      loadingSearch.value = false;
   }
};

const filteredOpportunities = computed(() => {
   return searchQuery.value.trim() ? searchResults.value : recentOpportunities.value;
});

const formatDate = (dateString: string) => {
   if (!dateString) return '';
   const date = new Date(dateString);
   const now = new Date();
   const diffMs = now.getTime() - date.getTime();
   const diffMins = Math.floor(diffMs / 60000);
   const diffHours = Math.floor(diffMs / 3600000);
   const diffDays = Math.floor(diffMs / 86400000);

   if (diffMins < 60) return `${diffMins}m ago`;
   if (diffHours < 24) return `${diffHours}h ago`;
   if (diffDays < 7) return `${diffDays}d ago`;
   return date.toLocaleDateString();
};

onMounted(() => {
   loadOpportunity();
   loadRecentOpportunities();
   document.addEventListener('click', handleClickOutside);
});

onUnmounted(() => {
   document.removeEventListener('click', handleClickOutside);
});

watch(
   () => props.opportunityId,
   () => {
      loadOpportunity();
   }
);

watch(
   () => showDropdown.value,
   async (isOpen) => {
      if (isOpen) {
         await nextTick();
         searchInput.value?.focus();
      }
   }
);

watch(
   () => searchQuery.value,
   (value) => {
      if (searchTimeout) {
         window.clearTimeout(searchTimeout);
      }
      searchTimeout = window.setTimeout(() => {
         searchOpportunities(value);
      }, 250);
   }
);

const handleClickOutside = (event: MouseEvent) => {
   const target = event.target as HTMLElement;
   if (!target.closest('.relative')) {
      showDropdown.value = false;
   }
};

defineExpose({
   refreshOpportunity,
});
</script>
