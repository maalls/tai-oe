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

            <div v-if="isBrandsLoading" class="text-sm text-gray-500">
               {{ t('vendors.relatedBrands.loading') }}
            </div>
            <div v-else-if="brandsErrorMessage" class="text-sm text-red-600">
               {{ brandsErrorMessage }}
            </div>
            <div v-else-if="relatedBrands.length === 0" class="text-sm text-gray-500">
               {{ t('vendors.relatedBrands.empty') }}
            </div>
            <div v-else class="list-card">
               <div class="list-table-wrap">
                  <table class="list-table">
                     <thead>
                        <tr>
                           <th>{{ t('vendors.relatedBrands.columns.name') }}</th>
                           <th>{{ t('vendors.relatedBrands.columns.marque') }}</th>
                           <th class="list-table-right">
                              {{ t('products.brand.columns.minimumMargin') }}
                           </th>
                           <th class="list-table-right">
                              {{ t('products.brand.columns.targetMargin') }}
                           </th>
                           <th class="list-table-right">
                              {{ t('products.brand.columns.products') }}
                           </th>
                        </tr>
                     </thead>
                     <tbody>
                        <tr v-for="brand in relatedBrands" :key="brand.id">
                           <td class="font-medium text-gray-900">
                              <router-link
                                 :to="`/vendors/brand/${brand.id}`"
                                 class="list-table-link"
                              >
                                 {{ brand.name || brand.marque || '-' }}
                              </router-link>
                           </td>
                           <td class="list-table-muted">
                              <router-link
                                 :to="`/vendors/brand/${brand.id}`"
                                 class="list-table-link"
                              >
                                 {{ brand.marque || '-' }}
                              </router-link>
                           </td>
                           <td class="list-table-muted list-table-right">
                              {{ brand.minimum_margin }}%
                           </td>
                           <td class="list-table-muted list-table-right">
                              {{ brand.target_margin }}%
                           </td>
                           <td class="list-table-muted list-table-right">
                              {{ brand.product_count?.toLocaleString(locale) ?? '0' }}
                           </td>
                        </tr>
                     </tbody>
                  </table>
               </div>
            </div>
         </div>
      </div>
   </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { supabase } from '../../lib/supabase';
import { useI18n } from '../../i18n/useI18n';
import { useDddApi } from '../../composables/useDddApi';
import ProductsSubHeader from '../products/ProductsSubHeader.vue';
import Breadcrumb from '../common/Breadcrumb.vue';

interface Brand {
   id: string;
   name?: string | null;
   marque?: string | null;
   website?: string | null;
   target_margin?: number | null;
   minimum_margin?: number | null;
   product_count?: number;
}

const route = useRoute();
const router = useRouter();
const { t, locale } = useI18n();
const { fetchDddJson } = useDddApi();

const isNewVendor = computed(() => route.params.id === 'new');
const vendorId = computed(() => (isNewVendor.value ? null : (route.params.id as string)));

const isLoading = ref(false);
const isSaving = ref(false);
const isDeleting = ref(false);
const errorMessage = ref('');
const successMessage = ref('');
const brandsErrorMessage = ref('');
const isBrandsLoading = ref(false);
const relatedBrands = ref<Brand[]>([]);
const showForm = ref(false);

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

      const result = await fetchDddJson<{ status: string; vendor?: any }>('vendor', {
         vendor_id: vendorId.value,
      });

      if (result?.status !== 'ok' || !result?.vendor) {
         throw new Error('Failed loading vendor');
      }

      const vendor = result.vendor as any;
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

const loadRelatedBrands = async () => {
   if (isNewVendor.value || !vendorId.value) {
      relatedBrands.value = [];
      return;
   }

   isBrandsLoading.value = true;
   brandsErrorMessage.value = '';

   try {
      const { data, error } = await supabase
         .from('brand')
         .select('*, family(product_family(count))')
         .eq('vendor_id', vendorId.value)
         .order('name', { ascending: true });

      if (error) {
         brandsErrorMessage.value = t('vendors.relatedBrands.loadFailed', {
            message: error.message,
         });
         relatedBrands.value = [];
         return;
      }

      relatedBrands.value = (data || []).map((b: any) => ({
         ...b,
         product_count: (b.family || []).reduce(
            (sum: number, f: any) => sum + (f.product_family?.[0]?.count ?? 0),
            0
         ),
      }));
   } catch (error) {
      brandsErrorMessage.value = t('vendors.relatedBrands.loadFailed', {
         message: error instanceof Error ? error.message : t('vendors.errors.unknown'),
      });
      relatedBrands.value = [];
   } finally {
      isBrandsLoading.value = false;
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
         updated_at: new Date().toISOString(),
      };

      if (isNewVendor.value) {
         const { data, error } = await (supabase.from('vendor') as any).insert([payload]).select();

         if (error) {
            errorMessage.value = t('vendors.errors.createFailed', { message: error.message });
            return;
         }

         const rows = (data as any[]) || [];
         if (rows.length > 0) {
            successMessage.value = t('vendors.messages.createSuccess');
            setTimeout(() => {
               router.push(`/vendors/${rows[0].id}`);
            }, 800);
         }
      } else {
         if (!vendorId.value) {
            errorMessage.value = t('vendors.errors.unknown');
            return;
         }
         const { error } = await (supabase.from('vendor') as any)
            .update(payload)
            .eq('id', vendorId.value);

         if (error) {
            errorMessage.value = t('vendors.errors.updateFailed', { message: error.message });
            return;
         }

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
      const { error } = await supabase.from('vendor').delete().eq('id', vendorId.value);

      if (error) {
         errorMessage.value = t('vendors.errors.deleteFailed', { message: error.message });
         return;
      }

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
   loadRelatedBrands();
});
</script>
