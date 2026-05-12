<template>
   <div>
      <ProductsSubHeader />
      <div class="p-6 max-w-7xl mx-auto space-y-6">
         <div v-if="errorMessage" class="rounded-lg bg-red-50 text-red-700 p-4">
            {{ errorMessage }}
         </div>

         <div class="bg-white rounded-lg border border-gray-200 shadow-sm">
            <div class="border-b border-gray-200 px-4 py-3">
               <div class="flex flex-wrap items-end gap-4">
                  <div class="max-w-xs">
                     <label
                        class="block text-xs uppercase tracking-wide text-gray-400"
                        for="codeSearch"
                     >
                        code
                     </label>
                     <input
                        id="codeSearch"
                        v-model.trim="codeQuery"
                        placeholder="Type a family code"
                        class="mt-1 w-full rounded border border-gray-300 px-3 py-2 text-sm"
                        type="text"
                     />
                  </div>
                  <div class="max-w-xs">
                     <label
                        class="block text-xs uppercase tracking-wide text-gray-400"
                        for="typeSearch"
                     >
                        type
                     </label>
                     <input
                        id="typeSearch"
                        v-model.trim="typeQuery"
                        class="mt-1 w-full rounded border border-gray-300 px-3 py-2 text-sm"
                        type="text"
                        placeholder="Type a family type"
                     />
                  </div>
                  <div class="max-w-xs">
                     <label
                        class="block text-xs uppercase tracking-wide text-gray-400"
                        for="skuSearch"
                     >
                        product SKU
                     </label>
                     <input
                        id="skuSearch"
                        v-model.trim="skuQuery"
                        class="mt-1 w-full rounded border border-gray-300 px-3 py-2 text-sm"
                        type="text"
                        placeholder="Type a product SKU"
                     />
                  </div>
                  <div class="max-w-xs">
                     <label
                        class="block text-xs uppercase tracking-wide text-gray-400"
                        for="brandSelect"
                     >
                        Brand
                     </label>
                     <select
                        id="brandSelect"
                        v-model="brandIdFilter"
                        class="mt-1 w-full rounded border border-gray-300 px-3 py-2 text-sm"
                     >
                        <option :value="null">All brands</option>
                        <option v-for="brand in brands" :key="brand.id" :value="brand.id">
                           {{ brand.name }}
                        </option>
                     </select>
                  </div>
                  <label class="flex items-center gap-2 text-sm text-gray-600">
                     <input v-model="exactMatch" type="checkbox" class="h-4 w-4" />
                     Exact match
                  </label>
                  <label class="flex items-center gap-2 text-sm text-gray-600">
                     <input v-model="showDiscountOnly" type="checkbox" class="h-4 w-4" />
                     Discount only
                  </label>
               </div>
            </div>
            <div class="border-b border-gray-200 px-4 py-2">
               <div class="flex items-center justify-between gap-3">
                  <div class="inline-flex rounded-md border border-gray-300 overflow-hidden">
                     <button
                        type="button"
                        class="px-3 py-1 text-sm"
                        :class="
                           familyTypeTab === 'all'
                              ? 'bg-gray-800 text-white'
                              : 'bg-white text-gray-700 hover:bg-gray-50'
                        "
                        @click="familyTypeTab = 'all'"
                     >
                        all
                     </button>
                     <button
                        type="button"
                        class="px-3 py-1 text-sm border-l border-gray-300"
                        :class="
                           familyTypeTab === 'discount'
                              ? 'bg-gray-800 text-white'
                              : 'bg-white text-gray-700 hover:bg-gray-50'
                        "
                        @click="familyTypeTab = 'discount'"
                     >
                        discount
                     </button>
                     <button
                        type="button"
                        class="px-3 py-1 text-sm border-l border-gray-300"
                        :class="
                           familyTypeTab === 'net_price'
                              ? 'bg-gray-800 text-white'
                              : 'bg-white text-gray-700 hover:bg-gray-50'
                        "
                        @click="familyTypeTab = 'net_price'"
                     >
                        net price
                     </button>
                  </div>
                  <button
                     type="button"
                     class="rounded border border-gray-300 px-3 py-1 text-sm text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                     :disabled="isCreatingFamily"
                     @click="addFamily"
                  >
                     {{ isCreatingFamily ? 'Adding...' : 'Add' }}
                  </button>
               </div>
            </div>
            <div v-if="isLoading" class="p-6 text-gray-500">Loading...</div>
            <div v-else-if="!filteredFamilies.length" class="p-6 text-gray-500">
               <div>Nothing found.</div>
               <button
                  v-if="hasActiveFilters"
                  type="button"
                  class="mt-3 rounded border border-gray-300 px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50"
                  @click="clearFilters"
               >
                  Clear filters
               </button>
            </div>
            <div v-else class="overflow-x-auto">
               <div class="px-4 py-2 text-sm text-gray-600 border-b border-gray-100">
                  {{ filteredFamilies.length }} result{{ filteredFamilies.length > 1 ? 's' : '' }}
               </div>
               <table class="w-full text-sm">
                  <thead class="bg-gray-100 text-gray-700">
                     <tr>
                        <th class="px-4 py-2 text-left">Brand</th>
                        <th v-if="familyTypeTab === 'all'" class="px-4 py-2 text-left">Type</th>
                        <th
                           v-if="familyTypeTab === 'discount' || familyTypeTab === 'all'"
                           class="px-4 py-2 text-left"
                        >
                           Family Code
                        </th>
                        <th
                           v-if="familyTypeTab === 'net_price' || familyTypeTab === 'all'"
                           class="px-4 py-2 text-left"
                        >
                           Product Code
                        </th>
                        <th class="px-4 py-2 text-left">Description</th>
                        <th class="px-4 py-2 text-right">Min. Quantity</th>
                        <th
                           v-if="familyTypeTab === 'net_price' || familyTypeTab === 'all'"
                           class="px-4 py-2 text-right"
                        >
                           Listed Price
                        </th>
                        <th
                           v-if="familyTypeTab === 'net_price' || familyTypeTab === 'all'"
                           class="px-4 py-2 text-right"
                        >
                           Net Price
                        </th>
                        <th
                           v-if="familyTypeTab === 'discount' || familyTypeTab === 'all'"
                           class="px-4 py-2 text-right"
                        >
                           Discount
                        </th>
                        <th class="px-4 py-2 text-right">Minimum Margin</th>
                        <th class="px-4 py-2 text-right">Target Margin</th>
                        <!--th class="px-4 py-2 text-left">Unit</th>
                        <th class="px-4 py-2 text-left">Packing</th>
                        <th class="px-4 py-2 text-right">Lead Time (wk)</th-->
                        <th
                           v-if="familyTypeTab === 'discount' || familyTypeTab === 'all'"
                           class="px-4 py-2 text-right"
                        >
                           Products
                        </th>
                     </tr>
                  </thead>
                  <tbody class="divide-y divide-gray-200">
                     <tr
                        v-for="family in filteredFamilies"
                        :key="family.id"
                        class="hover:bg-gray-50"
                     >
                        <td class="px-4 py-2 text-gray-600">
                           {{ brandLookup[family.brand_id] || family.brand_id }}
                        </td>
                        <td v-if="familyTypeTab === 'all'" class="px-4 py-2 text-gray-600">
                           <span v-if="family.type === 'discount'">Family discount</span>
                           <span v-else-if="family.type === 'net_price'">Net price</span>
                           <span v-else class="text-gray-400">-</span>
                        </td>
                        <td
                           v-if="familyTypeTab === 'discount' || familyTypeTab === 'all'"
                           class="px-4 py-2 text-gray-600"
                        >
                           {{ family.code || '-' }}
                        </td>
                        <td
                           v-if="familyTypeTab === 'net_price' || familyTypeTab === 'all'"
                           class="px-4 py-2 text-gray-600 relative overflow-visible"
                        >
                           <template v-if="family.type == 'net_price'">
                              <input
                                 v-model="family.product_code"
                                 class="w-32 rounded border border-gray-300 px-2 py-1 text-sm"
                                 type="text"
                                 placeholder="Product code"
                                 :class="{ 'saved-flash': savedFlashById[family.id] }"
                                 @input="
                                    performProductCodeSearch(family.id, family.product_code || '')
                                 "
                                 @focus="
                                    openProductCodeSuggestions(family.id, family.product_code || '')
                                 "
                                 @blur="closeProductCode(family.id)"
                              />
                              <!-- Product code search dropdown -->
                              <div
                                 v-if="
                                    activeProductCodeFamilyId === family.id &&
                                    ((productCodeSuggestions[family.id] || []).length > 0 ||
                                       productCodeSearchLoading[family.id])
                                 "
                                 class="absolute bottom-full left-0 z-100 mb-1 w-56 rounded border border-gray-300 bg-white shadow-lg max-h-56 overflow-y-auto"
                              >
                                 <div
                                    v-if="productCodeSearchLoading[family.id]"
                                    class="px-3 py-2 text-sm text-gray-500"
                                 >
                                    Searching...
                                 </div>
                                 <template
                                    v-else-if="(productCodeSuggestions[family.id] || []).length > 0"
                                 >
                                    <button
                                       v-for="product in productCodeSuggestions[family.id] || []"
                                       :key="product.id"
                                       type="button"
                                       class="block w-full text-left px-3 py-2 text-sm hover:bg-blue-100 cursor-pointer border-b border-gray-100 last:border-b-0"
                                       @click="selectProductCodeSuggestion(family.id, product)"
                                    >
                                       <div class="font-medium">{{ product.sku }}</div>
                                       <div class="text-xs text-gray-600">{{ product.name }}</div>
                                    </button>
                                 </template>
                                 <div v-else class="px-3 py-2 text-sm text-gray-500">
                                    No products found
                                 </div>
                              </div>
                           </template>
                           <span v-else class="text-gray-400">-</span>
                        </td>
                        <td class="px-4 py-2 text-gray-900 relative group">
                           <span>{{ truncateDescription(family.name) }}</span>
                           <div
                              v-if="(family.name || '').length > 50"
                              class="pointer-events-none absolute left-4 bottom-full z-40 mb-1 hidden max-w-56 max-h-36 overflow-y-auto whitespace-normal wrap-break-word rounded border border-gray-200 bg-white px-2 py-1 text-xs text-gray-700 shadow group-hover:block"
                           >
                              {{ family.name }}
                           </div>
                        </td>
                        <td class="px-4 py-2 text-gray-600 text-right">
                           <input
                              v-model.number="family.quantity"
                              class="w-20 rounded border border-gray-300 px-2 py-1 text-right text-sm"
                              type="number"
                              min="0"
                              step="0.001"
                              placeholder="Quantity"
                              :class="{ 'saved-flash': savedFlashById[family.id] }"
                              @blur="saveFamily(family)"
                           />
                        </td>
                        <td
                           v-if="familyTypeTab === 'net_price' || familyTypeTab === 'all'"
                           class="px-4 py-2 text-gray-600 text-right"
                        >
                           <template
                              v-if="
                                 family.type == 'net_price' &&
                                 family.product?.price !== null &&
                                 family.product?.price !== undefined
                              "
                           >
                              <div class="pt-1" style="font-size: 14px">
                                 <RouterLink
                                    v-if="family.product_code"
                                    :to="{
                                       path: '/products',
                                       query: { refciale: family.product_code },
                                    }"
                                    class="text-blue-600 hover:text-blue-800 hover:underline"
                                 >
                                    {{ formatListPrice(family.product?.price) }}
                                 </RouterLink>
                                 <span v-else>
                                    {{ formatListPrice(family.product?.price) }}
                                 </span>
                              </div>
                           </template>
                           <span v-else class="text-gray-400">-</span>
                        </td>

                        <td
                           v-if="familyTypeTab === 'net_price' || familyTypeTab === 'all'"
                           class="px-4 py-2 pt-2 text-gray-600 text-right"
                        >
                           <input
                              v-if="family.type == 'net_price'"
                              v-model.number="family.net_price"
                              class="w-24 rounded border border-gray-300 px-2 py-1 text-right text-sm"
                              type="number"
                              min="0"
                              step="0.0001"
                              placeholder="Net price"
                              :class="{ 'saved-flash': savedFlashById[family.id] }"
                              @blur="saveFamily(family)"
                           />
                           <span v-else class="text-gray-400">-</span>
                        </td>

                        <td
                           v-if="familyTypeTab === 'discount' || familyTypeTab === 'all'"
                           class="px-4 py-2 text-gray-600 text-right"
                        >
                           <input
                              v-if="family.type == 'discount'"
                              v-model.number="family.discount"
                              class="w-20 rounded border border-gray-300 px-2 py-1 text-right text-sm"
                              type="number"
                              min="0"
                              max="100"
                              step="0.01"
                              placeholder="Discount"
                              :class="{ 'saved-flash': savedFlashById[family.id] }"
                              @blur="saveFamily(family)"
                           />
                           <span v-else class="text-gray-400">-</span>
                        </td>
                        <td class="px-4 py-2 text-gray-600 text-right">
                           <input
                              v-model.number="family.minimum_margin"
                              class="w-20 rounded border border-gray-300 px-2 py-1 text-right text-sm"
                              type="number"
                              min="0"
                              max="100"
                              step="0.01"
                              placeholder="Minimum Margin"
                              :class="{ 'saved-flash': savedFlashById[family.id] }"
                              @blur="saveFamily(family)"
                           />
                        </td>
                        <td class="px-4 py-2 text-gray-600 text-right">
                           <input
                              v-model.number="family.target_margin"
                              class="w-20 rounded border border-gray-300 px-2 py-1 text-right text-sm"
                              type="number"
                              min="0"
                              max="100"
                              step="0.01"
                              placeholder="Target Margin"
                              :class="{ 'saved-flash': savedFlashById[family.id] }"
                              @blur="saveFamily(family)"
                           />
                        </td>

                        <!--td class="px-4 py-2 text-gray-600">
                           <input
                              v-model="family.unit"
                              class="w-16 rounded border border-gray-300 px-2 py-1 text-sm"
                              type="text"
                              placeholder="U"
                              :class="{ 'saved-flash': savedFlashById[family.id] }"
                              @blur="saveFamily(family)"
                           />
                        </td>
                        <td class="px-4 py-2 text-gray-600">
                           <input
                              v-model="family.packing"
                              class="w-20 rounded border border-gray-300 px-2 py-1 text-sm"
                              type="text"
                              placeholder="Pack"
                              :class="{ 'saved-flash': savedFlashById[family.id] }"
                              @blur="saveFamily(family)"
                           />
                        </td>
                        <td class="px-4 py-2 text-gray-600 text-right">
                           <input
                              v-model.number="family.lead_time_week"
                              class="w-20 rounded border border-gray-300 px-2 py-1 text-right text-sm"
                              type="number"
                              min="0"
                              step="1"
                              placeholder="Lead time"
                              :class="{ 'saved-flash': savedFlashById[family.id] }"
                              @blur="saveFamily(family)"
                           />
                        </td-->
                        <td
                           v-if="familyTypeTab === 'discount' || familyTypeTab === 'all'"
                           class="px-4 py-2 text-right"
                        >
                           <RouterLink
                              v-if="family.type == 'discount' && family.code"
                              :to="{ path: '/products', query: { family: family.code } }"
                              class="text-blue-600 hover:text-blue-800 hover:underline"
                           >
                              {{ family.product_family_count || 0 }}
                           </RouterLink>
                           <RouterLink
                              v-else-if="family.product"
                              class="text-gray-400"
                              :to="{ path: '/products', query: { refciale: family.product.sku } }"
                           >
                              1
                           </RouterLink>
                        </td>
                     </tr>
                  </tbody>
               </table>
            </div>
         </div>
         <button
            type="button"
            class="rounded border border-gray-300 px-3 py-1 text-sm text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            :disabled="isCreatingFamily"
            @click="addFamily"
         >
            {{ isCreatingFamily ? 'Adding...' : 'Add' }}
         </button>
      </div>
   </div>
