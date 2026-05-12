<template>
   <transition
      enter-active-class="transition ease-in duration-200"
      leave-active-class="transition ease-out duration-200"
      enter-from-class="opacity-0 -translate-y-2"
      leave-to-class="opacity-0 -translate-y-2"
   >
      <div
         v-if="notification.message"
         :class="[
            'fixed top-12 left-1/2 -translate-x-1/2 z-50 max-w-lg w-full mx-auto',
            'px-4 py-2 rounded-lg border shadow-lg flex items-center justify-between',
            notification.type === 'error'
               ? 'bg-red-50 border-red-200 text-red-800'
               : notification.type === 'success'
                 ? 'bg-green-50 border-green-200 text-green-800'
                 : 'bg-blue-50 border-blue-200 text-blue-800',
         ]"
      >
         <div class="flex items-center gap-3 flex-1">
            <div v-if="notification.type === 'error'" class="text-red-600">
               <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path
                     fill-rule="evenodd"
                     d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                     clip-rule="evenodd"
                  />
               </svg>
            </div>
            <div v-else-if="notification.type === 'success'" class="text-green-600">
               <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path
                     fill-rule="evenodd"
                     d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                     clip-rule="evenodd"
                  />
               </svg>
            </div>
            <div v-else class="text-blue-600">
               <svg class="w-5 h-5 animate-spin" fill="currentColor" viewBox="0 0 20 20">
                  <path
                     fill-rule="evenodd"
                     d="M4.293 5.707a1 1 0 010-1.414l2-2a1 1 0 111.414 1.414L5.414 4H11a1 1 0 110 2H5.414l2.293 2.293a1 1 0 11-1.414 1.414l-4-4a1 1 0 010-1.414z"
                     clip-rule="evenodd"
                  />
               </svg>
            </div>
            <span>{{ notification.message }}</span>
         </div>
         <button
            v-if="notification.type === 'error'"
            @click="notification.message = ''"
            class="text-red-600 hover:text-red-700 ml-2 flex-shrink-0"
         >
            <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
               <path
                  fill-rule="evenodd"
                  d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                  clip-rule="evenodd"
               />
            </svg>
         </button>
      </div>
   </transition>
</template>

<script setup lang="ts">
defineProps<{
   notification: { message: string; type: 'info' | 'success' | 'error' };
}>();
</script>
