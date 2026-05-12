<template>
   <div class="opportunity-page">
      <OpportunityHeader :opportunityId="opportunityId" activeTab="documents" />

      <div v-if="errorMessage" class="mb-4 p-4 bg-red-100 text-red-700 rounded-lg">
         {{ errorMessage }}
      </div>

      <div v-if="isLoading" class="flex justify-center items-center py-12">
         <div class="text-gray-500">{{ t('opportunities.loadingDocument') }}</div>
      </div>

      <div
         v-else-if="document"
         class="opportunity-page-section grid grid-cols-1 lg:grid-cols-3 gap-6"
      >
         <div class="lg:col-span-2 bg-white rounded-lg shadow p-4">
            <div class="mb-4 flex items-center justify-between">
               <h2 class="text-lg font-semibold text-gray-900">
                  <router-link
                     :to="`/opportunities/${opportunityId}/documents`"
                     class="text-blue-600 hover:text-blue-800 hover:underline"
                  >
                     {{ t('opportunities.documents') }}
                  </router-link>
                  <span class="mx-2 text-gray-400">/</span>
                  <span class="text-gray-900">
                     {{ document.title }}
                  </span>
               </h2>
               <div>
                  <a
                     v-if="document.storage_key"
                     :href="getDocumentUrl(document.storage_key)"
                     class="text-sm px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700"
                     download
                  >
                     {{ t('opportunities.download') }}
                  </a>
               </div>
            </div>

            <div v-if="isPdf" class="h-[70vh]">
               <iframe
                  v-if="document.storage_key"
                  :src="getDocumentUrl(document.storage_key) + '?inline=1'"
                  class="w-full h-full border border-gray-200 rounded"
               ></iframe>
               <div v-else class="text-gray-400">{{ t('opportunities.noFileAvailable') }}</div>
            </div>

            <div v-else-if="isImage" class="flex justify-center">
               <img
                  v-if="document.storage_key"
                  :src="getDocumentUrl(document.storage_key)"
                  :alt="document.title"
                  class="max-h-[70vh] object-contain rounded border border-gray-200"
               />
               <div v-else class="text-gray-400">{{ t('opportunities.noFileAvailable') }}</div>
            </div>

            <div v-else class="text-gray-600">
               <p class="mb-2">{{ t('opportunities.noInlinePreviewForType') }}</p>
               <a
                  v-if="document.storage_key"
                  :href="getDocumentUrl(document.storage_key)"
                  target="_blank"
                  class="text-blue-600 hover:text-blue-800 hover:underline"
               >
                  {{ t('opportunities.downloadFile') }}
               </a>
            </div>
         </div>

         <div class="bg-white rounded-lg shadow p-4">
            <h2 class="text-lg font-semibold text-gray-900 mb-4">
               {{ t('opportunities.details') }}
            </h2>
            <dl class="space-y-3 text-sm">
               <div>
                  <dt class="text-gray-500">{{ t('opportunities.documentTitle') }}</dt>
                  <dd class="text-gray-900 font-medium">{{ document.title }}</dd>
               </div>
               <div>
                  <dt class="text-gray-500">{{ t('opportunities.typeLabel') }}</dt>
                  <dd class="text-gray-900">{{ document.type }}</dd>
               </div>
               <div>
                  <dt class="text-gray-500">{{ t('opportunities.statusLabel') }}</dt>
                  <dd class="text-gray-900">{{ document.status }}</dd>
               </div>
               <div v-if="document.external_ref">
                  <dt class="text-gray-500">{{ t('opportunities.reference') }}</dt>
                  <dd class="text-gray-900">{{ document.external_ref }}</dd>
               </div>
               <div>
                  <dt class="text-gray-500">{{ t('opportunities.created') }}</dt>
                  <dd class="text-gray-900">{{ formatDate(document.created_at) }}</dd>
               </div>
               <div v-if="document.storage_key">
                  <dt class="text-gray-500">{{ t('opportunities.storageKey') }}</dt>
                  <dd class="text-gray-900 break-all">{{ document.storage_key }}</dd>
               </div>
               <div v-if="document.total_incl_tax">
                  <dt class="text-gray-500">{{ t('opportunities.total') }}</dt>
                  <dd class="text-gray-900">
                     {{ formatCurrency(document.total_incl_tax, document.currency) }}
                  </dd>
               </div>
            </dl>
         </div>
      </div>
   </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { supabase } from '../../../../lib/supabase';
import OpportunityHeader from '../../OpportunityHeader.vue';
import { useI18n } from '../../../../i18n/useI18n';

const { t } = useI18n();

const route = useRoute();
const opportunityId = route.params.id as string;
const documentId = route.params.documentId as string;

const isLoading = ref(true);
const errorMessage = ref('');
const document = ref<any | null>(null);

const getDocumentUrl = (storageKey: string) => {
   return `/api/documents/download/${storageKey}`;
};

const extension = computed(() => {
   const key = document.value?.storage_key || '';
   const parts = key.split('.');
   return parts.length > 1 ? parts[parts.length - 1].toLowerCase() : '';
});

const isPdf = computed(() => extension.value === 'pdf');
const isImage = computed(() => ['png', 'jpg', 'jpeg', 'gif', 'webp'].includes(extension.value));

const formatCurrency = (value: number, currency: string = 'EUR') => {
   const amount = Number(value) || 0;
   return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency,
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
   }).format(amount);
};

const formatDate = (dateString: string) => {
   if (!dateString) return '—';
   const date = new Date(dateString);
   return new Intl.DateTimeFormat('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
   }).format(date);
};

const loadDocument = async () => {
   try {
      const { data, error } = await supabase
         .from('document')
         .select(
            'id, opportunity_id, type, status, title, external_ref, currency, total_incl_tax, storage_key, created_at'
         )
         .eq('id', documentId)
         .eq('opportunity_id', opportunityId)
         .single();

      if (error) throw error;
      document.value = data;
   } catch (error: any) {
      errorMessage.value = error?.message || t('opportunities.failedToLoadDocument');
   } finally {
      isLoading.value = false;
   }
};

onMounted(loadDocument);
</script>
