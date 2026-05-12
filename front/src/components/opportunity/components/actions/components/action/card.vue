<template>
   <div class="bg-white rounded-lg shadow p-4">
      <div class="flex justify-between items-start mb-3">
         <div class="flex items-center gap-2">
            <h3 class="font-semibold text-gray-900">{{ actionTypeLabel }}</h3>
            <span
               class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
               :class="getStatusColor(normalizedStatus)"
            >
               {{ normalizedStatus }}
            </span>
         </div>
         <div class="flex gap-2">
            <button
               v-if="normalizedStatus === 'PAUSED'"
               @click="$emit('resume', action)"
               class="text-green-600 hover:text-green-800"
               :title="t('opportunities.resume')"
            >
               <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                     stroke-linecap="round"
                     stroke-linejoin="round"
                     stroke-width="2"
                     d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"
                  />
                  <path
                     stroke-linecap="round"
                     stroke-linejoin="round"
                     stroke-width="2"
                     d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
               </svg>
            </button>
            <button
               v-else-if="normalizedStatus === 'ACTIVE'"
               @click="$emit('pause', action)"
               class="text-yellow-600 hover:text-yellow-800"
               :title="t('opportunities.pause')"
            >
               <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                     stroke-linecap="round"
                     stroke-linejoin="round"
                     stroke-width="2"
                     d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
               </svg>
            </button>
            <button
               @click="$emit('edit', action)"
               class="text-blue-600 hover:text-blue-800"
               :title="t('common.edit')"
            >
               <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                     stroke-linecap="round"
                     stroke-linejoin="round"
                     stroke-width="2"
                     d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                  />
               </svg>
            </button>
            <button
               @click="$emit('delete', action)"
               class="text-red-600 hover:text-red-800"
               :title="t('common.delete')"
            >
               <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                     stroke-linecap="round"
                     stroke-linejoin="round"
                     stroke-width="2"
                     d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                  />
               </svg>
            </button>
         </div>
      </div>

      <div class="space-y-2 text-sm text-gray-600">
         <p v-if="action.description">{{ action.description }}</p>
         <p v-if="action.due_date">
            <span class="font-medium">{{ t('opportunities.dueDate') }}:</span>
            {{ formatDate(action.due_date) }}
         </p>
         <p v-if="action.last_executed_at">
            <span class="font-medium">{{ t('opportunities.lastExecuted') }}:</span>
            {{ formatDate(action.last_executed_at) }}
         </p>
      </div>

      <div class="mt-4 flex gap-2">
         <button
            @click="$emit('execute', action)"
            class="flex-1 px-3 py-2 bg-green-100 text-green-800 rounded hover:bg-green-200 text-sm font-medium"
         >
            {{ t('opportunities.execute') }}
         </button>
         <button
            @click="$emit('logs', action)"
            class="flex-1 px-3 py-2 bg-gray-100 text-gray-800 rounded hover:bg-gray-200 text-sm font-medium"
         >
            {{ t('opportunities.logs') }}
         </button>
      </div>
   </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

type Action = Record<string, any>;

type Props = {
   action: Action;
   t: (key: string) => string;
   getActionTypeLabel: (actionType?: string) => string;
   getStatusColor: (status: string) => string;
   formatDate: (dateString: string) => string;
};

const props = defineProps<Props>();

defineEmits<{
   (e: 'pause', action: Action): void;
   (e: 'resume', action: Action): void;
   (e: 'edit', action: Action): void;
   (e: 'delete', action: Action): void;
   (e: 'execute', action: Action): void;
   (e: 'logs', action: Action): void;
}>();

const normalizedStatus = computed(() => {
   const status = props.action?.status;
   if (!status) return 'UNKNOWN';
   return String(status).toUpperCase();
});

const actionTypeLabel = computed(() => {
   return props.getActionTypeLabel(props.action?.action_type || props.action?.type);
});
</script>
