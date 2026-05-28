<template>
   <div>
      <ProductsSubHeader>
         <template #actions>
            <ActionButton v-if="userRole === 'admin'" to="/vendors/new" variant="dark">
               {{ t('vendors.new') }}
            </ActionButton>
         </template>
      </ProductsSubHeader>
      <div class="list-page-shell">
         <div v-if="errorMessage" class="mb-4 p-4 bg-red-100 text-red-700 rounded-lg">
            {{ errorMessage }}
         </div>

         <div class="list-card">
            <div v-if="isLoading" class="p-6 text-center text-gray-500">
               {{ t('vendors.loading') }}
            </div>
            <div v-else-if="vendors.length === 0" class="p-6 text-center text-gray-500">
               {{ t('vendors.empty') }}
            </div>
            <div v-else class="list-table-wrap">
               <table class="list-table">
                  <thead>
                     <tr>
                        <th>
                           {{ t('vendors.columns.name') }}
                        </th>
                        <th>
                           {{ t('vendors.columns.email') }}
                        </th>
                        <th>
                           {{ t('vendors.columns.phone') }}
                        </th>
                        <th>
                           {{ t('vendors.columns.website') }}
                        </th>
                        <th class="list-table-right">
                           {{ t('vendors.columns.brands') }}
                        </th>
                        <th class="list-table-right">
                           {{ t('vendors.columns.families') }}
                        </th>
                        <th class="list-table-right">
                           {{ t('vendors.columns.products') }}
                        </th>
                        <th>
                           {{ t('vendors.columns.created') }}
                        </th>
                     </tr>
                  </thead>
                  <tbody>
                     <tr
                        v-for="vendor in vendors"
                        :key="vendor.id"
                        @click="$router.push(`/vendors/${vendor.id}`)"
                     >
                        <td class="font-medium text-gray-900">
                           {{ vendor.name }}
                        </td>
                        <td class="list-table-muted">
                           {{ vendor.email || '-' }}
                        </td>
                        <td class="list-table-muted">
                           {{ vendor.phone || '-' }}
                        </td>
                        <td class="list-table-wrap-text">
                           <a
                              v-if="vendor.website"
                              :href="vendor.website"
                              target="_blank"
                              rel="noreferrer"
                              @click.stop
                              class="list-table-link"
                           >
                              {{ vendor.website }}
                           </a>
                           <span v-else class="list-table-muted">-</span>
                        </td>
                        <td class="list-table-muted list-table-right">
                           {{ formatNumber(vendor.brand_count) }}
                        </td>
                        <td class="list-table-muted list-table-right">
                           {{ formatNumber(vendor.family_count) }}
                        </td>
                        <td class="list-table-muted list-table-right">
                           {{ formatNumber(vendor.product_count) }}
                        </td>
                        <td class="list-table-muted">
                           {{ formatDate(vendor.created_at) }}
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
import { onMounted, ref } from 'vue';
import ProductsSubHeader from '../products/ProductsSubHeader.vue';
import ActionButton from '../common/ActionButton.vue';
import { listVendors, type Vendor } from '../../api/vendor';
import { useI18n } from '../../i18n/useI18n';
import { useAuthWithProfile } from '../../composables/useAuthWithProfile';

const { userRole } = useAuthWithProfile();

const vendors = ref<Vendor[]>([]);
const isLoading = ref(false);
const errorMessage = ref('');
const { t } = useI18n();

const formatDate = (dateString?: string) => {
   if (!dateString) return '-';
   try {
      return new Date(dateString).toLocaleDateString('en-US', {
         year: 'numeric',
         month: 'short',
         day: 'numeric',
      });
   } catch {
      return dateString;
   }
};

const { locale } = useI18n();

const formatNumber = (number?: number) => {
   if (number === undefined || number === null) return '0';

   // Use the current locale directly from i18n
   return number.toLocaleString(locale.value || 'fr-FR', {
      useGrouping: true,
      minimumFractionDigits: 0,
      maximumFractionDigits: 2,
   });
};

const loadVendors = async () => {
   isLoading.value = true;
   errorMessage.value = '';

   try {
      vendors.value = await listVendors();
   } catch (error) {
      errorMessage.value = t('vendors.errors.generic', {
         message: error instanceof Error ? error.message : t('vendors.errors.unknown'),
      });
   } finally {
      isLoading.value = false;
   }
};

onMounted(() => {
   loadVendors();
});
</script>
