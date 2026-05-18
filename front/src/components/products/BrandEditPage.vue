<template>
   <div>
      <ProductsSubHeader />
      <div class="px-4 max-w-7xl mx-auto">
         <Breadcrumb v-if="!isNewBrand" :items="breadcrumbItems" />
         <div class="mb-6 flex items-center justify-between">
            <div>
               <div v-if="isNewBrand" class="text-gray-600 mt-2">
                  {{ t('products.brand.createTitle') }}
               </div>
               <div v-else class="flex gap-4 mt-2 text-gray-600">
                  <span class="text-gray-500">
                     {{ t('products.brand.minimumMargin') }}: {{ formData.minimum_margin || '0' }}%
                  </span>
                  <span class="text-gray-500">
                     {{ t('products.brand.targetMargin') }}: {{ formData.target_margin }}%
                  </span>
               </div>
            </div>
            <div class="flex gap-2">
               <button
                  v-if="!isNewBrand"
                  @click="showForm = !showForm"
                  class="px-4 py-2 bg-blue-600 text-white rounded-lg font-medium text-sm hover:bg-blue-700"
               >
                  {{ showForm ? t('products.brand.cancelButton') : t('products.brand.editButton') }}
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
                  <label class="block text-sm font-medium text-gray-700 mb-1">
                     {{ t('products.brand.nameField') }} *
                  </label>
                  <input
                     v-model="formData.name"
                     type="text"
                     class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                     required
                  />
               </div>
               <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">
                     {{ t('products.brand.columns.vendor') }} *
                  </label>
                  <select
                     v-model="formData.vendor_id"
                     class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                     required
                  >
                     <option value="" disabled>{{ t('common.loading') }}</option>
                     <option v-for="vendor in vendors" :key="vendor.id" :value="vendor.id">
                        {{ vendor.name }}
                     </option>
                  </select>
               </div>
               <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">
                     {{ t('products.brand.emailField') }}
                  </label>
                  <input
                     v-model="formData.email"
                     type="email"
                     class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
               </div>
               <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">
                     {{ t('products.brand.phoneField') }}
                  </label>
                  <input
                     v-model="formData.phone"
                     type="text"
                     class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
               </div>
               <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">
                     {{ t('products.brand.websiteField') }}
                  </label>
                  <input
                     v-model="formData.website"
                     type="url"
                     class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
               </div>
               <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">
                     {{ t('products.brand.fields.minimumMargin') }}
                  </label>
                  <input
                     v-model.number="formData.minimum_margin"
                     type="number"
                     step="0.01"
                     min="0"
                     max="999.99"
                     class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                     :placeholder="t('products.brand.placeholders.minimumMargin')"
                  />
               </div>
               <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">
                     {{ t('products.brand.fields.targetMargin') }}
                  </label>
                  <input
                     v-model.number="formData.target_margin"
                     type="number"
                     step="0.01"
                     min="0"
                     max="999.99"
                     class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                     :placeholder="t('products.brand.placeholders.targetMargin')"
                  />
               </div>

               <div class="flex gap-2 pt-2">
                  <button
                     type="submit"
                     :disabled="isSaving"
                     class="px-4 py-2 bg-blue-600 text-white rounded-lg font-medium text-sm hover:bg-blue-700 disabled:bg-gray-400"
                  >
                     {{
                        isSaving
                           ? t('common.saving')
                           : isNewBrand
                             ? t('common.create')
                             : t('common.edit')
                     }}
                  </button>
                  <button
                     type="button"
                     @click="resetForm"
                     class="px-4 py-2 bg-gray-200 text-gray-800 rounded-lg font-medium text-sm hover:bg-gray-300"
                  >
                     {{ t('products.brand.reset') }}
                  </button>
               </div>
            </form>
         </div>

         <div v-if="!isNewBrand && families.length > 0" class="mt-8">
            <div class="flex items-center justify-between mb-4">
               <h2 class="text-xl font-bold text-gray-900">
                  {{ t('products.brand.familiesTitle', { count: filteredFamilies.length }) }}
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
                  {{
                     showDiscountOnly
                        ? t('products.brand.showingDiscountsOnly')
                        : t('products.brand.showingAllFamilies')
                  }}
               </button>
            </div>
            <div class="bg-white border border-gray-200 rounded-lg shadow overflow-hidden">
               <table class="w-full">
                  <thead class="bg-gray-50 border-b">
                     <tr>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">
                           {{ t('products.brand.columns.name') }}
                        </th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">
                           {{ t('products.brand.columns.code') }}
                        </th>
                        <th
                           class="px-6 py-3 text-right text-xs font-medium text-gray-700 uppercase"
                        >
                           {{ t('products.brand.columns.discount') }}
                        </th>
                        <th
                           class="px-6 py-3 text-right text-xs font-medium text-gray-700 uppercase"
                        >
                           {{ t('products.brand.columns.minimumMargin') }}
                        </th>
                        <th
                           class="px-6 py-3 text-right text-xs font-medium text-gray-700 uppercase"
                        >
                           {{ t('products.brand.columns.targetMargin') }}
                        </th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">
                           {{ t('common.edit') }}
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
                              {{ t('common.edit') }}
                           </router-link>
                        </td>
                     </tr>
                  </tbody>
               </table>
               <div v-if="filteredFamilies.length === 0" class="p-6 text-center text-gray-500">
                  {{
                     showDiscountOnly
                        ? t('products.brand.noDiscountFamilies')
                        : t('products.brand.noFamilies')
                  }}
               </div>
            </div>
         </div>
         <div
            v-else-if="!isNewBrand && families.length === 0"
            class="mt-8 p-6 bg-gray-50 border border-gray-200 rounded-lg text-center text-gray-500"
         >
            {{ t('products.brand.noFamiliesLinked') }}
         </div>
      </div>
   </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import ProductsSubHeader from './ProductsSubHeader.vue';
