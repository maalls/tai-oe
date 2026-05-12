<template>
   <div class="bg-white rounded-lg shadow overflow-hidden">
      <div v-if="loading" class="p-6 text-center text-gray-600">Loading products...</div>
      <div v-else-if="products.length === 0" class="p-6 text-center text-gray-600">
         No products found
      </div>
      <div v-else class="overflow-x-auto">
         <div class="px-6 py-3 text-sm text-gray-600 border-b border-gray-200 bg-white">
            <template v-if="isUsingSearch">
               {{ products.length }} result{{ products.length > 1 ? 's' : '' }}
            </template>
            <template v-else> Showing {{ products.length }} of {{ totalCount }} products </template>
         </div>
         <table class="w-full">
            <thead class="bg-gray-50 border-b border-gray-200">
               <tr>
                  <th class="px-6 py-3 text-left text-sm font-semibold text-gray-900">
                     Ref. Ciale
                  </th>
                  <th class="px-6 py-3 text-left text-sm font-semibold text-gray-900">Brand</th>
                  <th class="px-6 py-3 text-left text-sm font-semibold text-gray-900">
                     Description
                  </th>
                  <th class="px-6 py-3 text-left text-sm font-semibold text-gray-900">Families</th>
                  <th class="px-6 py-3 text-right text-sm font-semibold text-gray-900">Price</th>
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
               {{ products.length }} result{{ products.length > 1 ? 's' : '' }}
            </template>
            <template v-else> Showing {{ products.length }} of {{ totalCount }} products </template>
         </div>
         <button
            v-if="nextOffset && !isUsingSearch"
            @click="loadMore"
            :disabled="loading"
            class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 transition"
         >
            Load More
         </button>
      </div>
   </div>
</template>

<script setup lang="ts">
import { RouterLink } from 'vue-router';

defineProps<{
   products: any[];
   loading: boolean;
   totalCount: number;
   nextOffset: string | number | null;
   isUsingSearch: boolean;
   getBrandDisplay: (product: any) => string;
   getFamilyTags: (
      product: any
   ) => { label: string; hasDiscount: boolean; isNetPrice: boolean; href: string }[];
   getDiscountedPrice: (product: any) => { original: number; discounted: number } | null;
   formatPrice: (price: string | number) => string;
   loadMore: () => void;
}>();
</script>
