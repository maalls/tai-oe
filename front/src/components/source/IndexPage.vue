<style>
.scroll-container {
   overflow: auto;
   scrollbar-width: none; /* Firefox */
   -ms-overflow-style: none; /* IE / Edge legacy */
}
.scroll-container::-webkit-scrollbar {
   display: none; /* Chrome / Safari */
}
</style>
<template>
   <div class="min-h-screen">
      <AdminNavHeader />
      <!-- Source Selection -->
      <div class="hidden sm:flex items-center gap-6">
         <select
            id="sourceSelect"
            class="px-3 text-black py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            style="max-width: 300px"
         ></select>
      </div>
      <div
         id="status"
         class="m-4 bottom-4 right-4 bg-black text-white px-4 py-2 rounded-md shadow-lg text-sm z-50 opacity-75"
      ></div>

      <!-- Sheet Tabs -->
      <div
         id="tabs"
         class="scroll-container flex gap-2 items-center mb-4 border-b border-gray-300 pl-2 overflow-x-auto no-scrollbar"
      ></div>

      <!-- Pagination -->
      <div class="flex items-center gap-4 justify-center">
         <button
            id="prevBtn"
            class="px-3 py-2 bg-gray-200 text-gray-700 rounded-md text-sm hover:bg-gray-300 transition"
         >
            ← Prev
         </button>
         <span id="pageInfo" class="text-sm text-gray-600">Page 1</span>
         <div class="flex items-center gap-2">
            <label for="limit" class="text-sm font-medium text-gray-700">Rows:</label>
            <select
               id="limit"
               class="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
               <option>10</option>
               <option>20</option>
               <option>25</option>
               <option>50</option>
               <option selected>100</option>
               <option>250</option>
               <option>500</option>
            </select>
         </div>
         <button
            id="nextBtn"
            class="px-3 py-2 bg-gray-200 text-gray-700 rounded-md text-sm hover:bg-gray-300 transition"
         >
            Next →
         </button>
      </div>

      <!-- Search Filter Section -->
      <div class="max-w-7xl mx-auto px-6 py-4">
         <div class="bg-gray-50 rounded-lg p-4 mb-4 border border-gray-200">
            <div class="flex flex-col gap-3 sm:flex-row sm:items-end sm:gap-3">
               <div class="flex-1 sm:flex-none">
                  <label for="searchField" class="block text-xs font-medium text-gray-700 mb-1"
                     >Search Field:</label
                  >
                  <select
                     id="searchField"
                     class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                     <option value="">-- Select a field --</option>
                  </select>
               </div>
               <div class="flex-1 sm:flex-none">
                  <label for="searchText" class="block text-xs font-medium text-gray-700 mb-1"
                     >Search Text:</label
                  >
                  <input
                     id="searchText"
                     type="text"
                     placeholder="Enter search value ..."
                     class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
               </div>
               <button
                  id="searchBtn"
                  class="px-4 py-2 bg-blue-500 text-white rounded-md text-sm hover:bg-blue-600 transition"
               >
                  Search
               </button>
               <button
                  id="clearSearchBtn"
                  class="px-4 py-2 bg-gray-400 text-white rounded-md text-sm hover:bg-gray-500 transition"
               >
                  Clear
               </button>
            </div>
            <div id="filterStatus" class="text-xs text-gray-600 mt-2"></div>
         </div>
      </div>

      <div class="max-w-7xl mx-auto px-6 py-2">
         <!-- CSV Table Section -->
         <section id="table" class="bg-white rounded-lg shadow mb-8">
            <div class="overflow-x-auto prevent-swipe-nav">
               <table id="csvTable" class="w-full text-sm">
                  <thead class="bg-black text-white border-b border-gray-200"></thead>
                  <tbody class="divide-y divide-gray-200"></tbody>
               </table>
            </div>
         </section>
      </div>
   </div>
</template>

<script setup lang="js">
import { onMounted, onActivated } from 'vue';
import { useRoute } from 'vue-router';
import AdminNavHeader from '../admin/AdminNavHeader.vue';
import { API_BASE_URL } from '../../utils/api';
import { authFetch } from '../../api/authFetch';

const BASE = API_BASE_URL;
const api = {
   sources: BASE + '/api/csv/sources',
   sheets: BASE + '/api/csv/files',
   preview: (file, sheet, limit, offset) =>
      BASE +
      `/api/csv/preview?source=${encodeURIComponent(file)}&file=${encodeURIComponent(sheet)}&limit=${limit}&offset=${offset}`,
   raw: (sheet) => BASE + `/api/csv/raw?file=${encodeURIComponent(sheet)}`,
};