import Breadcrumb from '../common/Breadcrumb.vue';
import { useI18n } from '../../i18n/useI18n';
import {
   createBrand,
   getBrand,
   listBrandFamilies,
   updateBrand,
   type BrandFamily,
} from '../../api/brand';
import { listVendors, type Vendor } from '../../api/vendor';

const route = useRoute();
const router = useRouter();
const { t } = useI18n();

const brandId = computed(() => (route.params.id ? String(route.params.id) : null));
const isNewBrand = computed(() => !brandId.value);

const formData = ref({
   name: '',
   vendor_id: '',
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
const families = ref<BrandFamily[]>([]);
const vendors = ref<Vendor[]>([]);
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
   { label: t('products.brand.breadcrumb'), to: '/vendors/brand' },
   { label: formData.value.name || t('common.loading') },
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
      const brand = await getBrand(brandId.value);

      formData.value = {
         name: brand.name || '',
         vendor_id: brand.vendor_id || '',
         email: brand.email || '',
         phone: brand.phone || '',
         website: brand.website || '',
         minimum_margin: brand.minimum_margin || null,
         target_margin: brand.target_margin || null,
      };
      originalData.value = { ...formData.value };

      // Load related families
      families.value = await listBrandFamilies(brandId.value);
   } catch (error) {
      errorMessage.value = error instanceof Error ? error.message : 'Failed to load brand';
   }
};

const loadVendors = async () => {
   try {
      vendors.value = await listVendors();
      if (!formData.value.vendor_id && vendors.value.length > 0) {
         formData.value.vendor_id = vendors.value[0]!.id;
      }
   } catch (error) {
      errorMessage.value = error instanceof Error ? error.message : 'Failed to load vendors';
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
         vendor_id: formData.value.vendor_id,
         email: formData.value.email || null,
         phone: formData.value.phone || null,
         website: formData.value.website || null,
         minimum_margin: formData.value.minimum_margin || null,
         target_margin: formData.value.target_margin || null,
      };

      if (isNewBrand.value) {
         await createBrand(payload);
         successMessage.value = 'Brand created successfully';
         setTimeout(() => router.push('/vendors/brand'), 1500);
      } else {
         if (!brandId.value) {
            throw new Error('Missing brand ID');
         }
         await updateBrand(brandId.value, payload);
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

   loadVendors();

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
