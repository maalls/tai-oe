<template>
   <div class="opportunity-page">
      <OpportunityHeader :opportunityId="opportunityId" activeTab="invoices" />

      <div v-if="errorMessage" class="m-4 p-4 bg-red-100 text-red-700 rounded-lg">
         {{ errorMessage }}
      </div>

      <div v-if="isLoading" class="flex justify-center items-center py-12">
         <div class="text-gray-500">{{ t('opportunities.loadingInvoices') }}</div>
      </div>

      <div v-else class="opportunity-page-section m-4 bg-white rounded-lg shadow">
         <div class="p-6">
            <div class="flex items-center justify-between mb-6">
               <h2 class="text-xl font-semibold text-gray-900">
                  {{ t('opportunities.invoicesTitle') }}
               </h2>
               <span class="text-sm text-gray-500">
                  {{ invoices.length }}
                  {{
                     invoices.length === 1
                        ? t('opportunities.invoiceSingular')
                        : t('opportunities.invoicePlural')
                  }}
               </span>
            </div>

            <div v-if="invoices.length === 0" class="text-center py-12 text-gray-500">
               {{ t('opportunities.noInvoicesFound') }}
            </div>

            <div v-else class="overflow-x-auto">
               <table class="min-w-full divide-y divide-gray-200">
                  <thead class="bg-gray-50">
                     <tr>
                        <th
                           class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                        >
                           {{ t('opportunities.referenceLabel') }}
                        </th>
                        <th
                           class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                        >
                           {{ t('opportunities.statusLabel') }}
                        </th>
                        <th
                           class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                        >
                           {{ t('opportunities.amountLabel') }}
                        </th>
                        <th
                           class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                        >
                           {{ t('opportunities.issuedDateLabel') }}
                        </th>
                        <th
                           class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                        >
                           {{ t('opportunities.actions') }}
                        </th>
                     </tr>
                  </thead>
                  <tbody class="bg-white divide-y divide-gray-200">
                     <tr
                        v-for="invoice in invoices"
                        :key="invoice.id"
                        class="hover:bg-gray-50 cursor-pointer"
                        @click="openInvoiceDetail(invoice.id)"
                     >
                        <td class="px-6 py-4 whitespace-nowrap">
                           <div class="text-sm font-medium text-blue-600 hover:text-blue-800">
                              {{ invoice.external_ref || invoice.title }}
                           </div>
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap">
                           <span
                              class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
                              :class="getStatusColor(invoice.status)"
                           >
                              {{ formatStatus(invoice.status) }}
                           </span>
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap">
                           <div class="text-sm font-medium text-gray-900">
                              {{ formatCurrency(invoice.total_incl_tax, invoice.currency) }}
                           </div>
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap">
                           <div class="text-sm text-gray-600">
                              {{ formatDate(invoice.issued_at) }}
                           </div>
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                           <div class="flex gap-2" @click.stop>
                              <a
                                 v-if="invoice.storage_key"
                                 :href="getInvoiceUrl(invoice.storage_key)"
                                 target="_blank"
                                 class="text-blue-600 hover:text-blue-800"
                              >
                                 {{ t('opportunities.download') }}
                              </a>
                              <button
                                 @click="sendInvoice(invoice)"
                                 class="text-blue-600 hover:text-blue-800"
                              >
                                 {{ t('opportunities.send') }}
                              </button>
                           </div>
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
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { listOpportunityDocuments } from '../../../../api/document';
import OpportunityHeader from '../../OpportunityHeader.vue';
import { useI18n } from '../../../../i18n/useI18n';

const { t, te, locale } = useI18n();

const route = useRoute();
const router = useRouter();
const opportunityId = ref<string>(route.params.id as string);
const invoices = ref<any[]>([]);
const isLoading = ref(true);
const errorMessage = ref('');

const loadInvoices = async () => {
   try {
      const documents = await listOpportunityDocuments(opportunityId.value);
      invoices.value = documents
         .filter((document) => document.type === 'INVOICE')
         .sort((left, right) => {
            const leftTime = left.created_at ? new Date(left.created_at).getTime() : 0;
            const rightTime = right.created_at ? new Date(right.created_at).getTime() : 0;
            return rightTime - leftTime;
         });
   } catch (error: any) {
      errorMessage.value = error?.message || t('opportunities.failedToLoadInvoices');
      console.error('[InvoicesPage] Error loading invoices:', error);
   } finally {
      isLoading.value = false;
   }
};

const getStatusColor = (status: string) => {
   const colors: Record<string, string> = {
      DRAFT: 'bg-gray-100 text-gray-800',
      SENT: 'bg-blue-100 text-blue-800',
      RECEIVED: 'bg-blue-100 text-blue-800',
      PAID: 'bg-green-100 text-green-800',
      PARTIALLY_PAID: 'bg-yellow-100 text-yellow-800',
      OVERDUE: 'bg-red-100 text-red-800',
      DISPUTED: 'bg-orange-100 text-orange-800',
      CANCELLED: 'bg-red-100 text-red-800',
   };
   return colors[status] || 'bg-gray-100 text-gray-800';
};

const formatStatus = (status: string) => {
   const key = `opportunities.invoiceStatuses.${status}` as const;
   return te(key) ? t(key) : status.replace(/_/g, ' ');
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

const getInvoiceUrl = (storageKey: string) => {
   return `/api/documents/download/${storageKey}`;
};

const sendInvoice = async (invoice: any) => {
   // Navigate to invoice detail page where send modal is available
   openInvoiceDetail(invoice.id);
};

const openInvoiceDetail = (invoiceId: string) => {
   router.push({
      name: 'opportunity-invoice-detail',
      params: {
         id: opportunityId.value,
         invoiceId: invoiceId,
      },
   });
};

onMounted(() => {
   loadInvoices();
});
</script>