</template>

<style scoped>
table {
   font-size: 12px;
}
table td {
   vertical-align: top;
}
/* Hide native number input arrows/spinners */
input[type='number']::-webkit-outer-spin-button,
input[type='number']::-webkit-inner-spin-button {
   -webkit-appearance: none;
   margin: 0;
}

input[type='number'] {
   -moz-appearance: textfield;
   appearance: textfield;
}
</style>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import ProductsSubHeader from './../products/ProductsSubHeader.vue';
import { useBrandFamilyData } from '../products/useBrandFamilyData';
import { supabase } from '../../lib/supabase';
import { searchProductBySku } from '../../composables/useSuggestionSearch';

const router = useRouter();
const route = useRoute();
const { brands, families, isLoading, errorMessage, loadData } = useBrandFamilyData();
const codeQuery = ref('');
const typeQuery = ref('');
const skuQuery = ref('');
const familyTypeTab = ref<'all' | 'discount' | 'net_price'>('discount');
const exactMatch = ref(true);
const showDiscountOnly = ref(true);
const brandIdFilter = ref<string | null>(null);
const isSavingById = ref<Record<string, boolean>>({});
const savedFlashById = ref<Record<string, boolean>>({});
const isCreatingFamily = ref(false);

// Product code search state
const productCodeSuggestions = ref<Record<string, any[]>>({});
const productCodeSearchLoading = ref<Record<string, boolean>>({});
const productCodeSearchError = ref<Record<string, string>>({});
const productCodeSearchTimeout = ref<Record<string, ReturnType<typeof setTimeout>>>({});
const activeProductCodeFamilyId = ref<string | null>(null);
const lastSyncedNetPriceSkuByFamilyId = ref<Record<string, string | null>>({});

