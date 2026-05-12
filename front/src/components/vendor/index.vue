<template>
   <div>
      <ProductsSubHeader />
      <div class="p-6 max-w-7xl mx-auto">
         <div class="flex flex-col md:flex-row md:items-center md:justify-between mb-6">
            <div>
               <h1 class="text-3xl font-bold text-gray-900">{{ t('vendors.title') }}</h1>
            </div>
            <div class="mt-4 md:mt-0 flex gap-2">
               <router-link
                  to="/vendors/new"
                  class="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg font-medium text-sm"
               >
                  {{ t('vendors.new') }}
               </router-link>
            </div>
         </div>

         <div v-if="errorMessage" class="mb-4 p-4 bg-red-100 text-red-700 rounded-lg">
            {{ errorMessage }}
         </div>

         <div class="bg-white rounded-lg shadow overflow-hidden">
            <div v-if="isLoading" class="p-6 text-center text-gray-500">
               {{ t('vendors.loading') }}
            </div>
            <div v-else-if="vendors.length === 0" class="p-6 text-center text-gray-500">
               {{ t('vendors.empty') }}
            </div>
            <table v-else class="w-full">
               <thead class="bg-gray-50 border-b">
                  <tr>
                     <th class="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">
                        {{ t('vendors.columns.name') }}
                     </th>
                     <th class="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">
                        {{ t('vendors.columns.email') }}
                     </th>
                     <th class="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">
                        {{ t('vendors.columns.phone') }}
                     </th>
                     <th class="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">
                        {{ t('vendors.columns.website') }}
                     </th>
                     <th class="px-6 py-3 text-right text-xs font-medium text-gray-700 uppercase">
                        {{ t('vendors.columns.brands') }}
                     </th>
                     <th class="px-6 py-3 text-right text-xs font-medium text-gray-700 uppercase">
                        Families
                     </th>
                     <th class="px-6 py-3 text-right text-xs font-medium text-gray-700 uppercase">
                        Products
                     </th>
                     <th class="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">
                        {{ t('vendors.columns.created') }}
                     </th>
                  </tr>
               </thead>
               <tbody class="divide-y">
                  <tr
                     v-for="vendor in vendors"
                     :key="vendor.id"
                     @click="$router.push(`/vendors/${vendor.id}`)"
                     class="hover:bg-gray-50 cursor-pointer"
                  >
                     <td class="px-6 py-4 text-sm font-medium text-gray-900">
                        {{ vendor.name }}
                     </td>
                     <td class="px-6 py-4 text-sm text-gray-600">
                        {{ vendor.email || '-' }}
                     </td>
                     <td class="px-6 py-4 text-sm text-gray-600">
                        {{ vendor.phone || '-' }}
                     </td>
                     <td class="px-6 py-4 text-sm text-blue-600">
                        <a
                           v-if="vendor.website"
                           :href="vendor.website"
                           target="_blank"
                           rel="noreferrer"
                           @click.stop
                        >
                           {{ vendor.website }}
                        </a>
                        <span v-else class="text-gray-600">-</span>
                     </td>
                     <td class="px-6 py-4 text-sm text-gray-600 text-right">
                        {{ vendor.brand_count ?? 0 }}
                     </td>
                     <td class="px-6 py-4 text-sm text-gray-600 text-right">
                        {{ vendor.family_count ?? 0 }}
                     </td>
                     <td class="px-6 py-4 text-sm text-gray-600 text-right">
                        {{ vendor.product_count ?? 0 }}
                     </td>
                     <td class="px-6 py-4 text-sm text-gray-600">
                        {{ formatDate(vendor.created_at) }}
                     </td>
                  </tr>
               </tbody>
            </table>
         </div>
      </div>
   </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import ProductsSubHeader from '../products/ProductsSubHeader.vue';
import { supabase } from '../../lib/supabase';
import { useAuth } from '../../stores/auth';
import { useI18n } from '../../i18n/useI18n';

interface Vendor {
   id: string;
   name: string;
   email?: string | null;
   phone?: string | null;
   website?: string | null;
   created_at?: string;
   updated_at?: string;
   brand_count?: number | null;
   family_count?: number | null;
   product_count?: number | null;
}

type VendorWithCounts = Vendor & {
   brand?: Array<{
      count: number;
      family?: Array<{ count: number; product_family?: Array<{ count: number }> }>;
   }> | null;
};

const vendors = ref<Vendor[]>([]);
const isLoading = ref(false);
const errorMessage = ref('');
const { user } = useAuth();
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

const loadVendors = async () => {
   isLoading.value = true;
   errorMessage.value = '';

   try {
      if (!user.value?.id) {
         errorMessage.value = t('vendors.errors.notAuthenticated');
         return;
      }

      // Fetch vendors with brand count
      const { data: vendorData, error: vendorError } = await supabase
         .from('vendor')
         .select('id, name, email, phone, website, created_at, brand(count)')
         .order('created_at', { ascending: false });

      if (vendorError) {
         errorMessage.value = t('vendors.errors.loadFailed', { message: vendorError.message });
         return;
      }

      // Fetch all brands to get vendor mapping
      const { data: brandsData, error: brandsError } = await supabase
         .from('brand')
         .select('id, vendor_id');

      if (brandsError) {
         console.error('Failed to fetch brands:', brandsError);
      }

      // Build brand to vendor mapping
      const brandToVendor: Record<string, string> = {};
      if (brandsData) {
         brandsData.forEach((brand: any) => {
            if (brand.id && brand.vendor_id) {
               brandToVendor[brand.id] = brand.vendor_id;
            }
         });
      }

      // Fetch all families with their brand_id
      const { data: familiesData, error: familiesError } = await supabase
         .from('family')
         .select('id, brand_id');

      if (familiesError) {
         console.error('Failed to fetch families:', familiesError);
      }

      // Build family to brand mapping and count families per vendor
      const familyToBrand: Record<string, string> = {};
      const familyCountByVendor: Record<string, number> = {};

      if (familiesData) {
         familiesData.forEach((family: any) => {
            if (family.id && family.brand_id) {
               familyToBrand[family.id] = family.brand_id;
               const vendorId = brandToVendor[family.brand_id];
               if (vendorId) {
                  familyCountByVendor[vendorId] = (familyCountByVendor[vendorId] || 0) + 1;
               }
            }
         });
      }

      // Fetch all product_families with their family_id
      const { data: productFamiliesData, error: productFamiliesError } = await supabase
         .from('product_family')
         .select('family_id');

      if (productFamiliesError) {
         console.error('Failed to fetch product families:', productFamiliesError);
      }

      // Count products per vendor
      const productCountByVendor: Record<string, number> = {};

      if (productFamiliesData) {
         productFamiliesData.forEach((productFamily: any) => {
            if (productFamily.family_id) {
               const brandId = familyToBrand[productFamily.family_id];
               if (brandId) {
                  const vendorId = brandToVendor[brandId];
                  if (vendorId) {
                     productCountByVendor[vendorId] = (productCountByVendor[vendorId] || 0) + 1;
                  }
               }
            }
         });
      }

      vendors.value = ((vendorData as VendorWithCounts[]) || []).map((vendor) => {
         const brandCount =
            Array.isArray(vendor.brand) && vendor.brand[0]?.count != null
               ? vendor.brand[0].count
               : 0;

         return {
            ...vendor,
            brand_count: brandCount,
            family_count: familyCountByVendor[vendor.id] || 0,
            product_count: productCountByVendor[vendor.id] || 0,
         };
      });
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
