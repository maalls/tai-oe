<template>
   <AdminNavHeader />
   <div class="p-6 max-w-7xl mx-auto">
      <div class="">
         <select
            id="collection-select"
            :value="selectedCollection"
            @change="onCollectionChange"
            class="flex-1 max-w-sm px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
         >
            <option value="" disabled>-- Choose a collection --</option>
            <option v-for="collection in collections" :key="collection" :value="collection">
               {{ collection }}
            </option>
         </select>

         <button
            @click="loadCollections"
            class="ml-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-400 transition"
         >
            {{ loading ? '⏳ Refreshing...' : '🔄 Refresh' }}
         </button>
      </div>

      <div v-if="error" class="text-red-600">{{ error }}</div>
      <div v-else-if="collections.length === 0" class="text-gray-600">No collections found</div>

      <!-- Collection Details Section -->

      <div v-if="selectedCollection" class="bg-white rounded-lg shadow p-6">
         <!-- Loading Details -->
         <div v-if="loadingDetails" class="text-gray-600">Loading collection details...</div>

         <!-- Error Loading Details -->
         <div v-else-if="detailsError" class="text-red-600">{{ detailsError }}</div>

         <!-- Collection Info -->
         <div v-else-if="collectionInfo">
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
               <div class="bg-gray-50 p-4 rounded-lg">
                  <div class="text-sm text-gray-600">Total Points</div>
                  <div class="text-2xl font-bold text-gray-900">
                     {{ collectionInfo.points_count }}
                  </div>
               </div>
               <div class="bg-gray-50 p-4 rounded-lg">
                  <div class="text-sm text-gray-600">Vector Size</div>
                  <div class="text-2xl font-bold text-gray-900">
                     {{ collectionInfo.vector_size }}
                  </div>
               </div>
               <div class="bg-gray-50 p-4 rounded-lg">
                  <div class="text-sm text-gray-600">Status</div>
                  <div class="text-xl font-bold">
                     <span
                        class="px-2 py-1 rounded text-white"
                        :class="
                           collectionInfo.status === 'green'
                              ? 'bg-green-500'
                              : collectionInfo.status === 'yellow'
                                ? 'bg-yellow-500'
                                : 'bg-gray-500'
                        "
                     >
                        {{ collectionInfo.status }}
                     </span>
                  </div>
               </div>
               <div class="bg-gray-50 p-4 rounded-lg">
                  <div class="text-sm text-gray-600">Optimizer</div>
                  <div class="text-xl font-bold">
                     <span class="px-2 py-1 rounded text-white bg-blue-500">
                        {{ collectionInfo.optimizer_status }}
                     </span>
                  </div>
               </div>
            </div>

            <!-- Vector Search Section -->
            <div class="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
               <h3 class="text-lg font-semibold text-gray-900 mb-4">Vector Search</h3>

               <div class="flex gap-3 mb-4">
                  <input
                     v-model="searchQuery"
                     type="text"
                     placeholder="Enter search query..."
                     class="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                     @keydown.enter="performSearch"
                  />
                  <button
                     @click="performSearch"
                     :disabled="searchLoading || !searchQuery.trim()"
                     class="px-4 py-2 bg-blue-600 text-white rounded-md disabled:opacity-50 hover:bg-blue-700"
                  >
                     Search
                  </button>
               </div>

               <div v-if="searchError" class="text-red-600 mb-4">{{ searchError }}</div>

               <!-- Search Results -->
               <div v-if="searchResults.length > 0" class="space-y-3">
                  <div class="text-sm text-gray-600 mb-3">
                     Found {{ searchResults.length }} results
                  </div>
                  <div
                     v-for="(result, idx) in searchResults"
                     :key="idx"
                     class="p-3 bg-white rounded border border-blue-200"
                  >
                     <div class="flex justify-between items-start mb-2">
                        <div class="font-mono text-sm text-gray-600">ID: {{ result.id }}</div>
                        <div
                           class="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs font-semibold"
                        >
                           Score: {{ ((result.score ?? 0) * 100).toFixed(1) }}%
                        </div>
                     </div>
                     <div v-if="result.payload" class="text-sm text-gray-700">
                        <details class="cursor-pointer">
                           <summary class="font-semibold text-gray-900">
                              Payload ({{ Object.keys(result.payload).length }} fields)
                           </summary>
                           <pre
                              class="mt-2 p-2 bg-gray-50 rounded border text-xs overflow-x-auto"
                              >{{ JSON.stringify(result.payload, null, 2) }}</pre
                           >
                        </details>
                     </div>
                  </div>
               </div>
               <div v-else-if="searchLoading" class="text-gray-600">Searching...</div>
            </div>

            <!-- Scroll Filter Section -->
            <div class="mt-6 p-4 bg-green-50 border border-green-200 rounded-lg">
               <h3 class="text-lg font-semibold text-gray-900 mb-4">Scroll Points with Filters</h3>

               <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                  <div>
                     <label class="block text-sm font-medium text-gray-700 mb-1"
                        >Marque (Manufacturer)</label
                     >
                     <input
                        v-model="filterMarque"
                        type="text"
                        placeholder="e.g., YUASA"
                        class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
                     />
                  </div>
                  <div>
                     <label class="block text-sm font-medium text-gray-700 mb-1"
                        >Refciale (Part Number)</label
                     >
                     <input
                        v-model="filterRefciale"
                        type="text"
                        placeholder="e.g., NP7-12FR"
                        class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
                     />
                  </div>
                  <div>
                     <label class="block text-sm font-medium text-gray-700 mb-1"
                        >Tarif (Price)</label
                     >
                     <input
                        v-model="filterTarif"
                        type="text"
                        placeholder="e.g., 10.50"
                        class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
                     />
                  </div>
               </div>

               <div class="flex gap-3">
                  <button
                     @click="applyScrollFilter"
                     :disabled="scrollFilterLoading"
                     class="px-4 py-2 bg-green-600 text-white rounded-md disabled:opacity-50 hover:bg-green-700"
                  >
                     {{ scrollFilterLoading ? 'Filtering...' : 'Apply Filters' }}
                  </button>
                  <button
                     @click="clearScrollFilter"
                     :disabled="scrollFilterLoading"
                     class="px-4 py-2 bg-gray-400 text-white rounded-md disabled:opacity-50 hover:bg-gray-500"
                  >
                     Clear Filters
                  </button>
               </div>

               <div v-if="scrollFilterError" class="text-red-600 mt-3">{{ scrollFilterError }}</div>
            </div>

            <!-- Scroll Points -->
            <div class="mt-6">
               <h3 class="text-lg font-semibold text-gray-900 mb-4">
                  {{ isUsingFilter ? 'Filtered Results' : 'Sample Points' }}
               </h3>

               <div v-if="loadingPoints || scrollFilterLoading" class="text-gray-600">
                  Loading points...
               </div>
               <div v-else-if="pointsError" class="text-red-600">{{ pointsError }}</div>

               <!-- Show filtered results when filter is active -->
               <div v-else-if="isUsingFilter && scrollFilterResults.length > 0" class="space-y-4">
                  <div class="text-sm text-gray-600 mb-3">
                     Found {{ scrollFilterResults.length }} matching results
                  </div>
                  <div
                     v-for="(point, idx) in scrollFilterResults"
                     :key="idx"
                     class="p-4 bg-gray-50 rounded-lg border border-green-300"
                  >
                     <div class="flex justify-between items-start mb-2">
                        <div class="font-mono text-sm text-gray-600">ID: {{ point.id }}</div>
                     </div>
                     <div v-if="point.payload" class="text-sm text-gray-700">
                        <details class="cursor-pointer">
                           <summary class="font-semibold text-gray-900">
                              Payload ({{ Object.keys(point.payload).length }} fields)
                           </summary>
                           <pre class="mt-2 p-2 bg-white rounded border text-xs overflow-x-auto">{{
                              JSON.stringify(point.payload, null, 2)
                           }}</pre>
                        </details>
                     </div>
                  </div>
               </div>

               <!-- Show message when filter is active but no results -->
               <div v-else-if="isUsingFilter" class="text-gray-600">
                  No points match the filters
               </div>

               <!-- Show normal scroll points when no filter is active -->
               <div v-else-if="scrollPoints.length > 0" class="space-y-4">
                  <div
                     v-for="(point, idx) in scrollPoints"
                     :key="idx"
                     class="p-4 bg-gray-50 rounded-lg border border-gray-200"
                  >
                     <div class="flex justify-between items-start mb-2">
                        <div class="font-mono text-sm text-gray-600">ID: {{ point.id }}</div>
                        <button
                           @click="loadMorePoints"
                           class="text-xs px-2 py-1 bg-blue-600 text-white rounded hover:bg-blue-700"
                        >
                           Load More
                        </button>
                     </div>
                     <div v-if="point.payload" class="text-sm text-gray-700">
                        <details class="cursor-pointer">
                           <summary class="font-semibold text-gray-900">
                              Payload ({{ Object.keys(point.payload).length }} fields)
                           </summary>
                           <pre class="mt-2 p-2 bg-white rounded border text-xs overflow-x-auto">{{
                              JSON.stringify(point.payload, null, 2)
                           }}</pre>
                        </details>
                     </div>
                  </div>
               </div>
               <div v-else class="text-gray-600">No points found in collection</div>
            </div>
         </div>
      </div>
   </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { QdrantSearch } from '../../utils/qdrantSearch';
