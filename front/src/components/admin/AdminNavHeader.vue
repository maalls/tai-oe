<template>
   <NavHeader :items="navItems" />
</template>

<script setup lang="ts">
import { computed } from 'vue';
import NavHeader from '../shared/NavHeader.vue';

const navItems = computed(() => [
   {
      label: 'Dashboard',
      path: '/admin',
      exact: true,
   },
   { path: '/admin/source', label: 'Source', matchChildren: true },
   { path: '/admin/database', label: 'Database', matchChildren: true },
   { path: '/admin/flow', label: 'Flow', matchChildren: true },
]);
</script>
