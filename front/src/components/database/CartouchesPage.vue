<template>
   <div class="p-8 max-w-7xl mx-auto">
      <!-- Table data display -->
      <div class="bg-white rounded-lg shadow p-6">
         <h2 class="text-xl font-semibold mb-4">Cartouches</h2>
         <div v-if="loadingData" class="text-gray-600">Loading data...</div>
         <div v-else-if="dataError" class="text-red-600">{{ dataError }}</div>
         <div
            v-else-if="tableData && tableData.rows && tableData.rows.length > 0"
            class="overflow-x-auto"
         >
            <table class="w-full text-sm">
               <thead class="bg-gray-900 text-white">
                  <tr>
                     <th
                        v-for="column in tableData.columns"
                        :key="column"
                        class="px-4 py-2 text-left"
                     >
                        {{ column }}
                     </th>
                  </tr>
               </thead>
               <tbody class="divide-y divide-gray-200">
                  <tr v-for="(row, idx) in tableData.rows" :key="idx">
                     <td v-for="column in tableData.columns" :key="column" class="px-4 py-2">
                        {{ row[column] }}
                     </td>
                  </tr>
               </tbody>
            </table>
            <div class="mt-4 text-sm text-gray-600">Showing {{ tableData.rows.length }} rows</div>
         </div>
         <div v-else class="text-gray-600">No data in this table</div>
      </div>
   </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';

const tableData = ref<any>(null);
const loadingData = ref(false);
const dataError = ref('');

onMounted(() => {
   loadTableData();
});

async function loadTableData() {
   loadingData.value = true;
   dataError.value = '';
   tableData.value = null;

   try {
      const response = await fetch(
         `/api/csv/query?table=${encodeURIComponent('fabdis_cartouches')}`
      );
      const data = await response.json();
      console.log('Fetched table data:', data);
      tableData.value = data;
   } catch (e) {
      dataError.value = `Failed to load table data: ${e}`;
   } finally {
      loadingData.value = false;
   }
}
</script>
