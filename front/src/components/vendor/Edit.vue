<template>
   <div>
      <ProductsSubHeader />
      <div class="p-6 max-w-7xl mx-auto">
         <Breadcrumb v-if="!isNewVendor" :items="breadcrumbItems" />

         <div v-if="errorMessage" class="mb-4 p-4 bg-red-100 text-red-700 rounded-lg">
            {{ errorMessage }}
         </div>
         <div v-if="successMessage" class="mb-4 p-4 bg-green-100 text-green-700 rounded-lg">
            {{ successMessage }}
         </div>

         <div v-if="isNewVendor || showForm" class="bg-white border border-gray-200 rounded-lg p-6">
            <form @submit.prevent="saveVendor" class="space-y-4">
               <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">
                     {{ t('vendors.fields.name') }} *
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
                     {{ t('vendors.fields.email') }}
                  </label>
                  <input
                     v-model="formData.email"
                     type="email"
                     class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
               </div>
               <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">
                     {{ t('vendors.fields.phone') }}
                  </label>
                  <input
                     v-model="formData.phone"
                     type="text"
                     class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
               </div>
               <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">
                     {{ t('vendors.fields.website') }}
                  </label>
                  <input
                     v-model="formData.website"
                     type="url"
                     class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
               </div>

               <div class="flex gap-2 pt-2">
                  <button type="submit" :disabled="isSaving" class="btn btn-primary">
                     {{
                        isSaving
                           ? t('vendors.actions.saving')
                           : isNewVendor
                             ? t('vendors.actions.create')
                             : t('vendors.actions.update')
                     }}
                  </button>
                  <button type="button" @click="resetForm" class="btn btn-secondary">
                     {{ t('vendors.actions.reset') }}
                  </button>
                  <button
                     v-if="!isNewVendor"
                     type="button"
                     @click="deleteVendor"
                     :disabled="isDeleting"
                     class="btn btn-danger"
                  >
                     {{ isDeleting ? t('vendors.actions.deleting') : t('vendors.actions.delete') }}
                  </button>
               </div>
            </form>
         </div>

         <div v-if="!isNewVendor" class="mt-8">
            <div class="mb-4">
               <h2 class="text-lg font-semibold text-gray-900">
                  {{ t('vendors.relatedBrands.title') }}
               </h2>
            </div>

            <div v-if="isBrandDataLoading" class="text-sm text-gray-500">
               {{ t('products.brand.loading') }}
            </div>
            <div v-else-if="brandDataErrorMessage" class="text-sm text-red-600">
               {{ brandDataErrorMessage }}
            </div>
            <div v-else-if="vendorBrands.length === 0" class="text-sm text-gray-500">
               {{ t('products.brand.noBrands') }}
            </div>
            <BrandListTable
               v-else
               :brands="vendorBrands"
               :families="vendorFamilies"
               :isLoading="isBrandDataLoading"
               :errorMessage="brandDataErrorMessage"
            />
         </div>
      </div>
   </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useI18n } from '../../i18n/useI18n';
import {
   createVendor,
   deleteVendor as deleteVendorApi,
   getVendor,
   updateVendor,
} from '../../api/vendor';
import ProductsSubHeader from '../products/ProductsSubHeader.vue';
import Breadcrumb from '../common/Breadcrumb.vue';
import { useBrandFamilyData } from '../products/useBrandFamilyData';
import BrandListTable from '../products/components/BrandListTable.vue';

const route = useRoute();
const router = useRouter();
const { t } = useI18n();

const isNewVendor = computed(() => route.params.id === 'new');
const vendorId = computed(() => (isNewVendor.value ? null : (route.params.id as string)));

const isLoading = ref(false);
const isSaving = ref(false);
const isDeleting = ref(false);
const errorMessage = ref('');
const successMessage = ref('');
const showForm = ref(false);

const {
   brands,
   families,
   isLoading: isBrandDataLoading,
   errorMessage: brandDataErrorMessage,
   loadData: loadBrandFamilyData,
} = useBrandFamilyData();

const vendorBrands = computed(() => {
   if (!vendorId.value) return [];
   return brands.value.filter((brand) => brand.vendor_id === vendorId.value);
});

const vendorBrandIdSet = computed(() => {
   return new Set(vendorBrands.value.map((brand) => brand.id));
});

const vendorFamilies = computed(() => {
   return families.value.filter((family) => vendorBrandIdSet.value.has(family.brand_id));
});

const formData = ref({
   name: '',
   email: '',
   phone: '',
   website: '',
});

const breadcrumbItems = computed(() => [
   { label: t('vendors.breadcrumb'), to: '/vendors' },
   { label: formData.value.name || t('common.loading') },
]);

const loadVendor = async () => {
   if (isNewVendor.value) {
      isLoading.value = false;
      return;
   }

   isLoading.value = true;
   errorMessage.value = '';

   try {
      if (!vendorId.value) {
         errorMessage.value = t('vendors.errors.unknown');
         return;
      }

      const vendor = await getVendor(vendorId.value);
      formData.value = {
         name: vendor.name || '',
         email: vendor.email || '',
         phone: vendor.phone || '',
         website: vendor.website || '',
      };
   } catch (error) {
      errorMessage.value = t('vendors.errors.generic', {
         message: error instanceof Error ? error.message : t('vendors.errors.unknown'),
      });
   } finally {
      isLoading.value = false;
   }
};

const resetForm = () => {
   if (isNewVendor.value) {
      formData.value = {
         name: '',
         email: '',
         phone: '',
         website: '',
      };
   } else {
      loadVendor();
      showForm.value = false;
   }
   errorMessage.value = '';
   successMessage.value = '';
};

const saveVendor = async () => {
   isSaving.value = true;
   errorMessage.value = '';
   successMessage.value = '';

   try {
      if (!formData.value.name.trim()) {
         errorMessage.value = t('vendors.errors.nameRequired');
         return;
      }

      const payload = {
         name: formData.value.name.trim(),
         email: formData.value.email?.trim() || null,
         phone: formData.value.phone?.trim() || null,
         website: formData.value.website?.trim() || null,
      };

      if (isNewVendor.value) {
         const created = await createVendor(payload);
         successMessage.value = t('vendors.messages.createSuccess');
         setTimeout(() => {
            router.push(`/vendors/${created.id}`);
         }, 800);
      } else {
         if (!vendorId.value) {
            errorMessage.value = t('vendors.errors.unknown');
            return;
         }
         await updateVendor(vendorId.value, payload);

         successMessage.value = t('vendors.messages.updateSuccess');
         showForm.value = false;
      }
   } catch (error) {
      errorMessage.value = t('vendors.errors.generic', {
         message: error instanceof Error ? error.message : t('vendors.errors.unknown'),
      });
   } finally {
      isSaving.value = false;
   }
};

const deleteVendor = async () => {
   if (!vendorId.value) return;
   if (!confirm(t('vendors.confirmDelete'))) {
      return;
   }

   isDeleting.value = true;
   errorMessage.value = '';
   successMessage.value = '';

   try {
      await deleteVendorApi(vendorId.value);

      successMessage.value = t('vendors.messages.deleteSuccess');
      setTimeout(() => {
         router.push('/vendors');
      }, 600);
   } catch (error) {
      errorMessage.value = t('vendors.errors.generic', {
         message: error instanceof Error ? error.message : t('vendors.errors.unknown'),
      });
   } finally {
      isDeleting.value = false;
   }
};

onMounted(() => {
   loadVendor();
   loadBrandFamilyData();
});
</script>
