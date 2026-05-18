<template>
   <div class="p-6 max-w-4xl mx-auto">
      <div class="flex items-center justify-between mb-6">
         <div>
            <div class="text-sm text-gray-500">{{ t('products.detail.title') }}</div>
            <h1 class="text-3xl font-bold text-gray-900">
               {{ product?.refciale || t('products.detail.fallbackTitle') }}
            </h1>
         </div>
         <RouterLink
            to="/products"
            class="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200"
         >
            {{ t('products.detail.back') }}
         </RouterLink>
      </div>

      <div v-if="error" class="text-red-600 bg-red-50 p-4 rounded-lg mb-6">
         {{ error }}
      </div>

      <div v-if="loading" class="bg-white rounded-lg shadow p-6 text-gray-600">
         {{ t('products.detail.loading') }}
      </div>

      <div v-else-if="!product" class="bg-white rounded-lg shadow p-6 text-gray-600">
         {{ t('products.detail.notFound') }}
      </div>

      <div v-else class="bg-white rounded-lg shadow p-6">
         <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
               <div class="text-sm text-gray-500">{{ t('products.detail.refciale') }}</div>
               <div class="text-lg font-mono text-gray-900">{{ product.refciale }}</div>
            </div>
            <div>
               <div class="text-sm text-gray-500">{{ t('products.detail.brand') }}</div>
               <div class="text-lg text-gray-900">{{ product.marque || '-' }}</div>
            </div>
            <div class="md:col-span-2">
               <div class="text-sm text-gray-500">{{ t('products.detail.description') }}</div>
               <div class="text-gray-900">{{ product.libelle240 || '-' }}</div>
            </div>
            <div>
               <div class="text-sm text-gray-500">{{ t('products.detail.tarif') }}</div>
               <div class="text-lg font-semibold text-gray-900">
                  {{ formatPrice(product.tarif) }}
               </div>
            </div>
            <div>
               <div class="text-sm text-gray-500">{{ t('products.detail.gamme') }}</div>
               <div class="text-gray-900">{{ product.gamme || '-' }}</div>
            </div>
            <div>
               <div class="text-sm text-gray-500">{{ t('products.detail.quantity') }}</div>
               <div class="text-gray-900">{{ product.qt ?? '-' }}</div>
            </div>
         </div>

         <div v-if="rawPayload" class="mt-6">
            <div class="text-sm text-gray-500 mb-2">{{ t('products.detail.rawPayload') }}</div>
            <pre class="bg-gray-50 border border-gray-200 rounded p-3 text-xs overflow-x-auto">{{
               rawPayload
            }}</pre>
         </div>
      </div>
   </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { getProduct } from '../../api/product';
import { useI18n } from '../../i18n/useI18n';

interface Product {
   id: string | number;
   marque?: string;
   refciale?: string;
   libelle240?: string;
   tarif?: string | number;
   gamme?: string;
   qt?: string | number;
}

const route = useRoute();
const { t } = useI18n();
const product = ref<Product | null>(null);
const loading = ref(false);
const error = ref('');
const rawPayload = ref('');

async function loadProduct() {
   const routeId = route.params.id;
   const id = Array.isArray(routeId) ? routeId[0] : routeId;
   if (!id) {
      error.value = t('products.detail.missingId');
      return;
   }

   loading.value = true;
   error.value = '';

   try {
      const data = await getProduct(String(id));

      if (!data) {
         product.value = null;
         return;
      }

      product.value = {
         id: data.id,
         marque: data.marque || '',
         refciale: data.refciale || '',
         libelle240: data.libelle240 || '',
         tarif: data.tarif ?? '',
         gamme: '',
         qt: '',
      };

      rawPayload.value = JSON.stringify(data, null, 2);
   } catch (e: any) {
      error.value = String(e?.message || e);
   } finally {
      loading.value = false;
   }
}

function formatPrice(price: string | number | undefined): string {
   if (price === undefined || price === null || price === '') return '-';
   const num = typeof price === 'string' ? parseFloat(price) : price;
   if (isNaN(num)) return '-';
   return (
      '€ ' + num.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
   );
}

onMounted(() => {
   loadProduct();
});
</script>
