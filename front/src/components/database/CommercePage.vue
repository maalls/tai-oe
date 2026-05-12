<template>
   <div class="p-8 max-w-7xl mx-auto">
      <!-- Column Filter Form -->
      <div class="bg-white rounded-lg shadow p-6 mb-6">
         <details class="cursor-pointer">
            <summary class="font-semibold text-blue-600 hover:text-blue-700 select-none">
               🔍 Filter Columns
            </summary>
            <div class="mt-4 p-4 bg-blue-50 rounded">
               <div class="mb-4">
                  <label class="block text-sm font-medium mb-3">Select columns to display:</label>
                  <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                     <label
                        v-for="column in allColumns"
                        :key="column"
                        class="flex items-center gap-2 cursor-pointer"
                     >
                        <input
                           type="checkbox"
                           :value="column"
                           v-model="selectedColumns"
                           class="w-4 h-4 rounded"
                        />
                        <span class="text-sm">{{ column }}</span>
                     </label>
                  </div>
               </div>
               <div class="flex gap-2">
                  <button
                     @click="selectAllColumns"
                     class="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 transition"
                  >
                     Select All
                  </button>
                  <button
                     @click="deselectAllColumns"
                     class="px-3 py-1 text-sm bg-gray-500 text-white rounded hover:bg-gray-600 transition"
                  >
                     Deselect All
                  </button>
               </div>
            </div>
         </details>
      </div>

      <!-- Table data display -->
      <div class="bg-white rounded-lg shadow p-6">
         <h2 class="text-xl font-semibold mb-4">Commerce</h2>
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
                        v-for="column in selectedColumns"
                        :key="column"
                        class="px-4 py-2 text-left"
                     >
                        {{ column }}
                     </th>
                  </tr>
               </thead>
               <tbody class="divide-y divide-gray-200">
                  <tr v-for="(row, idx) in tableData.rows" :key="idx">
                     <td v-for="column in selectedColumns" :key="column" class="px-4 py-2">
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
import { ref, onMounted, watch, computed } from 'vue';

const currentTable = ref('fabdis_commerce');

const tableData = ref<any>(null);
const loadingData = ref(false);
const dataError = ref('');
const selectedColumns = ref<string[]>([]);

const allColumns = computed(() => tableData.value?.columns || []);

function getStorageKey(tableName: string) {
   return `commerce_page_selected_columns_${tableName}`;
}

function loadSavedColumns(tableName: string) {
   try {
      const saved = localStorage.getItem(getStorageKey(tableName));
      if (saved) {
         return JSON.parse(saved);
      }
   } catch (e) {
      console.error('Failed to load saved columns:', e);
   }
   return null;
}

function saveColumns(tableName: string, columns: string[]) {
   try {
      localStorage.setItem(getStorageKey(tableName), JSON.stringify(columns));
   } catch (e) {
      console.error('Failed to save columns:', e);
   }
}

onMounted(() => {
   const saved = loadSavedColumns(currentTable.value);
   if (saved && saved.length > 0) {
      selectedColumns.value = saved;
   }
   loadTableData();
});

watch(
   tableData,
   (newData) => {
      if (newData?.columns) {
         // Check if we have saved columns for this table
         const saved = loadSavedColumns(currentTable.value);
         if (saved && saved.length > 0) {
            // Use saved columns if they're still valid
            const validColumns = saved.filter((col: string) => newData.columns.includes(col));
            selectedColumns.value = validColumns.length > 0 ? validColumns : [...newData.columns];
         } else {
            // Auto-select all columns when data loads
            selectedColumns.value = [...newData.columns];
         }
      }
   },
   { immediate: true }
);

watch(
   selectedColumns,
   (newColumns) => {
      saveColumns(currentTable.value, newColumns);
   },
   { deep: true }
);

async function loadTableData() {
   loadingData.value = true;
   dataError.value = '';
   tableData.value = null;

   try {
      const response = await fetch(
         `/api/csv/query?table=${encodeURIComponent(currentTable.value)}`
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

function selectAllColumns() {
   selectedColumns.value = [...allColumns.value];
}

function deselectAllColumns() {
   selectedColumns.value = [];
}
</script>
