<template>
   <div class="bg-slate-50 border-b border-slate-200 shadow-sm mb-4">
      <div class="max-w-7xl mx-auto px-6 py-3">
         <div class="flex flex-wrap items-center justify-between gap-3">
            <nav class="flex flex-wrap gap-2">
               <RouterLink
                  v-for="item in items"
                  :key="item.label"
                  :to="item.path"
                  class="px-3 py-1.5 rounded text-sm font-medium transition"
                  :class="
                     isActive(item)
                        ? 'bg-blue-600 text-white'
                        : 'text-slate-700 hover:text-slate-900 hover:bg-slate-200'
                  "
               >
                  {{ item.label }}
               </RouterLink>
            </nav>
            <div v-if="$slots.actions" class="flex items-center gap-2">
               <slot name="actions" />
            </div>
         </div>
      </div>
   </div>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router';

type NavItem = {
   label: string;
   path: string;
   matchChildren?: boolean;
   exact?: boolean;
   excludeStartsWith?: string[];
};

type Props = {
   items: NavItem[];
};

defineProps<Props>();

const route = useRoute();

const isActive = (item: NavItem) => {
   if (route.path === item.path) return true;
   if (item.excludeStartsWith?.some((prefix) => route.path.startsWith(prefix))) {
      return false;
   }
   if (item.exact) return false;
   if (item.matchChildren && route.path.startsWith(item.path + '/')) return true;
   return false;
};
</script>
