<template>
   <div class="p-6">
      <OpportunityHeader :opportunityId="opportunityId" activeTab="invoices" />

      <div v-if="errorMessage" class="mb-4 p-4 bg-red-100 text-red-700 rounded-lg">
         {{ errorMessage }}
      </div>

      <div v-if="isLoading" class="flex justify-center items-center py-12">
         <div class="text-gray-500">Loading invoices...</div>
      </div>

      <div v-else class="bg-white rounded-lg shadow">
         <div class="p-6">
            <div class="flex items-center justify-between mb-6">
               <h2 class="text-xl font-semibold text-gray-900">Invoices</h2>
               <span class="text-sm text-gray-500">
                  {{ invoices.length }}
                  {{ invoices.length === 1 ? 'invoice' : 'invoices' }}
               </span>
            </div>

            <div v-if="invoices.length === 0" class="text-center py-12 text-gray-500">
               No invoices found
            </div>

            <div v-else class="overflow-x-auto">
               <table class="min-w-full divide-y divide-gray-200">
                  <thead class="bg-gray-50">
                     <tr>
                        <th
                           class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                        >
                           Reference
                        </th>
                        <th
                           class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                        >
                           Status
                        </th>
                        <th
                           class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                        >
                           Amount
                        </th>
                        <th
                           class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                        >
                           Issued Date
                        </th>
                        <th
                           class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                        >
                           Actions
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
                                 Download
                              </a>
                              <button
                                 @click="sendInvoice(invoice)"
                                 class="text-blue-600 hover:text-blue-800"
                              >
                                 Send
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
import { listOpportunityInvoices } from '../../api/invoice';
import OpportunityHeader from '../opportunity/OpportunityHeader.vue';

const route = useRoute();
const router = useRouter();
const opportunityId = ref<string>(route.params.id as string);
const invoices = ref<any[]>([]);
const isLoading = ref(true);
const errorMessage = ref('');

const loadInvoices = async () => {
   try {
      invoices.value = await listOpportunityInvoices(opportunityId.value);
   } catch (error: any) {
      errorMessage.value = error?.message || 'Failed to load invoices';
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
   return status.replace(/_/g, ' ');
};

const formatCurrency = (value: number, currency: string = 'EUR') => {
   const amount = Number(value) || 0;
   return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
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
