<template>
   <div>
      <ProductsSubHeader />
      <div class="px-4 max-w-7xl mx-auto">
         <Breadcrumb v-if="!isNewBrand" :items="breadcrumbItems" />
         <div class="mb-6 flex items-center justify-between">
            <div>
               <div v-if="isNewBrand" class="text-gray-600 mt-2">Create a new brand</div>
               <div v-else class="flex gap-4 mt-2 text-gray-600">
                  <span class="text-gray-500">
                     Minimum Margin: {{ formData.minimum_margin || '0' }}%
                  </span>
                  <span class="text-gray-500"> Target Margin: {{ formData.target_margin }}% </span>
               </div>
            </div>
            <div class="flex gap-2">
               <button
                  v-if="!isNewBrand"
                  @click="showForm = !showForm"
                  class="px-4 py-2 bg-blue-600 text-white rounded-lg font-medium text-sm hover:bg-blue-700"
               >
                  {{ showForm ? 'Cancel' : 'Edit' }}
               </button>
            </div>
         </div>

         <div v-if="errorMessage" class="mb-4 p-4 bg-red-100 text-red-700 rounded-lg">
            {{ errorMessage }}
         </div>
         <div v-if="successMessage" class="mb-4 p-4 bg-green-100 text-green-700 rounded-lg">
            {{ successMessage }}
         </div>

         <div v-if="isNewBrand || showForm" class="bg-white border border-gray-200 rounded-lg p-6">
            <form @submit.prevent="saveBrand" class="space-y-4">
               <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1"> Name * </label>
                  <input
                     v-model="formData.name"
                     type="text"
                     class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                     required
                  />
               </div>
               <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1"> Email </label>
                  <input
                     v-model="formData.email"
                     type="email"
                     class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
               </div>
               <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1"> Phone </label>
                  <input
                     v-model="formData.phone"
                     type="text"
                     class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
               </div>
               <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1"> Website </label>
                  <input
                     v-model="formData.website"
                     type="url"
                     class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
               </div>
               <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">
                     Minimum Margin (%)
                  </label>
                  <input
                     v-model.number="formData.minimum_margin"
                     type="number"
                     step="0.01"
                     min="0"
                     max="999.99"
                     class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                     placeholder="e.g., 10.50"
                  />
               </div>
               <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">
                     Target Margin (%)
                  </label>
                  <input
                     v-model.number="formData.target_margin"
                     type="number"
                     step="0.01"
                     min="0"
                     max="999.99"
                     class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                     placeholder="e.g., 15.00"
                  />
               </div>

               <div class="flex gap-2 pt-2">
                  <button
                     type="submit"
                     :disabled="isSaving"
                     class="px-4 py-2 bg-blue-600 text-white rounded-lg font-medium text-sm hover:bg-blue-700 disabled:bg-gray-400"
                  >
                     {{ isSaving ? 'Saving...' : isNewBrand ? 'Create' : 'Update' }}
                  </button>
                  <button
                     type="button"
                     @click="resetForm"
                     class="px-4 py-2 bg-gray-200 text-gray-800 rounded-lg font-medium text-sm hover:bg-gray-300"
                  >
                     Reset
                  </button>
               </div>
            </form>
         </div>

         <div v-if="!isNewBrand && families.length > 0" class="mt-8">
            <div class="flex items-center justify-between mb-4">
               <h2 class="text-xl font-bold text-gray-900">
                  Families ({{ filteredFamilies.length }})
               </h2>
               <button
                  type="button"
                  @click="showDiscountOnly = !showDiscountOnly"
                  class="px-4 py-2 rounded-lg font-medium text-sm transition-colors"
                  :class="
                     showDiscountOnly
                        ? 'bg-blue-600 text-white hover:bg-blue-700'
                        : 'bg-gray-200 text-gray-800 hover:bg-gray-300'
                  "
               >
                  {{ showDiscountOnly ? 'Showing: Discounts only' : 'Showing: All families' }}
               </button>
            </div>
            <div class="bg-white border border-gray-200 rounded-lg shadow overflow-hidden">
               <table class="w-full">
                  <thead class="bg-gray-50 border-b">
                     <tr>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">
                           Name
                        </th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">
                           Code
                        </th>
                        <th
                           class="px-6 py-3 text-right text-xs font-medium text-gray-700 uppercase"
                        >
                           Discount
                        </th>
                        <th
                           class="px-6 py-3 text-right text-xs font-medium text-gray-700 uppercase"
                        >
                           Minimum Margin
                        </th>
                        <th
                           class="px-6 py-3 text-right text-xs font-medium text-gray-700 uppercase"
                        >
                           Target Margin
                        </th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">
                           Action
                        </th>
                     </tr>
                  </thead>
                  <tbody class="divide-y">
                     <tr
                        v-for="family in filteredFamilies"
                        :key="family.id"
                        class="hover:bg-gray-50"
                     >
                        <td class="px-6 py-4 text-sm font-medium text-gray-900">
                           {{ family.name }}
                        </td>
                        <td class="px-6 py-4 text-sm text-gray-600">{{ family.code || '-' }}</td>
                        <td class="px-6 py-4 text-sm text-right text-gray-600">
                           {{ family.discount ? family.discount + '%' : '-' }}
                        </td>
                        <td class="px-6 py-4 text-sm text-right text-gray-600">
                           {{ family.minimum_margin ? family.minimum_margin + '%' : '-' }}
                        </td>
                        <td class="px-6 py-4 text-sm text-right text-gray-600">
                           {{ family.target_margin ? family.target_margin + '%' : '-' }}
                        </td>
                        <td class="px-6 py-4 text-sm">
                           <router-link
                              :to="getFamilyEditLink(family)"
                              class="text-blue-600 hover:text-blue-800 hover:underline font-medium"
                           >
                              Edit
                           </router-link>
                        </td>
                     </tr>
                  </tbody>
               </table>
               <div v-if="filteredFamilies.length === 0" class="p-6 text-center text-gray-500">
                  {{
                     showDiscountOnly ? 'No families with discounts found.' : 'No families found.'
                  }}
               </div>
            </div>
         </div>
         <div
            v-else-if="!isNewBrand && families.length === 0"
            class="mt-8 p-6 bg-gray-50 border border-gray-200 rounded-lg text-center text-gray-500"
         >
            No families associated with this brand.
         </div>
      </div>
   </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import ProductsSubHeader from './ProductsSubHeader.vue';
