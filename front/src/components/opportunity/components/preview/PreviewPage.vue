<template>
   <div class="opportunity-page">
      <OpportunityHeader :opportunityId="opportunityId" activeTab="preview" />

      <div v-if="errorMessage" class="mb-4 p-4 bg-red-100 text-red-700 rounded-lg">
         {{ errorMessage }}
      </div>

      <div v-if="successMessage" class="mb-4 p-4 bg-green-100 text-green-700 rounded-lg">
         {{ successMessage }}
      </div>

      <div v-if="isLoading" class="flex justify-center items-center py-12">
         <div class="text-gray-500">{{ t('opportunities.loadingDots') }}</div>
      </div>

      <div v-else-if="pdfFilename" class="opportunity-page-section bg-white rounded-lg shadow m-4">
         <div class="flex items-center justify-between gap-2 px-4 py-3 border-b">
            <div class="flex items-center gap-2">
               <button
                  type="button"
                  class="px-3 py-2 text-sm bg-red-600 text-white rounded hover:bg-red-700 disabled:bg-gray-300 disabled:text-gray-600"
                  @click="deleteQuotePdf"
                  :disabled="isDeleting"
               >
                  {{ isDeleting ? t('common.deleting') || 'Deleting...' : t('common.delete') }}
               </button>
            </div>
            <button
               type="button"
               class="px-3 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
               @click="goToSend"
            >
               {{ t('opportunities.prepare_email') }}
            </button>
         </div>
         <div style="height: calc(100vh - 180px)">
            <PdfViewer :pdfUrl="quoteDownloadUrl" />
         </div>
      </div>

      <div
         v-else
         class="opportunity-page-section bg-white rounded-lg shadow p-6 text-center text-gray-500"
      >
         {{ t('opportunities.noPdfAvailable') }}
      </div>
   </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { supabase } from '../../../../lib/supabase';
import OpportunityHeader from '../../OpportunityHeader.vue';
import PdfViewer from '../../../PdfViewer.vue';
import { useI18n } from '../../../../i18n/useI18n';

const { t } = useI18n();
const route = useRoute();
const opportunityId = route.params.id as string;
const router = useRouter();

const isLoading = ref(true);
const pdfFilename = ref<string | null>(null);
const quoteDocumentId = ref<string | null>(null);
const isDeleting = ref(false);
const errorMessage = ref('');
const successMessage = ref('');

const quoteDownloadUrl = computed(() => {
   return pdfFilename.value ? `/api/quotes/download/${pdfFilename.value}` : '';
});

const loadQuotePdf = async () => {
   isLoading.value = true;

   try {
      const { data, error } = await supabase
         .from('document')
         .select('id, storage_key')
         .eq('opportunity_id', opportunityId)
         .eq('type', 'QUOTE')
         .order('created_at', { ascending: false })
         .limit(1);

      if (error) {
         console.error('[PreviewPage] Error loading quote PDF:', error);
         return;
      }

      const latestDoc = data && data.length > 0 ? (data[0] as any) : null;
      if (latestDoc?.storage_key) {
         pdfFilename.value = latestDoc.storage_key;
         quoteDocumentId.value = latestDoc.id;
      }
   } catch (error) {
      console.error('[PreviewPage] Unexpected error:', error);
   } finally {
      isLoading.value = false;
   }
};

const deleteQuotePdf = async () => {
   if (!quoteDocumentId.value) return;

   if (!confirm('Are you sure you want to delete the generated PDF?')) {
      return;
   }

   isDeleting.value = true;
   errorMessage.value = '';
   successMessage.value = '';

   try {
      const { error } = await (supabase.from('document') as any)
         .update({ storage_key: null })
         .eq('id', quoteDocumentId.value);

      if (error) {
         throw new Error(error.message || 'Failed to delete PDF');
      }

      pdfFilename.value = null;
      successMessage.value = 'Quote PDF deleted successfully';
      setTimeout(() => {
         successMessage.value = '';
      }, 800);
      router.push(`/opportunities/${opportunityId}/quote`);
   } catch (error: any) {
      errorMessage.value = error?.message || 'Failed to delete PDF';
   } finally {
      isDeleting.value = false;
   }
};

const goToSend = () => {
   router.push(`/opportunities/${opportunityId}/send`);
};

onMounted(() => {
   loadQuotePdf();
});
</script>
