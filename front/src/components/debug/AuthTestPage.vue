<template>
   <div class="p-6 max-w-5xl mx-auto space-y-6">
      <div>
         <h1 class="text-2xl font-bold text-gray-900">Auth/API Test</h1>
         <p class="text-sm text-gray-600 mt-1">
            Use this page to test `/api/auth/user`, `/api/opportunities/search`, and `/api/vendor`
            with the current browser session or a pasted bearer token.
         </p>
      </div>

      <div class="bg-white border rounded-lg p-4 space-y-4">
         <div class="flex items-center justify-between">
            <h2 class="font-semibold text-gray-900">Bearer Token</h2>
            <div class="flex gap-2">
               <button
                  class="px-3 py-1.5 text-sm bg-gray-100 hover:bg-gray-200 rounded"
                  @click="prefillFromSession"
               >
                  Prefill From Session
               </button>
               <button
                  class="px-3 py-1.5 text-sm bg-gray-100 hover:bg-gray-200 rounded"
                  @click="copyToken"
                  :disabled="!token.trim()"
               >
                  Copy Token
               </button>
               <button class="px-3 py-1.5 text-sm bg-blue-100 hover:bg-blue-200 rounded" @click="copyDebugReport">
                  Copy Debug Report
               </button>
            </div>
         </div>

         <textarea
            v-model="token"
            rows="5"
            class="w-full border rounded p-3 font-mono text-xs"
            placeholder="Paste raw JWT here (without 'Bearer ')"
         />

         <div v-if="token" class="text-xs text-gray-500 font-mono">
            {{ maskedToken }}
         </div>

         <div class="text-xs text-gray-500">
            <div>Current origin: {{ origin }}</div>
            <div>API base: {{ apiBase }}</div>
            <div v-if="prefillError" class="text-red-600 mt-1">{{ prefillError }}</div>
            <div v-if="tokenClaims" class="mt-2 text-gray-700">
               <div><span class="font-semibold">sub:</span> {{ tokenClaims.sub || '-' }}</div>
               <div><span class="font-semibold">session_id:</span> {{ tokenClaims.session_id || '-' }}</div>
               <div><span class="font-semibold">exp:</span> {{ tokenClaims.exp || '-' }}</div>
               <div><span class="font-semibold">iat:</span> {{ tokenClaims.iat || '-' }}</div>
               <div><span class="font-semibold">email:</span> {{ tokenClaims.email || '-' }}</div>
            </div>
         </div>
      </div>

      <div class="bg-white border rounded-lg p-4 space-y-3">
         <h2 class="font-semibold text-gray-900">Quick Tests</h2>
         <div class="flex flex-wrap gap-2">
            <button
               class="px-3 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
               :disabled="isLoading"
               @click="testAuthUser"
            >
               Test /api/auth/user (with token)
            </button>
            <button
               class="px-3 py-2 text-sm bg-indigo-600 text-white rounded hover:bg-indigo-700"
               :disabled="isLoading"
               @click="testOpportunities"
            >
               Test /api/opportunities/search (with token)
            </button>
            <button
               class="px-3 py-2 text-sm bg-gray-700 text-white rounded hover:bg-gray-800"
               :disabled="isLoading"
               @click="testVendor"
            >
               Test /api/vendor (no token)
            </button>
            <button
               class="px-3 py-2 text-sm bg-gray-100 rounded hover:bg-gray-200"
               :disabled="isLoading"
               @click="runAll"
            >
               Run All
            </button>
            <button class="px-3 py-2 text-sm bg-red-100 rounded hover:bg-red-200" @click="clearResults">
               Clear Results
            </button>
         </div>
      </div>

      <div v-if="results.length" class="space-y-3">
         <div
            v-for="item in results"
            :key="item.id"
            class="bg-white border rounded-lg p-4"
         >
            <div class="flex items-center justify-between gap-2">
               <div class="font-semibold text-sm">{{ item.label }}</div>
               <div
                  class="text-xs px-2 py-1 rounded"
                  :class="item.status >= 200 && item.status < 300 ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'"
               >
                  HTTP {{ item.status }}
               </div>
            </div>
            <div class="text-xs text-gray-500 mt-1">{{ item.url }}</div>
            <pre class="mt-3 text-xs bg-gray-50 border rounded p-3 overflow-auto">{{ item.body }}</pre>
         </div>
      </div>
   </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { useAuth } from '../../stores/auth';

