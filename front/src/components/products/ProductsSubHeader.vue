<template>
   <NavHeader :items="navItems" />
</template>

<script setup lang="ts">
import { computed } from 'vue';
import NavHeader from '../shared/NavHeader.vue';

const navItems = computed(() => [
   {
      label: 'Vendors',
      path: '/vendors',
      matchChildren: true,
      excludeStartsWith: ['/vendors/brand', '/vendors/family'],
   },
   { label: 'Brand', path: '/vendors/brand', matchChildren: true },
   { label: 'Family', path: '/vendors/family', matchChildren: true },
   { label: 'Products', path: '/products', matchChildren: true },
]);
</script>
