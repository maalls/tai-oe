<template>
   <nav class="">
      <ol class="flex items-center space-x-2 text-sm text-gray-600">
         <li v-for="(item, index) in items" :key="index" class="flex items-center">
            <router-link
               v-if="item.to && index < items.length - 1"
               :to="item.to"
               class="hover:text-blue-600 hover:underline"
            >
               {{ item.label }}
            </router-link>
            <span v-else :class="{ 'text-gray-900 font-medium': index === items.length - 1 }">
               {{ item.label }}
            </span>
            <span v-if="index < items.length - 1" class="mx-2 text-gray-400">/</span>
         </li>
      </ol>
   </nav>
</template>

<script setup lang="ts">
interface BreadcrumbItem {
   label: string;
   to?: string;
}

defineProps<{
   items: BreadcrumbItem[];
}>();
</script>
