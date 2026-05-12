<template>
   <div>
      <ProductsSubHeader />
      <div class="p-6 max-w-7xl mx-auto space-y-6">
         <div v-if="errorMessage" class="rounded-lg bg-red-50 text-red-700 p-4">
            {{ errorMessage }}
         </div>

         <div v-if="isLoading" class="text-gray-500">Loading...</div>

         <div v-else class="bg-white rounded-lg border border-gray-200 shadow overflow-hidden">
            <table class="w-full">
               <thead class="bg-gray-50 border-b">
                  <tr>
                     <th class="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">
                        Name
                     </th>
                     <th class="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">
                        Website
                     </th>
                     <th class="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">
                        Email
                     </th>
                     <th class="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">
                        Phone
                     </th>
                     <th class="px-6 py-3 text-right text-xs font-medium text-gray-700 uppercase">
                        Default Margin
                     </th>
                     <th class="px-6 py-3 text-right text-xs font-medium text-gray-700 uppercase">
                        Families
                     </th>
                     <th class="px-6 py-3 text-right text-xs font-medium text-gray-700 uppercase">
                        Discounts
                     </th>
                     <th class="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">
                        Created
                     </th>
                  </tr>
               </thead>
               <tbody class="divide-y">
                  <tr
                     v-for="brand in brands"
                     :key="brand.id"
                     class="hover:bg-gray-50 cursor-pointer"
                     @click="router.push({ name: 'vendor-brand-edit', params: { id: brand.id } })"
                  >
                     <td class="px-6 py-4 text-sm font-medium text-blue-600">
                        {{ brand.name }}
                     </td>
                     <td class="px-6 py-4 text-sm text-blue-600">
                        <a
                           v-if="brand.website"
                           :href="brand.website"
                           target="_blank"
                           rel="noreferrer"
                           class="hover:underline"
                           @click.stop
                        >
                           {{ brand.website }}
                        </a>
                        <span v-else class="text-gray-600">-</span>
                     </td>
                     <td class="px-6 py-4 text-sm text-gray-600">{{ brand.email || '-' }}</td>
                     <td class="px-6 py-4 text-sm text-gray-600">{{ brand.phone || '-' }}</td>
                     <td class="px-6 py-4 text-sm text-right text-gray-600">
                        {{ brand.minimum_margin ? brand.minimum_margin + '%' : '-' }}
                     </td>
                     <td class="px-6 py-4 text-sm text-right" @click.stop>
                        <router-link
                           :to="{ path: '/vendors/family', query: { brand_id: brand.id } }"
                           class="text-blue-600 hover:text-blue-800 hover:underline"
                        >
                           {{ familiesByBrand[brand.id]?.length || 0 }}
                        </router-link>
                     </td>
                     <td class="px-6 py-4 text-sm text-right" @click.stop>
                        <router-link
                           :to="{
                              path: '/vendors/family',
                              query: { brand_id: brand.id, discount_only: 'true' },
                           }"
                           class="text-blue-600 hover:text-blue-800 hover:underline"
                        >
                           {{ familiesWithDiscountByBrand[brand.id]?.length || 0 }}
                        </router-link>
                     </td>
                     <td class="px-6 py-4 text-sm text-gray-500">
                        {{ formatDate(brand.created_at) }}
                     </td>
                  </tr>
               </tbody>
            </table>
            <div v-if="!brands.length && !isLoading" class="p-6 text-center text-gray-500">
               No brands found.
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

const router = useRouter();

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