let currentOffset = 0;
let availableSheets = [];
let currentSheetName = '';
let availableSources = [];
let currentSourceFile = '';
let currentMeta = {};
let currentHeaders = [];
let currentSearchField = '';
let currentSearchText = '';

const route = useRoute();

async function loadSources() {
   console.log('Loading sources from', api.sources);

   const res = await authFetch(api.sources);
   if (!res.ok) throw new Error(`Sources HTTP ${res.status}`);
   const data = await res.json();
   console.log('Sources data:', data);
   const sel = document.getElementById('sourceSelect');
   sel.innerHTML = '';

   const selectedSource = currentSourceFile || (data.length > 0 ? data[0] : '');
   // On initial load keep existing URL params (do not overwrite the active sheet)
   setCurrentSource(selectedSource, { updateUrl: false });

   function addOption(name, value) {
      const opt = document.createElement('option');
      opt.value = value || name;
      if (name === selectedSource) {
         opt.selected = true;
      }
      opt.textContent = name;
      sel.appendChild(opt);
   }
   data.forEach((name) => {
      addOption(name);
   });

   addOption('import new source...', -1);
}

async function loadSheets() {
   console.log('Loading sheets for', currentSourceFile, 'from', api.sheets);
   setStatus('Loading sheets from', api.sheets);
   const res = await authFetch(api.sheets + `?source=${encodeURIComponent(currentSourceFile)}`);

   if (!res.ok) throw new Error(`Files HTTP ${res.status}`);
   const data = await res.json();
   console.log('Sheets response:', data);
   availableSheets = data.files || [];
   // pick current sheet from URL > localStorage > first entry
   const params = new URLSearchParams(window.location.search);
   currentSheetName = params.get('file') || availableSheets[0] || '';
   if (currentSheetName) {
      console.log('Setting current sheet to', currentSheetName);
      setCurrentSheet(currentSheetName, { updateUrl: true });
   }
   renderTabs();
   console.log('tabs rendered');
   setStatus(`${availableSheets.length} CSV files`);
}

function renderTabs() {
   const tabsContainer = document.getElementById('tabs');
   tabsContainer.innerHTML = '';
   const currentSheet = getCurrentSheet();

   availableSheets.forEach((sheet) => {
      const btn = document.createElement('button');
      const displayName = sheet.endsWith('.csv') ? sheet.slice(0, -4) : sheet;
      btn.textContent = displayName;
      btn.className = 'px-4 py-2 rounded-t-md text-sm font-medium whitespace-nowrap transition';

      if (sheet === currentSheet) {
         btn.className += ' bg-black text-white';
      } else {
         btn.className += ' bg-gray-200 text-gray-700 hover:bg-gray-300';
      }

      btn.addEventListener('click', async () => {
         console.log('Tab clicked:', sheet);
         try {
            setCurrentSheet(sheet, { updateUrl: true });
            renderTabs();
            await loadPreview();
         } catch (e) {
            console.error('Error loading preview for', sheet, e);
            setStatus(e.message);
         }
      });

      tabsContainer.appendChild(btn);
   });
}

function getCurrentSheet() {
   return currentSheetName;
}

function clearTable() {
   const thead = document.querySelector('#csvTable thead');
   const tbody = document.querySelector('#csvTable tbody');
   if (thead) thead.innerHTML = '';
   if (tbody) tbody.innerHTML = '';
   const pageInfo = document.getElementById('pageInfo');
   if (pageInfo) pageInfo.textContent = '';
}

function setCurrentSource(source, { updateUrl = false } = {}) {
   currentSourceFile = source;
   // Clear current sheet when source changes
   currentSheetName = '';
   clearTable();
   if (updateUrl) {
      const params = new URLSearchParams(window.location.search);
      params.set('source', source);
      params.delete('file');
      params.delete('offset');
      window.history.replaceState({}, '', `?${params.toString()}`);
   }
}

function setCurrentSheet(sheet, { updateUrl = false } = {}) {
   currentSheetName = sheet;
   clearTable();
   if (updateUrl) {
      const params = new URLSearchParams(window.location.search);
      const limit = document.getElementById('limit').value;
      params.set('file', sheet);
      params.set('limit', limit);
      params.delete('offset');
      window.history.replaceState({}, '', `?${params.toString()}`);
   }
   if (sheet) updateDownloadLink(sheet);
   console.log('Current sheet set to', sheet);
}