const brandLookup = computed<Record<string, string>>(() => {
   return brands.value.reduce(
      (acc, brand) => {
         acc[brand.id] = brand.name;
         return acc;
      },
      {} as Record<string, string>
   );
});

const hasActiveFilters = computed(() => {
   return (
      familyTypeTab.value !== 'discount' ||
      codeQuery.value.trim().length > 0 ||
      typeQuery.value.trim().length > 0 ||
      skuQuery.value.trim().length > 0 ||
      brandIdFilter.value !== null ||
      exactMatch.value !== true ||
      showDiscountOnly.value !== true
   );
});

const filteredFamilies = computed(() => {
   console.log('[compute] Filtering families with:', {
      codeQuery: codeQuery.value,
      typeQuery: typeQuery.value,
      skuQuery: skuQuery.value,
      exactMatch: exactMatch.value,
      showDiscountOnly: showDiscountOnly.value,
      brandIdFilter: brandIdFilter.value,
   });

   return families.value
      .filter((family) => {
         if (familyTypeTab.value !== 'all') {
            const normalizedFamilyType = (family.type || '').toLowerCase();
            const selectedType = familyTypeTab.value === 'net_price' ? 'net_price' : 'discount';
            if (normalizedFamilyType !== selectedType) {
               return false;
            }
         }

         // Filter by brand if brand_id is set
         if (brandIdFilter.value && family.brand_id !== brandIdFilter.value) {
            return false;
         }

         const code = family.code ? family.code.toLowerCase() : '';
         const type = family.type ? family.type.toLowerCase() : '';
         const sku = family.product_code ? family.product_code.toLowerCase() : '';
         const normalizedCodeQuery = codeQuery.value.toLowerCase();
         const normalizedTypeQuery = typeQuery.value.toLowerCase();
         const normalizedSkuQuery = skuQuery.value.toLowerCase();

         if (normalizedCodeQuery) {
            if (exactMatch.value) {
               if (code !== normalizedCodeQuery) {
                  return false;
               }
            } else if (!code.includes(normalizedCodeQuery)) {
               return false;
            }
         }

         if (normalizedTypeQuery) {
            if (exactMatch.value) {
               if (type !== normalizedTypeQuery) {
                  return false;
               }
            } else if (!type.includes(normalizedTypeQuery)) {
               return false;
            }
         }

         if (normalizedSkuQuery) {
            if (exactMatch.value) {
               if (sku !== normalizedSkuQuery) {
                  return false;
               }
            } else if (!sku.includes(normalizedSkuQuery)) {
               return false;
            }
         }

         if (familyTypeTab.value === 'discount' && showDiscountOnly.value) {
            const discount = family.discount;
            if (typeof discount !== 'number' || discount <= 0) {
               return false;
            }
         }

         return true;
      })
      .sort((a, b) => {
         const codeA = (a.code || '').toLowerCase();
         const codeB = (b.code || '').toLowerCase();
         return codeA.localeCompare(codeB, undefined, { numeric: true, sensitivity: 'base' });
      });
});

