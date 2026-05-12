<template>
   <ProductsSubHeader />
   <div class="max-w-xl mx-auto p-6">
      <h1 class="text-2xl font-bold mb-4">{{ isEdit ? 'Edit Product' : 'Create Product' }}</h1>
      <form @submit.prevent="handleSubmit">
         <div class="mb-4">
            <label class="block mb-1 font-medium">Marque</label>
            <select v-model="form.marque" class="w-full border rounded px-3 py-2" required>
               <option value="" disabled>Select a brand</option>
               <option v-for="brand in brands" :key="brand.id" :value="brand.name">
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
               class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
            >
               {{ isEdit ? 'Update' : 'Create' }}
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

const form = ref({
   marque: '',
   refciale: '',
   libelle240: '',
   tarif: 0,
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
            marque: data.marque || '',
            refciale: data.refciale || '',
            libelle240: data.libelle240 || '',
            tarif: data.tarif || 0,
            family_codes: Array.isArray(data.family_codes) ? data.family_codes : [],
            vector_text: data.vector_text || '',
         };
         familyCodesInput.value = form.value.family_codes.join(',');
      }
   }
});

async function handleSubmit() {
   // Parse family codes from input
   form.value.family_codes = familyCodesInput.value
      .split(',')
      .map((c) => c.trim())
      .filter((c) => c);

   if (isEdit) {
      // Update product (replace with real API call)
      await fetch(`/api/products/${route.params.id}`, {
         method: 'PUT',
         headers: { 'Content-Type': 'application/json' },
         body: JSON.stringify(form.value),
      });
   } else {
      // Create product (replace with real API call)
      await fetch('/api/products', {
         method: 'POST',
         headers: { 'Content-Type': 'application/json' },
         body: JSON.stringify(form.value),
      });
   }
}
</script>

<style scoped></style>