function updateDownloadLink(file) {
   const link = document.getElementById('downloadLink');
   if (link) link.href = api.raw(file);
}

async function loadPreview(offset = 0) {
   const file = getCurrentSheet();
   const limit = parseInt(document.getElementById('limit').value);
   if (!file) {
      console.warn('No file selected for preview');
      return;
   }
   if (!currentSourceFile) {
      console.warn('No source selected for preview');
      return;
   }
   currentOffset = offset;
   setStatus(`Loading ${file}...`);
   const res = await authFetch(api.preview(currentSourceFile, currentSheetName, limit, offset));
   if (!res.ok) throw new Error(`Preview HTTP ${res.status}`);
   const data = await res.json();
   const headers = data.headers || [];
   const rows = data.rows || [];
   const metadata = data.column_metadata || [];
   currentMeta = data.meta || {};
   currentHeaders = headers;
   const total = data.total ?? data.count ?? rows.length;
   const count = rows.length;

   renderColumnMetadata(metadata);
   renderTable(headers, rows, metadata);
   updateSearchFieldOptions(headers);

   const page = Math.floor(offset / limit) + 1;
   const totalPages = Math.max(1, Math.ceil(total / limit));
   document.getElementById('pageInfo').textContent =
      `Page ${page} of ${totalPages} | Showing ${count} of ${total} rows`;
   document.getElementById('prevBtn').disabled = offset === 0;
   document.getElementById('nextBtn').disabled = count < limit;
   setStatus(`${file} (${total} total rows)`);
}

function renderTable(headers, rows, metadata) {
   const thead = document.querySelector('#csvTable thead');
   const tbody = document.querySelector('#csvTable tbody');
   thead.innerHTML = '';
   tbody.innerHTML = '';
   const metaMap = {};
   (metadata || []).forEach((m) => {
      metaMap[m.name] = m;
   });
   const oneToManyRaw = currentMeta['one_to_many'] || currentMeta['one_to_many:'] || {};
   const oneToMany = Object.entries(oneToManyRaw).map(([target, cfg]) => ({
      target,
      key: cfg?.key,
      foreign_key: cfg?.foreign_key,
   }));
   const headerIndex = {};
   headers.forEach((h, idx) => {
      headerIndex[h] = idx;
   });
   const tr = document.createElement('tr');
   headers.forEach((h) => {
      const m = metaMap[h];
      const th = document.createElement('th');
      const distinct = m ? m.distinct : '?';
      const keyIcon = m && m.is_unique ? ' 🔑' : '';
      th.innerHTML = h + ` <br/><small>(${distinct})${keyIcon}</small>`;
      tr.appendChild(th);
   });
   oneToMany.forEach((rel) => {
      const th = document.createElement('th');
      th.textContent = rel.target;
      tr.appendChild(th);
   });
   thead.appendChild(tr);
   rows.forEach((r) => {
      const tr = document.createElement('tr');
      (Array.isArray(r) ? r : []).forEach((cell) => {
         const td = document.createElement('td');
         td.textContent = cell;
         tr.appendChild(td);
      });
      oneToMany.forEach((rel) => {
         const td = document.createElement('td');
         const keyIdx = rel.key != null ? headerIndex[rel.key] : undefined;
         const keyVal = keyIdx !== undefined ? r[keyIdx] : undefined;
         if (keyVal !== undefined && rel.foreign_key && rel.target) {
            const link = document.createElement('a');
            link.href = '#';
            link.textContent = 'open';
            link.addEventListener('click', async (e) => {
               e.preventDefault();
               await openOneToMany(rel, keyVal);
            });
            td.appendChild(link);
         } else {
            td.textContent = '';
         }
         tr.appendChild(td);
      });
      tbody.appendChild(tr);
   });
}

async function openOneToMany(rel, keyVal) {
   try {
      const limit = parseInt(document.getElementById('limit').value) || 100;
      const base = api.preview(currentSourceFile, rel.target, limit, 0);
      const filter = { [rel.foreign_key]: keyVal };
      const url = `${base}&filter=${encodeURIComponent(JSON.stringify(filter))}`;
      const res = await authFetch(url);
      if (!res.ok) throw new Error(`Related preview HTTP ${res.status}`);
      const data = await res.json();
      console.log('One-to-many related result', {
         target: rel.target,
         key: rel.foreign_key,
         value: keyVal,
         headers: data.headers,
         rows: data.rows,
         total: data.total,
      });
      setStatus(`Loaded related rows from ${rel.target}`);
   } catch (e) {
      console.error('One-to-many load error', e);
      setStatus(`Error loading related: ${e.message}`);
   }
}

