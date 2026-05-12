<template>
   <div class="p-8 max-w-7xl mx-auto">
      <ChatPanel :showModelSelector="true" :context="{ section: 'global' }" :forceOpen="true" />

      <!-- API Info -->
      <div class="p-4 text-center text-xs text-gray-500">
         LLM: {{ LLM_API_URL }} · DB: {{ DB_API_URL }}
      </div>
   </div>
</template>

<script setup lang="ts">
import { LLM_API_URL, DB_API_URL } from './types';
import ChatPanel from './ChatPanel.vue';
</script>
