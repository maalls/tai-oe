<template>
   <div
      v-if="show"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
      @click.self="handleClose"
   >
      <div
         class="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden m-4 flex flex-col"
      >
         <div class="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
            <h2 class="text-xl font-semibold text-gray-900">{{ t('actions.executionLogs') }}</h2>
            <button @click="handleClose" class="text-gray-400 hover:text-gray-600">
               <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path
                     stroke-linecap="round"
                     stroke-linejoin="round"
                     stroke-width="2"
                     d="M6 18L18 6M6 6l12 12"
                  />
               </svg>
            </button>
         </div>

         <div class="flex-1 overflow-y-auto p-6">
            <!-- Loading State -->
            <div v-if="loading" class="flex items-center justify-center py-12">
               <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            </div>

            <!-- Error State -->
            <div v-else-if="error" class="text-center py-12">
               <svg
                  class="mx-auto h-12 w-12 text-red-400"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
               >
                  <path
                     stroke-linecap="round"
                     stroke-linejoin="round"
                     stroke-width="2"
                     d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                  />
               </svg>
               <p class="mt-4 text-sm text-gray-500">{{ error }}</p>
            </div>

            <!-- Empty State -->
            <div v-else-if="!logs || logs.length === 0" class="text-center py-12">
               <svg
                  class="mx-auto h-12 w-12 text-gray-400"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
               >
                  <path
                     stroke-linecap="round"
                     stroke-linejoin="round"
                     stroke-width="2"
                     d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                  />
               </svg>
               <p class="mt-4 text-sm text-gray-500">{{ t('actions.noLogsYet') }}</p>
            </div>

            <!-- Logs List -->
            <div v-else class="space-y-4">
               <div
                  v-for="log in logs"
                  :key="log.id"
                  class="bg-gray-50 rounded-lg border border-gray-200 p-4 hover:shadow-sm transition-shadow"
               >
                  <div class="flex items-start justify-between mb-3">
                     <div class="flex items-center gap-3">
                        <span
                           :class="[
                              'px-2 py-1 text-xs font-medium rounded-full',
                              getStatusClass(log.status),
                           ]"
                        >
                           {{ getStatusLabel(log.status) }}
                        </span>
                        <span class="text-sm text-gray-600">
                           {{ formatDate(log.executed_at) }}
                        </span>
                     </div>
                     <div v-if="log.execution_duration_ms" class="text-sm text-gray-500">
                        {{ formatDuration(log.execution_duration_ms) }}
                     </div>
                  </div>

                  <!-- Success Result -->
                  <div v-if="log.status === 'success' && log.result_data" class="mt-3">
                     <div class="text-xs font-medium text-gray-700 mb-2">
                        {{ t('actions.result') }}:
                     </div>
                     <div class="bg-white rounded border border-gray-200 p-3">
                        <pre class="text-xs text-gray-800 whitespace-pre-wrap">{{
                           formatJson(log.result_data)
                        }}</pre>
                     </div>
                  </div>

                  <!-- Error Details -->
                  <div v-if="log.status === 'error' && log.error_message" class="mt-3">
                     <div class="text-xs font-medium text-red-700 mb-2">
                        {{ t('actions.error') }}:
                     </div>
                     <div class="bg-red-50 rounded border border-red-200 p-3">
                        <p class="text-xs text-red-800">{{ log.error_message }}</p>
                        <div v-if="log.error_details" class="mt-2">
                           <details class="text-xs text-red-700">
                              <summary class="cursor-pointer hover:text-red-900">
                                 {{ t('actions.errorDetails') }}
                              </summary>
                              <pre class="mt-2 whitespace-pre-wrap">{{
                                 formatJson(log.error_details)
                              }}</pre>
                           </details>
                        </div>
                     </div>
                  </div>
               </div>
            </div>
         </div>

         <div
            class="bg-gray-50 border-t border-gray-200 px-6 py-4 flex items-center justify-between"
         >
            <div class="text-sm text-gray-600">
               {{ t('actions.totalExecutions', { count: logs?.length || 0 }) }}
            </div>
            <button
               @click="handleClose"
               class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
            >
               {{ t('common.close') }}
            </button>
         </div>
      </div>
   </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { useAuth } from '../../../stores/auth';

const { t } = useI18n();
const { getValidToken } = useAuth();

interface Props {
   show: boolean;
   actionId: string | null;
}

const props = defineProps<Props>();

const emit = defineEmits<{
   close: [];
}>();

const logs = ref<any[]>([]);
const loading = ref(false);
const error = ref<string | null>(null);

watch(
   () => props.show,
   async (show) => {
      if (show && props.actionId) {
         await loadLogs();
      }
   }
);

async function loadLogs() {
   if (!props.actionId) return;

   try {
      loading.value = true;
      error.value = null;

      const token = await getValidToken();
      const response = await fetch(`/api/actions/${props.actionId}/logs`, {
         headers: {
            Authorization: `Bearer ${token}`,
         },
      });

      if (!response.ok) {
         throw new Error('Failed to load logs');
      }

      const data = await response.json();
      logs.value = data.logs || [];
   } catch (err: any) {
      error.value = err.message || 'Failed to load execution logs';
      console.error('Error loading logs:', err);
   } finally {
      loading.value = false;
   }
}

function getStatusLabel(status: string): string {
   const labels: Record<string, string> = {
      success: t('actions.logStatus.success'),
      error: t('actions.logStatus.error'),
      pending: t('actions.logStatus.pending'),
   };
   return labels[status] || status;
}

function getStatusClass(status: string): string {
   const classes: Record<string, string> = {
      success: 'bg-green-100 text-green-800',
      error: 'bg-red-100 text-red-800',
      pending: 'bg-yellow-100 text-yellow-800',
   };
   return classes[status] || 'bg-gray-100 text-gray-800';
}

function formatDate(dateString: string): string {
   const date = new Date(dateString);
   return date.toLocaleString();
}

function formatDuration(ms: number): string {
   if (ms < 1000) {
      return `${ms}ms`;
   }
   const seconds = (ms / 1000).toFixed(2);
   return `${seconds}s`;
}

function formatJson(obj: any): string {
   try {
      return JSON.stringify(obj, null, 2);
   } catch {
      return String(obj);
   }
}

function handleClose() {
   emit('close');
   logs.value = [];
   error.value = null;
}
</script>
