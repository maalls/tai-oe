<script setup lang="ts">
import Header from './components/header/Header.vue';
import { RouterView } from 'vue-router';
</script>

<template>
   <div class="flex flex-col h-screen">
      <Header />
      <main class="flex-1 overflow-auto">
         <RouterView />
      </main>
   </div>
</template>