const syncUrlWithFilters = async () => {
   const query: Record<string, string> = {};

   if (familyTypeTab.value !== 'discount') {
      query.tab = familyTypeTab.value;
   }

   if (codeQuery.value.trim()) {
      query.code = codeQuery.value.trim();
   }

   if (typeQuery.value.trim()) {
      query.type = typeQuery.value.trim();
   }

   if (skuQuery.value.trim()) {
      query.sku = skuQuery.value.trim();
   }

   if (!exactMatch.value) {
      query.exactMatch = 'false';
   }

   if (showDiscountOnly.value) {
      query.discount_only = 'true';
   }

   if (brandIdFilter.value) {
      query.brand_id = brandIdFilter.value;
   }
   console.log('[syncUrlWithFilters] Syncing URL with query:', query);
   await router.replace({ query });
};

const applyUrlFilters = () => {
   // Read selected tab
   const queryTab = route.query.tab;
   if (queryTab === 'all') {
      familyTypeTab.value = 'all';
   } else if (queryTab === 'net_price') {
      familyTypeTab.value = 'net_price';
   } else {
      familyTypeTab.value = 'discount';
   }

   // Read code query
   const queryCode = route.query.code;
   if (queryCode && typeof queryCode === 'string') {
      codeQuery.value = queryCode;
   } else {
      codeQuery.value = '';
   }

   // Read type query
   const queryType = route.query.type;
   if (queryType && typeof queryType === 'string') {
      typeQuery.value = queryType;
   } else {
      typeQuery.value = '';
   }

   // Read sku query
   const querySku = route.query.sku;
   if (querySku && typeof querySku === 'string') {
      skuQuery.value = querySku;
   } else {
      skuQuery.value = '';
   }

   // Read exactMatch query
   const queryExactMatch = route.query.exactMatch;
   if (queryExactMatch === 'false') {
      exactMatch.value = false;
   } else {
      exactMatch.value = true;
   }

   // Read discount only query
   const queryDiscountOnly = route.query.discount_only;
   if (queryDiscountOnly === 'true') {
      showDiscountOnly.value = true;
   } else {
      showDiscountOnly.value = false;
   }

   // Read brand_id query
   const queryBrandId = route.query.brand_id;
   if (queryBrandId && typeof queryBrandId === 'string') {
      brandIdFilter.value = queryBrandId;
   } else {
      brandIdFilter.value = null;
   }
};

