<template>
   <div>
      <ProductsSubHeader />
      <div class="list-page-shell list-page-stack">
         <div v-if="errorMessage" class="rounded-lg bg-red-50 text-red-700 p-4">
            {{ errorMessage }}
         </div>

         <div v-if="isLoading" class="text-gray-500">{{ t('products.brand.loading') }}</div>

         <div v-else class="list-card">
            <div class="list-table-wrap">
               <table class="list-table">
                  <thead>
                     <tr>
                        <th>
                           {{ t('products.brand.columns.name') }}
                        </th>
                        <th>
                           {{ t('products.brand.columns.vendor') }}
                        </th>
                        <th>
                           {{ t('products.brand.columns.email') }}
                        </th>
                        <th>
                           {{ t('products.brand.columns.phone') }}
                        </th>
                        <th class="list-table-right">
                           {{ t('products.brand.columns.minimumMargin') }}
                        </th>
                        <th class="list-table-right">
                           {{ t('products.brand.columns.targetMargin') }}
                        </th>
                        <th class="list-table-right">
                           {{ t('products.brand.columns.families') }}
                        </th>
                        <th class="list-table-right">
                           {{ t('products.brand.columns.discounts') }}
                        </th>
                        <th class="list-table-right">
                           {{ t('products.brand.columns.products') }}
                        </th>
                        <th>
                           {{ t('products.brand.columns.created') }}
                        </th>
                     </tr>
                  </thead>
                  <tbody>
                     <tr
                        v-for="brand in brands"
                        :key="brand.id"
                        @click="
                           router.push({ name: 'vendor-brand-edit', params: { id: brand.id } })
                        "
                     >
                        <td class="font-medium">
                           <span class="list-table-link">{{ brand.name }}</span>
                        </td>
                        <td class="list-table-muted">{{ brand.vendor_name || '-' }}</td>
                        <td class="list-table-muted">{{ brand.email || '-' }}</td>
                        <td class="list-table-muted">{{ brand.phone || '-' }}</td>
                        <td class="list-table-muted list-table-right">
                           {{ brand.minimum_margin != null ? brand.minimum_margin + '%' : '-' }}
                        </td>
                        <td class="list-table-muted list-table-right">
                           {{ brand.target_margin != null ? brand.target_margin + '%' : '-' }}
                        </td>
                        <td class="list-table-right" @click.stop>
                           <router-link
                              :to="{ path: '/vendors/family', query: { brand_id: brand.id } }"
                              class="list-table-link"
                           >
                              {{ familiesByBrand[brand.id]?.length || 0 }}
                           </router-link>
                        </td>
                        <td class="list-table-right" @click.stop>
                           <router-link
                              :to="{
                                 path: '/vendors/family',
                                 query: { brand_id: brand.id, discount_only: 'true' },
                              }"
                              class="list-table-link"
                           >
                              {{ familiesWithDiscountByBrand[brand.id]?.length || 0 }}
                           </router-link>
                        </td>
                        <td class="list-table-muted list-table-right">
                           {{
                              productCountByBrand[brand.id]
                                 ? productCountByBrand[brand.id].toLocaleString(
                                      locale.value || 'fr-FR'
                                   )
                                 : '0'
                           }}
                        </td>
                        <td class="list-table-muted">
                           {{ formatDate(brand.created_at) }}
                        </td>
                     </tr>
                  </tbody>
               </table>
            </div>
            <div v-if="!brands.length && !isLoading" class="p-6 text-center text-gray-500">
               {{ t('products.brand.noBrands') }}
            </div>
         </div>
      </div>
   </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import ProductsSubHeader from './ProductsSubHeader.vue';
import { useBrandFamilyData } from './useBrandFamilyData';
import { useI18n } from '../../i18n/useI18n';

const router = useRouter();
const { t, locale } = useI18n();

const { brands, families, isLoading, errorMessage, loadData } = useBrandFamilyData();

const familiesByBrand = computed(() => {
   return families.value.reduce(
      (acc, family) => {
         if (!acc[family.brand_id]) acc[family.brand_id] = [];
         acc[family.brand_id]!.push(family);
         return acc;
      },
      {} as Record<string, typeof families.value>
   );
});

const familiesWithDiscountByBrand = computed(() => {
   return families.value.reduce(
      (acc, family) => {
         if (typeof family.discount === 'number' && family.discount > 0) {
            if (!acc[family.brand_id]) acc[family.brand_id] = [];
            acc[family.brand_id]!.push(family);
         }
         return acc;
      },
      {} as Record<string, typeof families.value>
   );
});

const productCountByBrand = computed(() => {
   return families.value.reduce(
      (acc, family) => {
         acc[family.brand_id] = (acc[family.brand_id] || 0) + (family.product_family_count || 0);
         return acc;
      },
      {} as Record<string, number>
   );
});

const formatDate = (dateString?: string | null) => {
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

onMounted(() => {
   loadData();
});
</script>
