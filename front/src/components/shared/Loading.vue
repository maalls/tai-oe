<template>
   <div class="flex justify-center items-center py-12">
      <div class="text-gray-500">{{ t('opportunities.loadingDots') }}</div>
   </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n';
const { t } = useI18n();
</script>