import AdminNavHeader from '../admin/AdminNavHeader.vue';
import { apiUrl } from '../../utils/api';

const QDRANT_API_URL = apiUrl('qdrant');

interface CollectionInfo {
   name: string;
   points_count: number;
   vectors_count: number | null;
   indexed_vectors_count: number;
   status: string;
   optimizer_status: string;
   vector_size: number | null;
}

interface Point {
   id: string | number;
   payload?: Record<string, any>;
   score?: number;
}

const collections = ref<string[]>([]);
const loading = ref(true);
const error = ref('');

const selectedCollection = ref<string | null>(null);
const collectionInfo = ref<CollectionInfo | null>(null);
const loadingDetails = ref(false);
const detailsError = ref('');

const scrollPoints = ref<Point[]>([]);
const loadingPoints = ref(false);
const pointsError = ref('');
const scrollOffset = ref<string | null>(null);

const filterMarque = ref('');
const filterRefciale = ref('');
const filterTarif = ref('');
const scrollFilterLoading = ref(false);
const scrollFilterError = ref('');
const scrollFilterResults = ref<Point[]>([]);
const isUsingFilter = ref(false);

const searchQuery = ref('');
const searchLoading = ref(false);
const searchError = ref('');
const searchResults = ref<Point[]>([]);

