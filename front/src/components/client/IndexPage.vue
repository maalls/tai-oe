<template>
   <div>
      <AccountNavHeader>
         <template #actions>
            <button
               class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium text-sm"
            >
               + Add Client
            </button>
         </template>
      </AccountNavHeader>
      <div class="p-6">
         <div class="mb-6">
            <h1 class="text-3xl font-bold text-gray-900">Clients</h1>
            <p class="text-gray-600 mt-2">Manage your clients</p>
         </div>

         <div class="bg-white rounded-lg border border-gray-200 shadow-sm p-12 text-center">
            <div class="text-gray-400 mb-4">
               <svg class="w-24 h-24 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                     stroke-linecap="round"
                     stroke-linejoin="round"
                     stroke-width="1.5"
                     d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
                  />
               </svg>
            </div>
            <h2 class="text-2xl font-semibold text-gray-700 mb-2">Client Management</h2>
            <p class="text-gray-500 max-w-md mx-auto">
               Client management page coming soon. This will be your central hub for managing all
               client relationships and information.
            </p>
         </div>
      </div>
   </div>
</template>

<script setup lang="ts">
import AccountNavHeader from '../account/AccountNavHeader.vue';
</script>
