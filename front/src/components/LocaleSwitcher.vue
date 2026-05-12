<template>
   <div class="flex items-center gap-2">
      <button
         v-for="lang in availableLocales"
         :key="lang"
         @click="setLocale(lang)"
         :class="[
            'px-3 py-1 text-sm rounded-md transition',
            locale === lang
               ? 'bg-blue-600 text-white'
               : 'bg-gray-100 text-gray-700 hover:bg-gray-200',
         ]"
      >
         {{ lang.toUpperCase() }}
      </button>
   </div>
</template>

<script setup lang="ts">
import { useI18n } from '../i18n/useI18n';
import { LOCALE_STORAGE_KEY } from '../i18n/index';

const { locale, availableLocales } = useI18n();

const setLocale = (lang: string) => {
   locale.value = lang as 'en' | 'fr';
   localStorage.setItem(LOCALE_STORAGE_KEY, lang);
};
</script>
