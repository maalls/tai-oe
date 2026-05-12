<template>
   <NavHeader :items="navItems">
      <template #actions>
         <slot name="actions" />
      </template>
   </NavHeader>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useI18n } from '../../i18n/useI18n';
import NavHeader from '../shared/NavHeader.vue';

const { t } = useI18n();

const navItems = computed(() => [
   { label: t('nav.client'), path: '/client', matchChildren: true },
   { label: t('nav.contacts'), path: '/contacts', matchChildren: true },
   { label: t('nav.accounts'), path: '/accounts', matchChildren: true },
]);
</script>
