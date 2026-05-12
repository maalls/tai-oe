<template>
   <div>
      <ProductsSubHeader />
      <NavHeader :items="navItems" />
      <div class="p-6 max-w-7xl mx-auto">
         <router-view />
      </div>
   </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import ProductsSubHeader from '../ProductsSubHeader.vue';
import NavHeader from '../../shared/NavHeader.vue';

const navItems = computed(() => [
   { label: 'Brand', path: '/products/cms/brand', matchChildren: true },
   { label: 'Family', path: '/products/cms/family', matchChildren: true },
]);
</script>
