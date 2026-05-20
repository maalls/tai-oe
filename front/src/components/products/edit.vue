<template>
   <ProductsSubHeader />
   <div class="max-w-xl mx-auto p-6">
      <h1 class="text-2xl font-bold mb-4">{{ isEdit ? 'Edit Product' : 'Create Product' }}</h1>
      <div v-if="errorMessage" class="mb-4 rounded-lg bg-red-50 p-4 text-red-700">
         {{ errorMessage }}
      </div>
      <div v-if="successMessage" class="mb-4 rounded-lg bg-green-50 p-4 text-green-700">
         {{ successMessage }}
      </div>
      <form @submit.prevent="handleSubmit">
         <div class="mb-4">
            <label class="block mb-1 font-medium">Marque</label>
            <select v-model="form.brand_id" class="w-full border rounded px-3 py-2" required>
               <option value="" disabled>Select a brand</option>
               <option v-for="brand in brands" :key="brand.id" :value="brand.id">
                  {{ brand.vendor_name ? brand.vendor_name + ' / ' : '' }}{{ brand.name }}
               </option>
            </select>
         </div>
         <div class="mb-4">
            <label class="block mb-1 font-medium">Refciale</label>
            <input
               v-model="form.refciale"
               type="text"
               class="w-full border rounded px-3 py-2"
               required
            />
         </div>
         <div class="mb-4">
            <label class="block mb-1 font-medium">Libellé 240</label>
            <input
               v-model="form.libelle240"
               type="text"
               class="w-full border rounded px-3 py-2"
               required
            />
         </div>
         <div class="mb-4">
            <label class="block mb-1 font-medium">Tarif</label>
            <input
               v-model.number="form.tarif"
               type="number"
               min="0"
               step="0.01"
               class="w-full border rounded px-3 py-2"
               required
            />
         </div>
         <div class="mb-4">
            <label class="block mb-1 font-medium">Batch</label>
            <input
               v-model.number="form.batch"
               type="number"
               min="1"
               step="1"
               class="w-full border rounded px-3 py-2"
               required
            />
         </div>
         <div class="mb-4">
            <label class="block mb-1 font-medium">Family Codes (comma separated)</label>
            <input
               v-model="familyCodesInput"
               type="text"
               class="w-full border rounded px-3 py-2"
               placeholder="e.g., D,D11,D11B9"
            />
         </div>
         <div class="mb-4">
            <label class="block mb-1 font-medium">Vector Text</label>
            <textarea
               v-model="form.vector_text"
               class="w-full border rounded px-3 py-2"
               rows="2"
            ></textarea>
         </div>
         <div class="flex gap-2">
            <button
               type="submit"
               :disabled="isSaving"
               class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
            >
               {{ isSaving ? 'Saving...' : isEdit ? 'Update' : 'Create' }}
            </button>
            <button
               v-if="isEdit"
               type="button"
               :disabled="isDeleting"
               class="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700 disabled:opacity-50"
               @click="handleDelete"
            >
               {{ isDeleting ? 'Deleting...' : 'Delete' }}
            </button>
            <router-link
               to="/products"
               class="bg-gray-300 text-gray-800 px-4 py-2 rounded hover:bg-gray-400"
               >Cancel</router-link
            >
         </div>
      </form>
   </div>
</template>

<script setup>
import ProductsSubHeader from './ProductsSubHeader.vue';
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useBrandFamilyData } from './useBrandFamilyData';

const route = useRoute();
const router = useRouter();
const isEdit = !!route.params.id;
const isSaving = ref(false);
const isDeleting = ref(false);
const errorMessage = ref('');
const successMessage = ref('');

const form = ref({
   brand_id: '',
   marque: '',
   refciale: '',
   libelle240: '',
   tarif: 0,
   batch: 1,
   family_codes: [],
   vector_text: '',
});

const familyCodesInput = ref('');

// Brand select
const { brands, loadData: loadBrandData } = useBrandFamilyData();
onMounted(() => {
   loadBrandData();
});

onMounted(async () => {
   if (isEdit) {
      // Fetch product data by ID (replace with real API call)
      const res = await fetch(`/api/products/${route.params.id}`);
      if (res.ok) {
         const data = await res.json();
         form.value = {
            brand_id: data.brand_id || '',
            marque: data.marque || '',
            refciale: data.refciale || '',
            libelle240: data.libelle240 || '',
            tarif: data.tarif || 0,
            batch: Number.isFinite(Number(data.batch)) ? Number(data.batch) : 1,
            family_codes: Array.isArray(data.family_codes) ? data.family_codes : [],
            vector_text: data.vector_text || '',
         };
         familyCodesInput.value = form.value.family_codes.join(',');
      }
   } else {
      const queryRefciale = route.query.refciale;
      if (typeof queryRefciale === 'string' && queryRefciale.trim().length > 0) {
         form.value.refciale = queryRefciale.trim();
      }

      const queryBrandId = route.query.brand_id;
      if (typeof queryBrandId === 'string' && queryBrandId.trim().length > 0) {
         form.value.brand_id = queryBrandId.trim();
      }
   }
});

async function handleSubmit() {
   if (isSaving.value) return;

   isSaving.value = true;
   errorMessage.value = '';
   successMessage.value = '';

   // Parse family codes from input
   form.value.family_codes = familyCodesInput.value
      .split(',')
      .map((c) => c.trim())
      .filter((c) => c);

   const selectedBrand = brands.value.find((brand) => brand.id === form.value.brand_id);
   form.value.marque = selectedBrand?.name || form.value.marque;

   try {
      const response = await fetch(isEdit ? `/api/products/${route.params.id}` : '/api/products', {
         method: isEdit ? 'PUT' : 'POST',
         headers: { 'Content-Type': 'application/json' },
         body: JSON.stringify(form.value),
      });

      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
         throw new Error(payload.message || 'Unable to save product');
      }

      successMessage.value = isEdit
         ? 'Product updated successfully.'
         : 'Product created successfully.';

      if (!isEdit) {
         const createdProductId = payload?.product?.id || payload?.id;
         if (createdProductId) {
            setTimeout(() => {
               router.push(`/products/${createdProductId}`);
            }, 600);
         }
      }
   } catch (error) {
      errorMessage.value = error instanceof Error ? error.message : 'Unable to save product';
   } finally {
      isSaving.value = false;
   }
}

async function handleDelete() {
   if (!isEdit || isDeleting.value) return;
   if (!window.confirm('Delete this product? This action cannot be undone.')) {
      return;
   }

   isDeleting.value = true;
   errorMessage.value = '';
   successMessage.value = '';

   try {
      const response = await fetch(`/api/products/${route.params.id}`, {
         method: 'DELETE',
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
         throw new Error(payload.message || 'Unable to delete product');
      }

      successMessage.value = 'Product deleted successfully.';
      setTimeout(() => {
         router.push('/products');
      }, 600);
   } catch (error) {
      errorMessage.value = error instanceof Error ? error.message : 'Unable to delete product';
   } finally {
      isDeleting.value = false;
   }
}
</script>

<style scoped></style>