onMounted(() => {
   loadData();
   applyUrlFilters();
});

// Watch for filter changes and sync URL
watch(
   [familyTypeTab, codeQuery, typeQuery, skuQuery, exactMatch, showDiscountOnly, brandIdFilter],
   () => {
      syncUrlWithFilters();
   }
);

const clearFilters = () => {
   familyTypeTab.value = 'discount';
   codeQuery.value = '';
   typeQuery.value = '';
   skuQuery.value = '';
   brandIdFilter.value = null;
   exactMatch.value = true;
   showDiscountOnly.value = true;
};

const addFamily = async () => {
   const selectedBrandId = brandIdFilter.value || brands.value[0]?.id || null;
   if (!selectedBrandId) {
      errorMessage.value = 'Please select a brand before adding a family.';
      return;
   }

   isCreatingFamily.value = true;
   try {
      const type = familyTypeTab.value === 'all' ? 'discount' : familyTypeTab.value;
      const payload: Record<string, any> = {
         brand_id: selectedBrandId,
         type,
         name: '',
         code: null,
         product_code: null,
         quantity: 0,
         discount: 0,
         minimum_margin: 0,
         target_margin: 0,
         net_price: type === 'net_price' ? 0 : null,
      };

      const { data, error } = await (supabase as any)
         .from('family')
         .insert(payload)
         .select('*')
         .single();
      if (error) {
         alert('Failed to add family: ' + error.message);
         throw error;
      }

      families.value = [
         ...families.value,
         {
            ...data,
            product_family_count: 0,
            product: null,
         },
      ];

      if (type === 'discount' && showDiscountOnly.value) {
         // New rows start with discount 0; show them immediately.
         showDiscountOnly.value = false;
      }
   } catch (error) {
      console.error('[FamilyPage] Failed to add family:', error);
      errorMessage.value = error instanceof Error ? error.message : 'Failed to add family.';
   } finally {
      isCreatingFamily.value = false;
   }
};

