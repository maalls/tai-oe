<template>
   <div class="bg-white rounded-lg shadow overflow-hidden">
      <div class="px-6 py-3 text-sm text-gray-600 border-b border-gray-200 bg-white">
         <template v-if="isUsingSearch">
            {{ t('products.table.results', { count: totalCount }) }}
         </template>
         <template v-else>
            {{ t('products.table.showing', { count: products.length, total: totalCount }) }}
         </template>
      </div>
      <div class="px-6 py-3 bg-white border-b border-gray-200 flex justify-end">
         <PaginationControls
            :currentPage="currentPage"
            :totalPages="totalPages"
            :goToPage="goToPage"
         />
      </div>

      <div
         v-if="loading"
         class="min-h-105 p-6 flex items-center justify-center text-center text-gray-600 border-b border-gray-200"
      >
         {{ t('products.table.loading') }}
      </div>
      <div
         v-else-if="products.length === 0"
         class="min-h-80 p-6 flex items-center justify-center text-center text-gray-600"
      >
         {{ t('products.table.empty') }}
      </div>
      <div v-else class="overflow-x-auto">
         <table class="w-full">
            <thead class="bg-gray-50 border-b border-gray-200">
               <tr>
                  <th class="px-6 py-3 text-left text-sm font-semibold text-gray-900">
                     {{ t('products.table.columns.refciale') }}
                  </th>
                  <th class="px-6 py-3 text-left text-sm font-semibold text-gray-900">
                     {{ t('products.table.columns.brand') }}
                  </th>
                  <th class="px-6 py-3 text-left text-sm font-semibold text-gray-900">
                     {{ t('products.table.columns.description') }}
                  </th>
                  <th class="px-6 py-3 text-left text-sm font-semibold text-gray-900">
                     {{ t('products.table.columns.batch') }}
                  </th>
                  <th class="px-6 py-3 text-left text-sm font-semibold text-gray-900">
                     {{ t('products.table.columns.families') }}
                  </th>
                  <th class="px-6 py-3 text-right text-sm font-semibold text-gray-900">
                     {{ t('products.table.columns.price') }}
                  </th>
               </tr>
            </thead>
            <tbody class="divide-y divide-gray-200">
               <tr
                  v-for="product in products"
                  :key="product.id"
                  class="hover:bg-gray-50 transition"
               >
                  <td class="px-6 py-4 text-sm font-mono text-gray-900">
                     <RouterLink
                        :to="`/products/${product.id}`"
                        class="text-blue-600 hover:text-blue-700"
                     >
                        {{ product.refciale }}
                     </RouterLink>
                  </td>
                  <td class="px-6 py-4 text-sm text-gray-700">{{ getBrandDisplay(product) }}</td>
                  <td class="px-6 py-4 text-sm text-gray-600">{{ product.libelle240 }}</td>
                  <td class="px-6 py-4 text-sm text-gray-700">{{ product.batch ?? '-' }}</td>
                  <td class="px-6 py-4 text-sm text-gray-600">
                     <div v-if="getFamilyTags(product).length" class="flex flex-wrap gap-2">
                        <a
                           v-for="tag in getFamilyTags(product)"
                           :key="tag.label"
                           :href="tag.href"
                           class="rounded-full px-2 py-0.5 text-xs cursor-pointer hover:opacity-80"
                           :class="
                              tag.isNetPrice
                                 ? 'bg-green-100 text-emerald-700'
                                 : tag.hasDiscount
                                   ? 'bg-amber-100 text-amber-800'
                                   : 'bg-gray-100 text-gray-700'
                           "
                        >
                           {{ tag.label }}
                        </a>
                     </div>
                     <span v-else class="text-gray-400">-</span>
                  </td>
                  <td class="px-6 py-4 text-sm text-right text-gray-900">
                     <div v-if="getDiscountedPrice(product)">
                        <div class="text-gray-500 line-through">
                           {{ formatPrice(getDiscountedPrice(product)!.original) }}
                        </div>
                        <div class="font-semibold">
                           {{ formatPrice(getDiscountedPrice(product)!.discounted) }}
                        </div>
                     </div>
                     <div v-else class="font-semibold">{{ formatPrice(product.tarif) }}</div>
                  </td>
               </tr>
            </tbody>
         </table>
      </div>
      <div
         v-if="products.length > 0 && !loading"
         class="px-6 py-4 bg-gray-50 border-t border-gray-200 flex justify-between items-center"
      >
         <div class="text-sm text-gray-600">
            <template v-if="isUsingSearch">
               {{ t('products.table.results', { count: totalCount }) }}
            </template>
            <template v-else>
               {{ t('products.table.showing', { count: products.length, total: totalCount }) }}
            </template>
         </div>
         <PaginationControls
            :currentPage="currentPage"
            :totalPages="totalPages"
            :goToPage="goToPage"
         />
      </div>
   </div>
</template>

<script setup lang="ts">
import { RouterLink } from 'vue-router';
import { useI18n } from '../../../../i18n/useI18n';
import PaginationControls from './PaginationControls.vue';

const { t } = useI18n();

const props = defineProps<{
   products: any[];
   loading: boolean;
   totalCount: number;
   isUsingSearch: boolean;
   currentPage: number;
   totalPages: number;
   pageSize: number;
   getBrandDisplay: (product: any) => string;
   getFamilyTags: (
      product: any
   ) => { label: string; hasDiscount: boolean; isNetPrice: boolean; href: string }[];
   getDiscountedPrice: (product: any) => { original: number; discounted: number } | null;
   formatPrice: (price: string | number) => string;
   goToPage: (page: number) => void;
}>();
</script>
