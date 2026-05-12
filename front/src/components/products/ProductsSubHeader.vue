<template>
   <NavHeader :items="navItems" />
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useI18n } from '../../i18n/useI18n';
import NavHeader from '../shared/NavHeader.vue';

const { t } = useI18n();

const navItems = computed(() => [
   {
      label: t('products.subnav.vendors'),
      path: '/vendors',
      matchChildren: true,
      excludeStartsWith: ['/vendors/brand', '/vendors/family'],
   },
   { label: t('products.subnav.brand'), path: '/vendors/brand', matchChildren: true },
   { label: t('products.subnav.family'), path: '/vendors/family', matchChildren: true },
   { label: t('products.subnav.products'), path: '/products', matchChildren: true },
]);
</script>