const formatListPrice = (value: number) => {
   return new Intl.NumberFormat('fr-FR', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
   }).format(Number(value) || 0);
};

const truncateDescription = (value: string | null | undefined) => {
   const text = String(value || '');
   if (text.length <= 50) return text;
   return `${text.slice(0, 50)}...`;
};

const triggerSavedFlash = (familyId: string) => {
   savedFlashById.value = { ...savedFlashById.value, [familyId]: true };
   setTimeout(() => {
      savedFlashById.value = { ...savedFlashById.value, [familyId]: false };
   }, 800);
};

const performProductCodeSearch = (familyId: string, query: string) => {
   // Clear previous timeout
   if (productCodeSearchTimeout.value[familyId]) {
      clearTimeout(productCodeSearchTimeout.value[familyId]);
   }

   productCodeSearchError.value[familyId] = '';

   // Clear suggestions if query is too short
   if (!query || query.length < 2) {
      productCodeSuggestions.value[familyId] = [];
      productCodeSearchLoading.value[familyId] = false;
      return;
   }

   productCodeSearchLoading.value[familyId] = true;

   // Debounce search by 300ms
   productCodeSearchTimeout.value[familyId] = setTimeout(() => {
      console.log(`[ProductCodeSearch] Searching for "${query}" in family ${familyId}`);
      searchProductBySku(
         query,
         (products, error) => {
            console.log('[ProductCodeSearch] Search results for family', familyId, {
               products,
               error,
            });
            productCodeSuggestions.value[familyId] = products;

            console.log('suggestions for family', familyId, productCodeSuggestions.value[familyId]);
            if (error) {
               productCodeSearchError.value[familyId] = error;
            }
            productCodeSearchLoading.value[familyId] = false;
         },
         () => {
            // Loading state updated by searchProductBySku
         }
      );
   }, 300);
};

