<template>
   <div>
      <AdminNavHeader />
      <div class="p-6 max-w-3xl mx-auto">
         <h1 class="text-2xl font-bold mb-6">Add User</h1>
         <UserForm />
      </div>
   </div>
</template>

<script setup lang="ts">
import AdminNavHeader from '../../AdminNavHeader.vue';
import UserForm from './UserForm.vue';
</script>
