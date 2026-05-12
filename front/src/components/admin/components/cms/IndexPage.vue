<template>
   <div>
      <AdminNavHeader />
      <NavHeader :items="navItems" />
      <div class="p-6 max-w-7xl mx-auto">
         <router-view />
      </div>
   </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import AdminNavHeader from '../../AdminNavHeader.vue';
import NavHeader from '../../../shared/NavHeader.vue';

const navItems = computed(() => [
   { label: 'Brand', path: '/admin/cms/brand', matchChildren: true },
   { label: 'Family', path: '/admin/cms/family', matchChildren: true },
]);
</script>
