<template>
   <NavHeader :items="navItems" />
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useI18n } from '../../i18n/useI18n';
import NavHeader from '../shared/NavHeader.vue';

const { t } = useI18n();

const navItems = computed(() => [
   { label: t('nav.vendors'), path: '/vendors', matchChildren: true },
   { label: t('nav.products'), path: '/products', matchChildren: true },
]);
</script>