import Breadcrumb from '../common/Breadcrumb.vue';
import { supabase } from '../../lib/supabase';

const route = useRoute();
const router = useRouter();

const brandId = computed(() => (route.params.id ? String(route.params.id) : null));
const isNewBrand = computed(() => !brandId.value);

const formData = ref({
   name: '',
   email: '',
   phone: '',
   website: '',
   minimum_margin: null as number | null,
   target_margin: null as number | null,
});

const originalData = ref({ ...formData.value });
const isSaving = ref(false);
const errorMessage = ref('');
const successMessage = ref('');
const families = ref<any[]>([]);
const showDiscountOnly = ref(true);
const showForm = ref(false);

const isEditModeQueryEnabled = () => {
   const editQuery = route.query.edit;
   if (Array.isArray(editQuery)) {
      return editQuery.some((value) => String(value).toLowerCase() === 'true');
   }
   return String(editQuery || '').toLowerCase() === 'true';
};

const breadcrumbItems = computed(() => [
   { label: 'Brands', to: '/vendors/brand' },
   { label: formData.value.name || 'Loading...' },
]);

const filteredFamilies = computed(() => {
   if (showDiscountOnly.value) {
      return families.value.filter((f) => typeof f.discount === 'number' && f.discount > 0);
   }
   return families.value;
});

const getFamilyEditLink = (family: any) => {
   const query: Record<string, string> = {};

   if (brandId.value) {
      query.brand_id = brandId.value;
   }

   const familyType = String(family?.type || '').toLowerCase();
   if (familyType === 'net_price') {
      query.tab = 'net_price';
      const sku = String(family?.product_code || family?.sku || '').trim();
      if (sku) {
         query.sku = sku;
      }
   } else {
      query.tab = 'discount';
      const code = String(family?.code || '').trim();
      if (code) {
         query.code = code;
      }
   }

   return { path: '/vendors/family', query };
};

const loadBrand = async () => {
   if (!brandId.value) return;

   try {
      const { data, error } = await supabase
         .from('brand')
         .select('*')
         .eq('id', brandId.value)
         .single();

      if (error) throw new Error(error.message);
      if (!data) throw new Error('Brand not found');
      const brand = data as any;

      formData.value = {
         name: brand.name || '',
         email: brand.email || '',
         phone: brand.phone || '',
         website: brand.website || '',
         minimum_margin: brand.minimum_margin || null,
         target_margin: brand.target_margin || null,
      };
      originalData.value = { ...formData.value };

      // Load related families
      const { data: familiesData, error: familiesError } = await supabase
         .from('family')
         .select('*')
         .eq('brand_id', brandId.value)
         .order('name', { ascending: true });

      if (familiesError) throw new Error(familiesError.message);
      families.value = familiesData || [];
   } catch (error) {
      errorMessage.value = error instanceof Error ? error.message : 'Failed to load brand';
   }
};

const saveBrand = async () => {
   if (!formData.value.name.trim()) {
      errorMessage.value = 'Brand name is required';
      return;
   }

   isSaving.value = true;
   errorMessage.value = '';
   successMessage.value = '';

   try {
      const payload = {
         name: formData.value.name,
         email: formData.value.email || null,
         phone: formData.value.phone || null,
         website: formData.value.website || null,
         minimum_margin: formData.value.minimum_margin || null,
         target_margin: formData.value.target_margin || null,
      };

      if (isNewBrand.value) {
         const { error } = await (supabase.from('brand') as any).insert([payload]);
         if (error) throw new Error(error.message);
         successMessage.value = 'Brand created successfully';
         setTimeout(() => router.push('/vendors/brand'), 1500);
      } else {
         if (!brandId.value) {
            throw new Error('Missing brand ID');
         }
         const { error } = await (supabase.from('brand') as any)
            .update(payload)
            .eq('id', brandId.value);
         if (error) throw new Error(error.message);
         successMessage.value = 'Brand updated successfully';
         originalData.value = { ...formData.value };
         showForm.value = false;
      }
   } catch (error) {
      errorMessage.value = error instanceof Error ? error.message : 'Failed to save brand';
   } finally {
      isSaving.value = false;
   }
};

const resetForm = () => {
   formData.value = { ...originalData.value };
   errorMessage.value = '';
   successMessage.value = '';
   if (!isNewBrand.value) {
      showForm.value = false;
   }
};

onMounted(() => {
   if (!isNewBrand.value && isEditModeQueryEnabled()) {
      showForm.value = true;
   }

   if (!isNewBrand.value) {
      loadBrand();
   }
});

watch(
   () => route.query.edit,
   () => {
      if (!isNewBrand.value) {
         showForm.value = isEditModeQueryEnabled();
      }
   }
);
</script>
