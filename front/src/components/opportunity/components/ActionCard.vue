<template>
   <div
      class="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow"
   >
      <div class="flex items-start justify-between">
         <!-- Left: Action Info -->
         <div class="flex-1">
            <div class="flex items-center gap-3 mb-2">
               <h3 class="text-lg font-semibold text-gray-900">
                  {{ getActionTypeLabel(action.action_type) }}
               </h3>
               <span
                  :class="[
                     'px-2 py-1 text-xs font-medium rounded-full',
                     getStatusClass(action.status),
                  ]"
               >
                  {{ getStatusLabel(action.status) }}
               </span>
            </div>

            <div class="space-y-2 text-sm text-gray-600">
               <div class="flex items-center gap-2">
                  <svg
                     class="w-4 h-4 text-gray-400"
                     fill="none"
                     viewBox="0 0 24 24"
                     stroke="currentColor"
                  >
                     <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
                     />
                  </svg>
                  <span>{{ getScheduleLabel(action.schedule_type, action.schedule_config) }}</span>
               </div>

               <div
                  v-if="action.next_execution_at && action.status === 'active'"
                  class="flex items-center gap-2"
               >
                  <svg
                     class="w-4 h-4 text-gray-400"
                     fill="none"
                     viewBox="0 0 24 24"
                     stroke="currentColor"
                  >
                     <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                     />
                  </svg>
                  <span
                     >{{ t('actions.nextExecution') }}:
                     {{ formatDate(action.next_execution_at) }}</span
                  >
               </div>

               <div v-if="action.last_executed_at" class="flex items-center gap-2">
                  <svg
                     class="w-4 h-4 text-gray-400"
                     fill="none"
                     viewBox="0 0 24 24"
                     stroke="currentColor"
                  >
                     <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                     />
                  </svg>
                  <span
                     >{{ t('actions.lastExecuted') }}:
                     {{ formatDate(action.last_executed_at) }}</span
                  >
               </div>

               <div class="flex items-center gap-2">
                  <svg
                     class="w-4 h-4 text-gray-400"
                     fill="none"
                     viewBox="0 0 24 24"
                     stroke="currentColor"
                  >
                     <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                     />
                  </svg>
                  <span>
                     {{ t('actions.executions') }}: {{ action.execution_count || 0 }}
                     <span v-if="action.max_executions">/ {{ action.max_executions }}</span>
                  </span>
               </div>
            </div>
         </div>

         <!-- Right: Actions Menu -->
         <div class="relative ml-4">
            <button
               @click="showMenu = !showMenu"
               class="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100"
            >
               <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path
                     d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z"
                  />
               </svg>
            </button>

            <div
               v-if="showMenu"
               v-click-outside="() => (showMenu = false)"
               class="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-10"
            >
               <button
                  @click="handleExecute"
                  class="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center gap-2"
               >
                  <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
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
                  {{ t('actions.executeNow') }}
               </button>

               <button
                  v-if="action.status === 'active'"
                  @click="handlePause"
                  class="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center gap-2"
               >
                  <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                     <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z"
                     />
                  </svg>
                  {{ t('actions.pause') }}
               </button>

               <button
                  v-if="action.status === 'paused'"
                  @click="handleResume"
                  class="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center gap-2"
               >
                  <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                     <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"
                     />
                  </svg>
                  {{ t('actions.resume') }}
               </button>

               <button
                  @click="handleViewLogs"
                  class="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center gap-2"
               >
                  <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                     <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                     />
                  </svg>
                  {{ t('actions.viewLogs') }}
               </button>

               <div class="border-t border-gray-200 my-1"></div>

               <button
                  @click="handleEdit"
                  class="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center gap-2"
               >
                  <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                     <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                     />
                  </svg>
                  {{ t('common.edit') }}
               </button>

               <button
                  @click="handleDelete"
                  class="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 flex items-center gap-2"
               >
                  <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                     <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                     />
                  </svg>
                  {{ t('common.delete') }}
               </button>
            </div>
         </div>
      </div>
   </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();

interface Props {
   action: any;
}

const props = defineProps<Props>();

const emit = defineEmits<{
   edit: [action: any];
   delete: [actionId: string];
   pause: [actionId: string];
   resume: [actionId: string];
   execute: [actionId: string];
   viewLogs: [actionId: string];
}>();

const showMenu = ref(false);

function getActionTypeLabel(type: string): string {
   const labels: Record<string, string> = {
      recurring_quote: t('actions.types.recurringQuote'),
      recurring_invoice: t('actions.types.recurringInvoice'),
      follow_up_email: t('actions.types.followUpEmail'),
      stage_reminder: t('actions.types.stageReminder'),
   };
   return labels[type] || type;
}

function getStatusLabel(status: string): string {
   const labels: Record<string, string> = {
      active: t('actions.statuses.active'),
      paused: t('actions.statuses.paused'),
      completed: t('actions.statuses.completed'),
      failed: t('actions.statuses.failed'),
      cancelled: t('actions.statuses.cancelled'),
   };
   return labels[status] || status;
}

function getStatusClass(status: string): string {
   const classes: Record<string, string> = {
      active: 'bg-green-100 text-green-800',
      paused: 'bg-yellow-100 text-yellow-800',
      completed: 'bg-blue-100 text-blue-800',
      failed: 'bg-red-100 text-red-800',
      cancelled: 'bg-gray-100 text-gray-800',
   };
   return classes[status] || 'bg-gray-100 text-gray-800';
}

function getScheduleLabel(scheduleType: string, config: any): string {
   if (scheduleType === 'monthly') {
      const day = config?.day_of_month || 1;
      const time = config?.time || '09:00';
      return t('actions.schedules.monthly', { day, time });
   } else if (scheduleType === 'weekly') {
      const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
      const dayOfWeek = days[config?.day_of_week || 0];
      const time = config?.time || '09:00';
      return t('actions.schedules.weekly', { day: dayOfWeek, time });
   } else if (scheduleType === 'daily') {
      const time = config?.time || '09:00';
      return t('actions.schedules.daily', { time });
   } else if (scheduleType === 'one_time') {
      return t('actions.schedules.oneTime');
   }
   return scheduleType;
}

function formatDate(dateString: string): string {
   const date = new Date(dateString);
   return date.toLocaleString();
}

function handleEdit() {
   showMenu.value = false;
   emit('edit', props.action);
}

function handleDelete() {
   showMenu.value = false;
   emit('delete', props.action.id);
}

function handlePause() {
   showMenu.value = false;
   emit('pause', props.action.id);
}

function handleResume() {
   showMenu.value = false;
   emit('resume', props.action.id);
}

function handleExecute() {
   showMenu.value = false;
   emit('execute', props.action.id);
}

function handleViewLogs() {
   showMenu.value = false;
   emit('viewLogs', props.action.id);
}

// Click outside directive
const vClickOutside = {
   mounted(el: any, binding: any) {
      el.clickOutsideEvent = (event: Event) => {
         if (!(el === event.target || el.contains(event.target))) {
            binding.value();
         }
      };
      document.addEventListener('click', el.clickOutsideEvent);
   },
   unmounted(el: any) {
      document.removeEventListener('click', el.clickOutsideEvent);
   },
};
</script>