async function loadCollections() {
   loading.value = true;
   error.value = '';

   try {
      const url = new URL(QDRANT_API_URL);
      url.searchParams.set('action', 'collections');

      const response = await fetch(url.toString());
      if (!response.ok) {
         const text = await response.text();
         throw new Error(`API error ${response.status}: ${text}`);
      }

      const data = await response.json();
      collections.value = data.collections || [];
   } catch (e: any) {
      error.value = String(e?.message || e);
   } finally {
      loading.value = false;
   }
}

function onCollectionChange(event: Event) {
   const target = event.target as HTMLSelectElement | null;
   const value = target?.value || '';
   if (value) {
      selectCollection(value);
   }
}

async function selectCollection(collectionName: string) {
   selectedCollection.value = collectionName;
   scrollOffset.value = null;
   scrollPoints.value = [];
   await loadCollectionInfo();
   await loadPoints();
}

async function loadCollectionInfo() {
   if (!selectedCollection.value) return;

   loadingDetails.value = true;
   detailsError.value = '';

   try {
      const url = new URL(QDRANT_API_URL);
      url.searchParams.set('action', 'info');
      url.searchParams.set('collection', selectedCollection.value);

      const response = await fetch(url.toString());
      if (!response.ok) {
         const text = await response.text();
         throw new Error(`API error ${response.status}: ${text}`);
      }

      collectionInfo.value = await response.json();
   } catch (e: any) {
      detailsError.value = String(e?.message || e);
   } finally {
      loadingDetails.value = false;
   }
}