const selectProductCodeSuggestion = (familyId: string, product: any) => {
   const family = families.value.find((f) => f.id === familyId);
   if (!family) return;

   family.product_code = product.sku;
   family.name = product.name || family.name;
   family.product = product;
   if (product.brand_id) {
      family.brand_id = product.brand_id;
   }
   productCodeSuggestions.value[familyId] = [];
   productCodeSearchError.value[familyId] = '';
   productCodeSearchLoading.value[familyId] = false;
   activeProductCodeFamilyId.value = null;
   saveFamily(family);
};

const openProductCodeSuggestions = (familyId: string, currentQuery: string) => {
   activeProductCodeFamilyId.value = familyId;
   performProductCodeSearch(familyId, currentQuery);
};

const closeProductCode = (familyId: string) => {
   closeProductCodeSuggestions(familyId);
   saveFamily(families.value.find((f) => f.id === familyId) as (typeof families.value)[number]);
};

const closeProductCodeSuggestions = (familyId: string) => {
   window.setTimeout(() => {
      if (activeProductCodeFamilyId.value === familyId) {
         activeProductCodeFamilyId.value = null;
      }
   }, 150);
};

const syncNetPriceFamilyProductLink = async (family: (typeof families.value)[number]) => {
   if ((family.type || '').toLowerCase() !== 'net_price') {
      delete lastSyncedNetPriceSkuByFamilyId.value[family.id];
      return;
   }

   const sku = String(family.product_code || '').trim();
   const normalizedSku = sku.length > 0 ? sku : null;
   if (lastSyncedNetPriceSkuByFamilyId.value[family.id] === normalizedSku) {
      return;
   }

   if (!normalizedSku) {
      const { error: deleteError } = await (supabase as any)
         .from('product_family')
         .delete()
         .eq('family_id', family.id);
      if (deleteError) {
         console.error(
            '[FamilyPage] Failed to clear product_family links for net_price family:',
            deleteError
         );
      }
      family.product = null;
      lastSyncedNetPriceSkuByFamilyId.value[family.id] = null;
      return;
   }

   const { data: product, error: productError } = await (supabase as any)
      .from('product')
      .select('id,sku,name,price,brand_id')
      .eq('sku', normalizedSku)
      .maybeSingle();
   if (productError) {
      console.error('[FamilyPage] Failed to resolve product by SKU:', productError);
      return;
   }

   if (!product?.id) {
      const { error: deleteError } = await (supabase as any)
         .from('product_family')
         .delete()
         .eq('family_id', family.id);
      if (deleteError) {
         console.error('[FamilyPage] Failed to clear stale product_family links:', deleteError);
      }
      family.product = null;
      lastSyncedNetPriceSkuByFamilyId.value[family.id] = normalizedSku;
      return;
   }

   const { error: linkError } = await (supabase as any).from('product_family').upsert(
      {
         product_id: product.id,
         family_id: family.id,
      },
      {
         onConflict: 'product_id,family_id',
      }
   );
   if (linkError) {
      console.error('[FamilyPage] Failed to upsert product_family link:', linkError);
      return;
   }

   const { error: cleanupError } = await (supabase as any)
      .from('product_family')
      .delete()
      .eq('family_id', family.id)
      .neq('product_id', product.id);
   if (cleanupError) {
      console.error('[FamilyPage] Failed to cleanup extra product_family links:', cleanupError);
   }

   family.product = {
      id: product.id,
      sku: product.sku,
      name: product.name ?? null,
      price: product.price ?? null,
      brand_id: product.brand_id ?? null,
   };
   lastSyncedNetPriceSkuByFamilyId.value[family.id] = normalizedSku;
};

