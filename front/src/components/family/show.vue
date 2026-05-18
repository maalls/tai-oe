<template>
   <div>
      <ProductsSubHeader />
      <div class="p-6 max-w-5xl mx-auto space-y-6">
         <nav class="text-sm text-gray-600">
            <router-link to="/vendors/family" class="hover:text-gray-900"> Family </router-link>
            <span class="mx-2">/</span>
            <span class="text-gray-900">
               {{ family?.name || family?.code || family?.id || 'New' }}
            </span>
         </nav>
         <div class="flex items-center justify-between">
            <div>
               <h1 class="text-3xl font-bold text-gray-900">Family</h1>
               <p class="text-sm text-gray-500">Manage the details for this family.</p>
            </div>
            <button type="button" class="text-sm text-gray-600 hover:text-gray-900" @click="goBack">
               Back to Families
            </button>
         </div>
         <div v-if="errorMessage" class="rounded-lg bg-red-50 text-red-700 p-4">
            {{ errorMessage }}
         </div>

         <div class="bg-white rounded-lg border border-gray-200 shadow-sm">
            <div v-if="isLoading" class="p-6 text-gray-500">Loading...</div>
            <div v-else-if="!family" class="p-6 text-gray-500">Family not found.</div>
            <div v-else class="p-6 space-y-4">
               <div>
                  <div class="text-sm text-gray-500">Family</div>
                  <div class="text-lg font-semibold text-gray-900">{{ family.name }}</div>
               </div>
               <div class="grid gap-4 sm:grid-cols-2">
                  <div>
                     <div class="text-xs uppercase tracking-wide text-gray-400">Code</div>
                     <div class="text-sm text-gray-700">{{ family.code || '-' }}</div>
                  </div>
                  <div>
                     <div class="text-xs uppercase tracking-wide text-gray-400">Type</div>
                     <div class="text-sm text-gray-700">{{ family.type }}</div>
                  </div>
                  <div>
                     <div class="text-xs uppercase tracking-wide text-gray-400">Brand</div>
                     <div class="text-sm text-gray-700">{{ family.brand_id }}</div>
                  </div>
               </div>
            </div>
         </div>
      </div>
   </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import ProductsSubHeader from '../products/ProductsSubHeader.vue';
import { getFamily } from '../../api/family';

interface FamilyRecord {
   id: string;
   name: string;
   code: string | null;
   type: string | null;
   brand_id: string | null;
}

const family = ref<FamilyRecord | null>(null);
const errorMessage = ref<string | null>(null);
const isLoading = ref<boolean>(true);

const goBack = () => {
   router.back();
};

const router = useRouter();
const route = useRoute();

onMounted(async () => {
   isLoading.value = true;
   const familyId = String(route.params.id || '');
   try {
      family.value = await getFamily(familyId);
   } catch {
      errorMessage.value = 'Family not found.';
      isLoading.value = false;
      return;
   }
   isLoading.value = false;
});
</script>
