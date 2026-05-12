<template>
   <div>
      <AdminNavHeader />
      <div class="p-8 max-w-7xl mx-auto">
         <!-- Tab Navigation -->
         <div class="bg-white rounded-lg shadow mb-6">
            <div class="border-b border-gray-200">
               <nav class="flex -mb-px">
                  <router-link
                     to="/admin/database/cartouches"
                     :class="[
                        'px-6 py-3 text-sm font-medium border-b-2 transition-colors',
                        $route.path === '/admin/database/cartouches'
                           ? 'border-blue-500 text-blue-600'
                           : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
                     ]"
                  >
                     Cartouches
                  </router-link>
                  <router-link
                     to="/admin/database/commerce"
                     :class="[
                        'px-6 py-3 text-sm font-medium border-b-2 transition-colors',
                        $route.path === '/admin/database/commerce'
                           ? 'border-blue-500 text-blue-600'
                           : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
                     ]"
                  >
                     Commerce
                  </router-link>
               </nav>
            </div>
         </div>

         <!-- Child route content -->
         <router-view />
      </div>
   </div>
</template>

<script setup lang="ts">
import AdminNavHeader from '../../AdminNavHeader.vue';
</script>
