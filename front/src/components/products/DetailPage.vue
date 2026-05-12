<template>
   <div class="p-6 max-w-4xl mx-auto">
      <div class="flex items-center justify-between mb-6">
         <div>
            <div class="text-sm text-gray-500">Product Detail</div>
            <h1 class="text-3xl font-bold text-gray-900">
               {{ product?.refciale || 'Product' }}
            </h1>
         </div>
         <RouterLink
            to="/products"
            class="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200"
         >
            Back to Products
         </RouterLink>
      </div>

      <div v-if="error" class="text-red-600 bg-red-50 p-4 rounded-lg mb-6">
         {{ error }}
      </div>

      <div v-if="loading" class="bg-white rounded-lg shadow p-6 text-gray-600">
         Loading product...
      </div>

      <div v-else-if="!product" class="bg-white rounded-lg shadow p-6 text-gray-600">
         Product not found.
      </div>

      <div v-else class="bg-white rounded-lg shadow p-6">
         <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
               <div class="text-sm text-gray-500">Ref. Ciale</div>
               <div class="text-lg font-mono text-gray-900">{{ product.refciale }}</div>
            </div>
            <div>
               <div class="text-sm text-gray-500">Marque</div>
               <div class="text-lg text-gray-900">{{ product.marque || '-' }}</div>
            </div>
            <div class="md:col-span-2">
               <div class="text-sm text-gray-500">Description</div>
               <div class="text-gray-900">{{ product.libelle240 || '-' }}</div>
            </div>
            <div>
               <div class="text-sm text-gray-500">Tarif</div>
               <div class="text-lg font-semibold text-gray-900">
                  {{ formatPrice(product.tarif) }}
               </div>
            </div>
            <div>
               <div class="text-sm text-gray-500">Gamme</div>
               <div class="text-gray-900">{{ product.gamme || '-' }}</div>
            </div>
            <div>
               <div class="text-sm text-gray-500">Quantity</div>
               <div class="text-gray-900">{{ product.qt ?? '-' }}</div>
            </div>
         </div>

         <div v-if="rawPayload" class="mt-6">
            <div class="text-sm text-gray-500 mb-2">Raw Payload</div>
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
import { apiUrl } from '../../utils/api';

interface Product {
   id: string | number;
   marque?: string;
   refciale?: string;
   libelle240?: string;
   tarif?: string | number;
   gamme?: string;
   qt?: string | number;
}

const QDRANT_API_URL = apiUrl('/api/qdrant');
const COLLECTION_NAME = 'test_commerce_vectors';

const route = useRoute();
const product = ref<Product | null>(null);
const loading = ref(false);
const error = ref('');
const rawPayload = ref('');

async function loadProduct() {
   const routeId = route.params.id;
   const id = Array.isArray(routeId) ? routeId[0] : routeId;
   if (!id) {
      error.value = 'Missing product id.';
      return;
   }

   loading.value = true;
   error.value = '';

   try {
      const url = new URL(QDRANT_API_URL);
      url.searchParams.set('action', 'retrieve');
      url.searchParams.set('collection', COLLECTION_NAME);
      url.searchParams.set('ids', JSON.stringify([id]));
      url.searchParams.set('with_payload', 'true');

      const response = await fetch(url.toString());
      if (!response.ok) {
         const text = await response.text();
         throw new Error(`API error ${response.status}: ${text}`);
      }

      const data = await response.json();
      const point = Array.isArray(data?.points) ? data.points[0] : null;

      if (!point) {
         product.value = null;
         return;
      }

      product.value = {
         id: point.id,
         marque: point.payload?.marque || '',
         refciale: point.payload?.refciale || '',
         libelle240: point.payload?.libelle240 || '',
         tarif: point.payload?.tarif || '',
         gamme: point.payload?.gamme || '',
         qt: point.payload?.qt ?? '',
      };

      rawPayload.value = JSON.stringify(point.payload || {}, null, 2);
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
