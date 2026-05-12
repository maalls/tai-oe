<template>
   <div class="space-y-6">
      <div class="flex items-center justify-between">
         <div>
            <h2 class="text-2xl font-semibold text-gray-900">Brands</h2>
            <p class="text-sm text-gray-500">Manage brands and their families</p>
         </div>
      </div>

      <div v-if="errorMessage" class="rounded-lg bg-red-50 text-red-700 p-4">
         {{ errorMessage }}
      </div>

      <div v-if="isLoading" class="text-gray-500">Loading...</div>

      <div v-else class="space-y-6">
         <div
            v-for="brand in brands"
            :key="brand.id"
            class="bg-white rounded-lg border border-gray-200 shadow-sm"
         >
            <div class="px-6 py-4 border-b border-gray-200">
               <div class="flex items-start justify-between gap-4">
                  <div>
                     <h3 class="text-lg font-semibold text-gray-900">{{ brand.name }}</h3>
                     <div class="text-sm text-gray-500 space-y-1 mt-1">
                        <div v-if="brand.website">
                           <a
                              :href="brand.website"
                              target="_blank"
                              rel="noreferrer"
                              class="text-blue-600 hover:underline"
                           >
                              {{ brand.website }}
                           </a>
                        </div>
                        <div v-if="brand.email">{{ brand.email }}</div>
                        <div v-if="brand.phone">{{ brand.phone }}</div>
                     </div>
                  </div>
                  <div class="text-xs text-gray-400">
                     {{ formatDate(brand.created_at) }}
                  </div>
               </div>
            </div>
            <div class="p-6">
               <h4 class="text-sm font-semibold text-gray-700 mb-3">Families</h4>
               <div v-if="familiesByBrand[brand.id]?.length" class="overflow-x-auto">
                  <table class="w-full text-sm">
                     <thead class="bg-gray-100 text-gray-700">
                        <tr>
                           <th class="px-4 py-2 text-left">Name</th>
                           <th class="px-4 py-2 text-left">Type</th>
                        </tr>
                     </thead>
                     <tbody class="divide-y divide-gray-200">
                        <tr
                           v-for="family in familiesByBrand[brand.id]"
                           :key="family.id"
                           class="hover:bg-gray-50"
                        >
                           <td class="px-4 py-2 text-gray-900">{{ family.name }}</td>
                           <td class="px-4 py-2 text-gray-600">{{ family.type }}</td>
                        </tr>
                     </tbody>
                  </table>
               </div>
               <div v-else class="text-sm text-gray-500">No families linked.</div>
            </div>
         </div>
         <div v-if="!brands.length && !isLoading" class="text-gray-500">No brands found.</div>
      </div>
   </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue';
import { useCmsData } from './useCmsData';
import type { Family } from './useCmsData';

const { brands, families, isLoading, errorMessage, loadData } = useCmsData();

const familiesByBrand = computed<Record<string, Family[]>>(() => {
   return families.value.reduce(
      (acc, family) => {
         if (!acc[family.brand_id]) acc[family.brand_id] = [];
         const bucket = acc[family.brand_id];
         if (bucket) bucket.push(family);
         return acc;
      },
      {} as Record<string, Family[]>
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