type TestResult = {
   id: number;
   label: string;
   url: string;
   status: number;
   body: string;
};

const { getValidToken } = useAuth();
const token = ref('');
const prefillError = ref('');
const results = ref<TestResult[]>([]);
const isLoading = ref(false);
const seq = ref(1);

const origin = computed(() => window.location.origin);
const apiBase = computed(() => `${window.location.origin}/api`);
const maskedToken = computed(() => {
   const raw = token.value.trim();
   if (!raw) return '';
   if (raw.length <= 24) return raw;
   return `${raw.slice(0, 18)}...${raw.slice(-8)}`;
});

const tokenClaims = computed<Record<string, any> | null>(() => {
   const raw = token.value.trim();
   if (!raw) return null;
   try {
      const parts = raw.split('.');
      if (parts.length < 2) return null;
      const payload = parts[1];
      const normalized = payload + '='.repeat((4 - (payload.length % 4)) % 4);
      const json = atob(normalized.replace(/-/g, '+').replace(/_/g, '/'));
      return JSON.parse(json);
   } catch {
      return null;
   }
});

async function prefillFromSession() {
   prefillError.value = '';
   try {
      token.value = await getValidToken();
   } catch (err: any) {
      token.value = '';
      prefillError.value = err?.message || 'Unable to prefill token from session';
   }
}

async function copyToken() {
   if (!token.value.trim()) return;
   await navigator.clipboard.writeText(token.value.trim());
}

async function copyDebugReport() {
   const report = {
      generatedAt: new Date().toISOString(),
      origin: window.location.origin,
      authUserEndpoint: `${window.location.origin}/api/auth/user`,
      opportunitiesEndpoint: `${window.location.origin}/api/opportunities/search`,
      vendorEndpoint: `${window.location.origin}/api/vendor`,
      token: token.value.trim(),
      tokenClaims: tokenClaims.value,
      recentResults: results.value,
   };
   await navigator.clipboard.writeText(JSON.stringify(report, null, 2));
}

async function callEndpoint(label: string, path: string, withToken = false) {
   const headers: Record<string, string> = {
      'Content-Type': 'application/json',
   };

   if (withToken && token.value.trim()) {
      headers.Authorization = `Bearer ${token.value.trim()}`;
   }

   const url = `${window.location.origin}${path}`;
   const response = await fetch(url, { headers });
   const body = await response.text();

   results.value.unshift({
      id: seq.value++,
      label,
      url,
      status: response.status,
      body,
   });
}

async function testAuthUser() {
   isLoading.value = true;
   try {
      await callEndpoint('Auth User', '/api/auth/user', true);
   } finally {
      isLoading.value = false;
   }
}

async function testOpportunities() {
   isLoading.value = true;
   try {
      await callEndpoint('Opportunities Search', '/api/opportunities/search', true);
   } finally {
      isLoading.value = false;
   }
}

async function testVendor() {
   isLoading.value = true;
   try {
      await callEndpoint('Vendor List', '/api/vendor', false);
   } finally {
      isLoading.value = false;
   }
}

async function runAll() {
   isLoading.value = true;
   try {
      await callEndpoint('Auth User', '/api/auth/user', true);
      await callEndpoint('Opportunities Search', '/api/opportunities/search', true);
      await callEndpoint('Vendor List', '/api/vendor', false);
   } finally {
      isLoading.value = false;
   }
}

function clearResults() {
   results.value = [];
}
</script>