function renderColumnMetadata(metadata) {
   // Metadata is now shown only in table headers; no separate table needed
}

function setStatus(text) {
   const statusEl = document.getElementById('status');
   if (statusEl) statusEl.textContent = text;
}

function updateSearchFieldOptions(headers) {
   const searchFieldSelect = document.getElementById('searchField');
   if (!searchFieldSelect) return;

   const currentVal = searchFieldSelect.value;
   searchFieldSelect.innerHTML = '<option value="">-- Select a field --</option>';

   headers.forEach((header) => {
      const opt = document.createElement('option');
      opt.value = header;
      opt.textContent = header;
      searchFieldSelect.appendChild(opt);
   });

   if (currentVal && headers.includes(currentVal)) {
      searchFieldSelect.value = currentVal;
   }
}

async function performSearch() {
   const field = document.getElementById('searchField').value;
   const text = document.getElementById('searchText').value;

   if (!field || !text) {
      setStatus('Please select a field and enter search text');
      return;
   }

   currentSearchField = field;
   currentSearchText = text;
   currentOffset = 0;

   try {
      setStatus(`Searching for "${text}" in field "${field}"...`);
      const file = getCurrentSheet();
      const limit = parseInt(document.getElementById('limit').value);

      const filter = { [field]: { $icontains: text } };
      const filterParam = encodeURIComponent(JSON.stringify(filter));
      const res = await authFetch(
         api.preview(currentSourceFile, currentSheetName, limit, 0) + `&filter=${filterParam}`
      );

      if (!res.ok) throw new Error(`Search HTTP ${res.status}`);
      const data = await res.json();

      const headers = data.headers || [];
      const rows = data.rows || [];
      const metadata = data.column_metadata || [];
      const total = data.total ?? data.count ?? rows.length;
      const count = rows.length;

      renderColumnMetadata(metadata);
      renderTable(headers, rows, metadata);

      const limit_val = limit;
      const page = Math.floor(currentOffset / limit_val) + 1;
      const totalPages = Math.max(1, Math.ceil(total / limit_val));
      document.getElementById('pageInfo').textContent =
         `Page ${page} of ${totalPages} | Showing ${count} of ${total} results`;
      document.getElementById('prevBtn').disabled = currentOffset === 0;
      document.getElementById('nextBtn').disabled = count < limit_val;

      const filterStatus = document.getElementById('filterStatus');
      if (filterStatus) {
         filterStatus.textContent = `Filter applied: "${text}" in "${field}" (${total} results)`;
      }

      setStatus(`Found ${total} results`);
   } catch (e) {
      setStatus(`Search error: ${e.message}`);
      console.error('Search error:', e);
   }
}

function clearSearch() {
   currentSearchField = '';
   currentSearchText = '';
   const filterStatus = document.getElementById('filterStatus');
   if (filterStatus) filterStatus.textContent = '';
   document.getElementById('searchField').value = '';
   document.getElementById('searchText').value = '';
   currentOffset = 0;
   loadPreview(0).catch((e) => setStatus(e.message));
}

