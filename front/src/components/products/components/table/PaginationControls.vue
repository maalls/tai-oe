<template>
   <div v-if="totalPages > 1" class="flex items-center gap-1">
      <button
         type="button"
         class="px-2 py-1 text-xs rounded border border-gray-300 text-gray-700 hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
         :disabled="currentPage <= 1"
         aria-label="Previous page"
         @click="goToPage(currentPage - 1)"
      >
         &lt;
      </button>
      <button
         v-for="page in visiblePages"
         :key="page"
         type="button"
         class="px-2 py-1 text-xs rounded border cursor-pointer"
         :class="
            page === currentPage
               ? 'bg-gray-800 border-gray-800 text-white'
               : 'border-gray-300 text-gray-700 hover:bg-gray-100'
         "
         @click="goToPage(page)"
      >
         {{ page }}
      </button>
      <button
         type="button"
         class="px-2 py-1 text-xs rounded border border-gray-300 text-gray-700 hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
         :disabled="currentPage >= totalPages"
         aria-label="Next page"
         @click="goToPage(currentPage + 1)"
      >
         &gt;
      </button>
   </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

const props = defineProps<{
   currentPage: number;
   totalPages: number;
   goToPage: (page: number) => void;
}>();

const visiblePages = computed(() => {
   const total = props.totalPages;
   const current = props.currentPage;
   if (total <= 7) {
      return Array.from({ length: total }, (_, i) => i + 1);
   }

   let start = Math.max(1, current - 3);
   let end = Math.min(total, start + 6);

   if (end - start < 6) {
      start = Math.max(1, end - 6);
   }

   return Array.from({ length: end - start + 1 }, (_, i) => start + i);
});
</script>
