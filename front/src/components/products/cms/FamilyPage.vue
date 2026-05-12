<template>
   <div class="space-y-6">
      <div class="flex items-center justify-between">
         <div>
            <h2 class="text-2xl font-semibold text-gray-900">{{ t('products.cms.family.title') }}</h2>
            <p class="text-sm text-gray-500">{{ t('products.cms.family.subtitle') }}</p>
         </div>
      </div>

      <div v-if="errorMessage" class="rounded-lg bg-red-50 text-red-700 p-4">
         {{ errorMessage }}
      </div>

      <div class="bg-white rounded-lg border border-gray-200 shadow-sm">
         <div v-if="isLoading" class="p-6 text-gray-500">{{ t('products.cms.family.loading') }}</div>
         <div v-else-if="!families.length" class="p-6 text-gray-500">{{ t('products.cms.family.noFamilies') }}</div>
         <div v-else class="overflow-x-auto">
            <table class="w-full text-sm">
               <thead class="bg-gray-100 text-gray-700">
                  <tr>
                     <th class="px-4 py-3 text-left">{{ t('products.cms.family.columns.name') }}</th>
                     <th class="px-4 py-3 text-left">{{ t('products.cms.family.columns.type') }}</th>
                     <th class="px-4 py-3 text-left">{{ t('products.cms.family.columns.brand') }}</th>
                  </tr>
               </thead>
               <tbody class="divide-y divide-gray-200">
                  <tr v-for="family in families" :key="family.id" class="hover:bg-gray-50">
                     <td class="px-4 py-3 text-gray-900">{{ family.name }}</td>
                     <td class="px-4 py-3 text-gray-600">{{ family.type }}</td>
                     <td class="px-4 py-3 text-gray-600">
                        {{ brandLookup[family.brand_id] || family.brand_id }}
                     </td>
                  </tr>
               </tbody>
            </table>
         </div>
      </div>
   </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue';
import { useCmsData } from './useCmsData';
import { useI18n } from '../../../i18n/useI18n';

const { brands, families, isLoading, errorMessage, loadData } = useCmsData();
const { t } = useI18n();

const brandLookup = computed<Record<string, string>>(() => {
   return brands.value.reduce(
      (acc, brand) => {
         acc[brand.id] = brand.name;
         return acc;
      },
      {} as Record<string, string>
   );
});

onMounted(() => {
   loadData();
});
</script>