const saveFamily = async (family: (typeof families.value)[number]) => {
   isSavingById.value = { ...isSavingById.value, [family.id]: true };
   try {
      const payload = {
         name: family.name || null,
         brand_id: family.brand_id || null,
         product_code: family.product_code || null,
         quantity: family.quantity,
         discount: family.discount,
         minimum_margin: family.minimum_margin,
         target_margin: family.target_margin,
         unit: family.unit || null,
         packing: family.packing || null,
         lead_time_week: family.lead_time_week,
         net_price: family.net_price,
      };

      const { error } = await (supabase as any).from('family').update(payload).eq('id', family.id);
      if (error) throw error;
      await syncNetPriceFamilyProductLink(family);
      triggerSavedFlash(family.id);
   } catch (error) {
      console.error('[FamilyPage] Failed to save family fields:', error);
   } finally {
      isSavingById.value = { ...isSavingById.value, [family.id]: false };
   }
};
</script>

<style scoped>
@keyframes saved-flash {
   0% {
      border-color: #3b82f6;
      box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.35);
   }
   100% {
      border-color: #d1d5db;
      box-shadow: 0 0 0 0 rgba(59, 130, 246, 0);
   }
}

.saved-flash {
   animation: saved-flash 0.8s ease-out;
}
</style>
