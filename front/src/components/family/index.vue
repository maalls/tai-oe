<template>
   <div>
      <ProductsSubHeader>
         <template #actions>
            <ActionButton
               v-if="userRole === 'admin'"
               type="button"
               variant="dark"
               :disabled="isCreatingFamily"
               @click="addFamily"
            >
               {{ isCreatingFamily ? t('products.family.adding') : t('products.family.add') }}
            </ActionButton>
         </template>
      </ProductsSubHeader>
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
               </div>
            </div>
            <div v-if="isLoading" class="p-6 text-gray-500">Loading...</div>
            <div v-else-if="!filteredFamilies.length" class="p-6 text-gray-500">
               <div>Nothing found.</div>
               <ActionButton
                  v-if="hasActiveFilters"
                  type="button"
                  variant="neutral"
                  size="xs"
                  class="mt-3"
                  @click="clearFilters"
               >
                  Clear filters
               </ActionButton>
            </div>
            <div v-else class="overflow-x-auto">
               <div
                  class="px-4 py-2 text-sm text-gray-600 border-b border-gray-100 flex items-center justify-between gap-3"
               >
                  <span>{{ shownResultsText }}</span>
                  <PaginationControls
                     :currentPage="currentPage"
                     :totalPages="totalPages"
                     :goToPage="goToPage"
                  />
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
                        <th v-if="userRole === 'admin'" class="px-4 py-2 text-right">Actions</th>
                     </tr>
                  </thead>
                  <tbody class="divide-y divide-gray-200">
                     <tr
                        v-for="family in paginatedFamilies"
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
                                 @blur="closeProductCode(family.id, $event)"
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
                                       data-product-suggestion="true"
                                       class="block w-full text-left px-3 py-2 text-sm hover:bg-blue-100 cursor-pointer border-b border-gray-100 last:border-b-0"
                                       @mousedown.prevent="
                                          selectProductCodeSuggestion(family.id, product)
                                       "
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
                              :class="{
                                 'saved-flash': savedFlashById[family.id] && userRole === 'admin',
                              }"
                              @blur="saveFamily(family)"
                              :readonly="userRole !== 'admin'"
                              :tabindex="userRole !== 'admin' ? -1 : 0"
                           />
                        </td>
                        <td
                           v-if="familyTypeTab === 'net_price' || familyTypeTab === 'all'"
                           class="px-4 py-2 text-gray-600 text-right"
                        >
                           <template v-if="family.type == 'net_price'">
                              <div class="pt-1" style="font-size: 14px">
                                 <RouterLink
                                    v-if="
                                       family.product?.id &&
                                       family.product?.price !== null &&
                                       family.product?.price !== undefined
                                    "
                                    :to="{
                                       name: 'product-detail',
                                       params: { id: family.product.id },
                                    }"
                                    class="text-blue-600 hover:text-blue-800 hover:underline"
                                 >
                                    {{ formatListPrice(family.product?.price) }}
                                 </RouterLink>
                                 <RouterLink
                                    v-else-if="family.product_code"
                                    :to="{
                                       name: 'product-new',
                                       query: {
                                          refciale: family.product_code,
                                          brand_id: family.brand_id,
                                       },
                                    }"
                                    class="text-blue-600 hover:text-blue-800 hover:underline"
                                 >
                                    create
                                 </RouterLink>
                                 <span v-else> - </span>
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
                              :class="{
                                 'saved-flash': savedFlashById[family.id] && userRole === 'admin',
                              }"
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
                              :class="{
                                 'saved-flash': savedFlashById[family.id] && userRole === 'admin',
                              }"
                              @blur="saveFamily(family)"
                              :readonly="userRole !== 'admin'"
                              :tabindex="userRole !== 'admin' ? -1 : 0"
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
                              :class="{
                                 'saved-flash': savedFlashById[family.id] && userRole === 'admin',
                              }"
                              @blur="saveFamily(family)"
                              :readonly="userRole !== 'admin'"
                              :tabindex="userRole !== 'admin' ? -1 : 0"
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
                              :readonly="userRole !== 'admin'"
                              :tabindex="userRole !== 'admin' ? -1 : 0"
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
                        <td v-if="userRole === 'admin'" class="px-4 py-2 text-right">
                           <ActionButton
                              type="button"
                              variant="danger-outline"
                              size="xs"
                              :disabled="isDeletingById[family.id]"
                              @click="deleteFamily(family)"
                           >
                              {{ isDeletingById[family.id] ? 'Deleting...' : 'Delete' }}
                           </ActionButton>
                        </td>
                     </tr>
                  </tbody>
               </table>
               <div
                  class="px-4 py-3 text-sm text-gray-600 border-t border-gray-100 flex items-center justify-between gap-3"
               >
                  <span>{{ shownResultsText }}</span>
                  <PaginationControls
                     :currentPage="currentPage"
                     :totalPages="totalPages"
                     :goToPage="goToPage"
                  />
               </div>
            </div>
         </div>
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
import ProductsSubHeader from './../products/ProductsSubHeader.vue';
import ActionButton from '../common/ActionButton.vue';
import PaginationControls from '../products/components/table/PaginationControls.vue';
import { useFamilyPageLogic } from './index';

const {
   t,
   userRole,
   brands,
   isLoading,
   errorMessage,
   codeQuery,
   typeQuery,
   skuQuery,
   familyTypeTab,
   exactMatch,
   showDiscountOnly,
   brandIdFilter,
   isDeletingById,
   savedFlashById,
   isCreatingFamily,
   currentPage,
   productCodeSuggestions,
   productCodeSearchLoading,
   activeProductCodeFamilyId,
   brandLookup,
   hasActiveFilters,
   filteredFamilies,
   totalPages,
   paginatedFamilies,
   shownResultsText,
   goToPage,
   clearFilters,
   addFamily,
   formatListPrice,
   truncateDescription,
   performProductCodeSearch,
   selectProductCodeSuggestion,
   openProductCodeSuggestions,
   closeProductCode,
   saveFamily,
   deleteFamily,
} = useFamilyPageLogic();
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