async function loadPoints() {
   if (!selectedCollection.value) return;

   loadingPoints.value = true;
   pointsError.value = '';

   try {
      const url = new URL(QDRANT_API_URL);
      url.searchParams.set('action', 'scroll');
      url.searchParams.set('collection', selectedCollection.value);
      url.searchParams.set('limit', '10');
      url.searchParams.set('with_payload', 'true');

      if (scrollOffset.value) {
         url.searchParams.set('offset', scrollOffset.value);
      }

      const response = await fetch(url.toString());
      if (!response.ok) {
         const text = await response.text();
         throw new Error(`API error ${response.status}: ${text}`);
      }

      const data = await response.json();
      if (scrollOffset.value) {
         // Append to existing points for "load more"
         scrollPoints.value = [...scrollPoints.value, ...(data.points || [])];
      } else {
         // First load
         scrollPoints.value = data.points || [];
      }
      scrollOffset.value = data.next_offset || null;
   } catch (e: any) {
      pointsError.value = String(e?.message || e);
   } finally {
      loadingPoints.value = false;
   }
}

async function applyScrollFilter() {
   if (!selectedCollection.value) return;

   scrollFilterLoading.value = true;
   scrollFilterError.value = '';
   scrollFilterResults.value = [];

   try {
      // Build filters object
      const filters: Record<string, any> = {};
      if (filterMarque.value.trim()) {
         filters.marque = filterMarque.value.trim();
      }
      if (filterRefciale.value.trim()) {
         filters.refciale = filterRefciale.value.trim();
      }
      if (filterTarif.value.trim()) {
         filters.tarif = filterTarif.value.trim();
      }

      if (Object.keys(filters).length === 0) {
         scrollFilterError.value = 'Please enter at least one filter';
         return;
      }

      const url = new URL(QDRANT_API_URL);
      url.searchParams.set('action', 'scroll');
      url.searchParams.set('collection', selectedCollection.value);
      url.searchParams.set('limit', '50');
      url.searchParams.set('with_payload', 'true');
      url.searchParams.set('filters', JSON.stringify(filters));

      const response = await fetch(url.toString());
      if (!response.ok) {
         const text = await response.text();
         throw new Error(`API error ${response.status}: ${text}`);
      }

      const data = await response.json();
      scrollFilterResults.value = data.points || [];
      isUsingFilter.value = true;
   } catch (e: any) {
      scrollFilterError.value = String(e?.message || e);
   } finally {
      scrollFilterLoading.value = false;
   }
}

async function clearScrollFilter() {
   filterMarque.value = '';
   filterRefciale.value = '';
   filterTarif.value = '';
   scrollFilterResults.value = [];
   scrollFilterError.value = '';
   isUsingFilter.value = false;
}

async function loadMorePoints() {
   if (!scrollOffset.value) {
      pointsError.value = 'No more points to load';
      return;
   }
   await loadPoints();
}

async function performSearch() {
   if (!searchQuery.value.trim() || !selectedCollection.value) {
      searchError.value = 'Please enter a search query and select a collection';
      return;
   }

   searchLoading.value = true;
   searchError.value = '';
   searchResults.value = [];

   try {
      const results = await QdrantSearch.search({
         collection: selectedCollection.value,
         query: searchQuery.value,
         limit: 10,
         with_payload: true,
      });
      searchResults.value = results;
   } catch (e: any) {
      searchError.value = String(e?.message || e);
   } finally {
      searchLoading.value = false;
   }
}

onMounted(async () => {
   await loadCollections();
   // Select default collection
   if (collections.value.includes('test_commerce_vectors')) {
      await selectCollection('test_commerce_vectors');
   }
});
</script>
