<template>
   <div>
      <ProductsSubHeader />
      <div class="list-page-shell list-page-stack">
         <BrandListTable
            :brands="brands"
            :families="families"
            :isLoading="isLoading"
            :errorMessage="errorMessage"
         />
      </div>
   </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import ProductsSubHeader from './ProductsSubHeader.vue';
import { useBrandFamilyData } from './useBrandFamilyData';
import BrandListTable from './components/BrandListTable.vue';

const { brands, families, isLoading, errorMessage, loadData } = useBrandFamilyData();

onMounted(() => {
   loadData();
});
</script>