function setupEventListeners() {
   document.getElementById('sourceSelect')?.addEventListener('change', async () => {
      // Check if user selected "import new source..." option
      const newSource = document.getElementById('sourceSelect').value;
      const previousSource = currentSourceFile;

      if (newSource === '-1') {
         console.log('Import new source selected');
         const fileSelected = await openFileUpload();
         if (!fileSelected) {
            console.log('File upload canceled by user');
            // User canceled; revert dropdown to current source
            document.getElementById('sourceSelect').value = previousSource;
         }
         return;
      } else {
         setCurrentSource(newSource, { updateUrl: true });
         console.log('source select changed', currentSourceFile);
         await loadSheets();
         await loadPreview(0);
      }
   });

   document.getElementById('limit')?.addEventListener('change', async () => {
      try {
         clearSearch();
         const file = getCurrentSheet();
         const limit = document.getElementById('limit').value;
         const params = new URLSearchParams(window.location.search);
         params.set('file', file);
         params.set('limit', limit);
         params.delete('offset');
         window.history.replaceState({}, '', `?${params.toString()}`);
         await loadPreview(0);
      } catch (e) {
         setStatus(e.message);
      }
   });

   document.getElementById('searchBtn')?.addEventListener('click', performSearch);
   document.getElementById('searchText')?.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') performSearch();
   });
   document.getElementById('clearSearchBtn')?.addEventListener('click', clearSearch);

   document.getElementById('prevBtn')?.addEventListener('click', async () => {
      try {
         const limit = parseInt(document.getElementById('limit').value);
         const newOffset = Math.max(0, currentOffset - limit);
         const params = new URLSearchParams(window.location.search);
         params.set('offset', newOffset);
         window.history.replaceState({}, '', `?${params.toString()}`);
         await loadPreview(newOffset);
      } catch (e) {
         setStatus(e.message);
      }
   });

   document.getElementById('nextBtn')?.addEventListener('click', async () => {
      try {
         console.log('Next button clicked, currentOffset:', currentOffset);
         const limit = parseInt(document.getElementById('limit').value);
         const newOffset = currentOffset + limit;
         const params = new URLSearchParams(window.location.search);
         params.set('offset', newOffset);
         window.history.replaceState({}, '', `?${params.toString()}`);
         await loadPreview(newOffset);
      } catch (e) {
         setStatus(e.message);
      }
   });
}

async function openFileUpload() {
   // Create a hidden file input if it doesn't exist
   let fileInput = document.getElementById('hiddenFileInput');
   if (!fileInput) {
      fileInput = document.createElement('input');
      fileInput.type = 'file';
      fileInput.id = 'hiddenFileInput';
      fileInput.accept = '.xlsx,.xls,.csv';
      fileInput.style.display = 'none';
      document.body.appendChild(fileInput);
   }

   // Return a promise that resolves to true if file selected, false if canceled
   return new Promise((resolve) => {
      let resolved = false;

      const handleChange = async (event) => {
         if (resolved) return;
         resolved = true;
         fileInput.removeEventListener('change', handleChange);
         fileInput.removeEventListener('cancel', handleCancel);
         const file = event.target.files?.[0];
         if (file) {
            await handleFileUpload(event);
            resolve(true);
         } else {
            resolve(false);
         }
      };

      const handleCancel = () => {
         if (resolved) return;
         resolved = true;
         fileInput.removeEventListener('change', handleChange);
         fileInput.removeEventListener('cancel', handleCancel);
         console.log('File dialog canceled');
         resolve(false);
      };

      fileInput.addEventListener('change', handleChange);
      fileInput.addEventListener('cancel', handleCancel);
      // Reset value so the same file can be selected again
      fileInput.value = '';
      // Trigger the file dialog
      fileInput.click();
   });
}

async function handleFileUpload(event) {
   const file = event.target.files?.[0];
   if (!file) return;

   try {
      setStatus(`Uploading ${file.name}...`);
      const formData = new FormData();
      formData.append('file', file);

      const res = await authFetch(BASE + '/api/csv/source', {
         method: 'POST',
         body: formData,
      });

      if (!res.ok) throw new Error(`Upload HTTP ${res.status}`);
      const result = await res.json();

      setStatus(`Successfully imported ${file.name}`);
      console.log('Upload result:', result);

      // Reload sources and select the newly uploaded one
      await loadSources();
      if (result.source) {
         setCurrentSource(result.source, { updateUrl: true });
         await loadSheets();
         await loadPreview(0);
      }
   } catch (e) {
      setStatus(`Error uploading file: ${e.message}`);
      console.error('Upload error:', e);
   }
}

function updateParams({ file, limit, offset }) {
   const params = new URLSearchParams(window.location.search);
   params.set('file', file);
   params.set('limit', limit);
   params.set('offset', offset);
   window.history.replaceState({}, '', `?${params.toString()}`);
}

async function initializePage() {
   try {
      const params = new URLSearchParams(window.location.search);
      const limitParam = params.get('limit');
      const offsetParam = parseInt(params.get('offset')) || 0;
      if (limitParam) {
         document.getElementById('limit').value = limitParam;
      }

      currentSourceFile = params.get('source') || '';

      await loadSources();
      await loadSheets();
      await loadPreview(offsetParam);

      // Setup event listeners after data is loaded
      setupEventListeners();
   } catch (e) {
      setStatus(e.message);
   }
}

// Initialize on mount and when component is activated (navigated back to)
onMounted(initializePage);
onActivated(initializePage);
</script>
