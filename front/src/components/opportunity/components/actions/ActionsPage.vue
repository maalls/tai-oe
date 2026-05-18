<template>
   <div class="opportunity-page">
      <OpportunityHeader :opportunityId="opportunityId" activeTab="actions" />

      <div v-if="errorMessage" class="p-4 bg-red-100 text-red-700 rounded-lg">
         {{ errorMessage }}
      </div>

      <div v-if="isLoading" class="flex justify-center items-center py-12">
         <div class="text-gray-500">{{ t('opportunities.loadingActions') }}</div>
      </div>

      <div v-else class="opportunity-page-section m-4 bg-white rounded-lg shadow p-6">
         <div class="flex justify-between items-center">
            <h2 class="text-xl font-semibold text-gray-900">
               {{ t('opportunities.actionsTitle') }}
            </h2>
            <button
               @click="showCreateModal = true"
               class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
               {{ t('opportunities.createAction') }}
            </button>
         </div>

         <div v-if="actions.length === 0" class="text-center py-12 text-gray-500">
            {{ t('opportunities.noActionsFound') }}
         </div>

         <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <ActionCard
               v-for="action in actions"
               :key="action.id"
               :action="action"
               :t="t"
               :getActionTypeLabel="getActionTypeLabel"
               :getStatusColor="getStatusColor"
               :formatDate="formatDate"
               @pause="pauseAction"
               @resume="resumeAction"
               @edit="editAction"
               @delete="deleteAction"
               @execute="executeAction"
               @logs="viewLogs"
            />
         </div>
      </div>

      <!-- Create/Edit Modal -->
      <div
         v-if="showCreateModal"
         class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
      >
         <div class="bg-white rounded-lg shadow-lg p-6 w-96">
            <h3 class="text-lg font-semibold">
               {{ editingAction ? t('common.edit') : t('common.create') }}
               {{ t('opportunities.action') }}
            </h3>
            <form @submit.prevent="saveAction" class="space-y-4">
               <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">
                     {{ t('opportunities.actionType') }} *
                  </label>
                  <select
                     v-model="formData.action_type"
                     required
                     class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                     <option value="">{{ t('actions.selectType') }}</option>
                     <option value="recurring_quote">
                        {{ t('actions.types.recurringQuote') }}
                     </option>
                     <option value="recurring_invoice">
                        {{ t('actions.types.recurringInvoice') }}
                     </option>
                     <option value="follow_up_email">{{ t('actions.types.followUpEmail') }}</option>
                     <option value="stage_reminder">{{ t('actions.types.stageReminder') }}</option>
                  </select>
               </div>
               <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">
                     {{ t('actions.scheduleType') }} *
                  </label>
                  <select
                     v-model="formData.schedule_type"
                     required
                     class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                     <option value="">{{ t('actions.selectSchedule') }}</option>
                     <option value="daily">{{ t('actions.scheduleTypes.daily') }}</option>
                     <option value="weekly">{{ t('actions.scheduleTypes.weekly') }}</option>
                     <option value="monthly">{{ t('actions.scheduleTypes.monthly') }}</option>
                     <option value="one_time">{{ t('actions.scheduleTypes.oneTime') }}</option>
                     <option value="custom_cron">
                        {{ t('actions.scheduleTypes.customCron') }}
                     </option>
                  </select>
               </div>
               <div class="flex justify-end gap-2 pt-4">
                  <button
                     type="button"
                     @click="closeModal"
                     class="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                  >
                     {{ t('common.cancel') }}
                  </button>
                  <button
                     type="submit"
                     class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                  >
                     {{ t('common.save') }}
                  </button>
               </div>
            </form>
         </div>
      </div>

      <!-- Logs Modal -->
      <div
         v-if="showLogsModal"
         class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
      >
         <div class="bg-white rounded-lg shadow-lg p-6 w-full max-w-2xl max-h-96 overflow-y-auto">
            <div class="flex justify-between items-center">
               <h3 class="text-lg font-semibold">{{ t('opportunities.actionLogs') }}</h3>
               <button @click="showLogsModal = false" class="text-gray-500 hover:text-gray-700">
                  <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                     <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M6 18L18 6M6 6l12 12"
                     />
                  </svg>
               </button>
            </div>

            <div v-if="actionLogs.length === 0" class="text-center py-8 text-gray-500">
               {{ t('opportunities.noLogs') }}
            </div>

            <div v-else class="space-y-3">
               <div
                  v-for="log in actionLogs"
                  :key="log.id"
                  class="p-3 bg-gray-50 rounded border border-gray-200"
               >
                  <div class="flex justify-between items-start mb-2">
                     <span class="font-medium text-sm">
                        {{ log.type }}:
                        <span
                           class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ml-2"
                           :class="getLogStatusColor(log.status)"
                        >
                           {{ log.status }}
                        </span>
                     </span>
                     <span class="text-xs text-gray-500">{{ formatDate(log.created_at) }}</span>
                  </div>
                  <p class="text-sm text-gray-700">{{ log.message }}</p>
               </div>
            </div>
         </div>
      </div>

      <!-- Delete Confirmation Modal -->
      <div
         v-if="showDeleteConfirm"
         class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
      >
         <div class="bg-white rounded-lg shadow-lg p-6 w-96">
            <h3 class="text-lg font-semibold">{{ t('opportunities.confirmDeleteAction') }}</h3>
            <p class="text-gray-600">
               {{ t('opportunities.deleteActionWarning') }}
               <strong>{{ deletingAction?.title }}</strong>
            </p>
            <div class="flex justify-end gap-2">
               <button
                  @click="showDeleteConfirm = false"
                  class="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
               >
                  {{ t('common.cancel') }}
               </button>
               <button
                  @click="confirmDeleteAction"
                  class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
               >
                  {{ t('common.delete') }}
               </button>
            </div>
         </div>
      </div>
   </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import {
   createAction,
   deleteAction as deleteOpportunityAction,
   executeAction as executeOpportunityAction,
   getActionLogs,
   listOpportunityActions,
   pauseAction as pauseOpportunityAction,
   resumeAction as resumeOpportunityAction,
   updateAction,
} from '../../../../api/action';
import OpportunityHeader from '../../OpportunityHeader.vue';
import { useI18n } from '../../../../i18n/useI18n';
import { useAuth } from '../../../../stores/auth';
import ActionCard from './components/action/card.vue';

const route = useRoute();
const opportunityId = route.params.id as string;
const { t, locale } = useI18n();
const { getValidToken } = useAuth();

const isLoading = ref(true);
const errorMessage = ref('');
const actions = ref<any[]>([]);
const actionLogs = ref<any[]>([]);

const showCreateModal = ref(false);
const showLogsModal = ref(false);
const showDeleteConfirm = ref(false);

const editingAction = ref<any>(null);
const deletingAction = ref<any>(null);

const formData = ref({
   action_type: '',
   schedule_type: '',
   schedule_config: {} as any,
});

const resetForm = () => {
   formData.value = {
      action_type: '',
      schedule_type: '',
      schedule_config: {},
   };
   editingAction.value = null;
};

const getActionTypeLabel = (actionType?: string) => {
   if (!actionType) return '';
   const normalized = actionType.replace(/_([a-z])/g, (_, c) => c.toUpperCase());
   const key = `actions.types.${normalized}` as const;
   return t(key) || actionType;
};

const closeModal = () => {
   showCreateModal.value = false;
   resetForm();
};

const requireToken = async () => {
   const token = await getValidToken();
   if (!token) {
      throw new Error(t('opportunities.errors.userNotAuthenticated'));
   }
   return token;
};

const loadActions = async () => {
   try {
      const token = await requireToken();
      actions.value = await listOpportunityActions(opportunityId, token);
   } catch (error: any) {
      errorMessage.value = error?.message || t('opportunities.failedToLoadActions');
      console.error('[ActionsPage] Error loading actions:', error);
   } finally {
      isLoading.value = false;
   }
};

const editAction = (action: any) => {
   editingAction.value = action;
   formData.value = {
      action_type: action.action_type,
      schedule_type: action.schedule_type,
      schedule_config: action.schedule_config || {},
   };
   showCreateModal.value = true;
};

const saveAction = async () => {
   try {
      const token = await requireToken();
      const payload = {
         action_type: formData.value.action_type,
         schedule_type: formData.value.schedule_type,
         schedule_config: formData.value.schedule_config || {},
      };

      if (editingAction.value) {
         const updated = await updateAction(editingAction.value.id, payload, token);

         const index = actions.value.findIndex((a) => a.id === editingAction.value.id);
         if (index !== -1) {
            actions.value[index] = updated;
         }
      } else {
         const created = await createAction(
            {
               ...payload,
               opportunity_id: opportunityId,
            },
            token
         );

         actions.value.unshift(created);
      }

      closeModal();
   } catch (error: any) {
      errorMessage.value = error?.message || t('opportunities.errors.failedToSaveAction');
      console.error('[ActionsPage] Error saving action:', error);
   }
};

const deleteAction = (action: any) => {
   deletingAction.value = action;
   showDeleteConfirm.value = true;
};

const confirmDeleteAction = async () => {
   try {
      const token = await requireToken();
      await deleteOpportunityAction(deletingAction.value.id, token);

      actions.value = actions.value.filter((a) => a.id !== deletingAction.value.id);
      showDeleteConfirm.value = false;
      deletingAction.value = null;
   } catch (error: any) {
      errorMessage.value = error?.message || t('opportunities.errors.failedToDeleteAction');
      console.error('[ActionsPage] Error deleting action:', error);
   }
};

const pauseAction = async (action: any) => {
   try {
      const token = await requireToken();
      const updated = await pauseOpportunityAction(action.id, token);
      action.status = updated.status;
   } catch (error: any) {
      errorMessage.value = error?.message || t('opportunities.errors.failedToPauseAction');
      console.error('[ActionsPage] Error pausing action:', error);
   }
};

const resumeAction = async (action: any) => {
   try {
      const token = await requireToken();
      const updated = await resumeOpportunityAction(action.id, token);
      action.status = updated.status;
   } catch (error: any) {
      errorMessage.value = error?.message || t('opportunities.errors.failedToResumeAction');
      console.error('[ActionsPage] Error resuming action:', error);
   }
};

const executeAction = async (action: any) => {
   try {
      const token = await requireToken();
      await executeOpportunityAction(action.id, token);

      action.last_executed_at = new Date().toISOString();
   } catch (error: any) {
      errorMessage.value = error?.message || t('opportunities.errors.failedToExecuteAction');
      console.error('[ActionsPage] Error executing action:', error);
   }
};

const viewLogs = async (action: any) => {
   try {
      const token = await requireToken();
      actionLogs.value = await getActionLogs(action.id, token);
      showLogsModal.value = true;
   } catch (error: any) {
      errorMessage.value = error?.message || t('opportunities.errors.failedToLoadLogs');
      console.error('[ActionsPage] Error loading logs:', error);
   }
};

const getStatusColor = (status: string) => {
   const colors: Record<string, string> = {
      ACTIVE: 'bg-green-100 text-green-800',
      PAUSED: 'bg-yellow-100 text-yellow-800',
      COMPLETED: 'bg-blue-100 text-blue-800',
      FAILED: 'bg-red-100 text-red-800',
   };
   return colors[status] || 'bg-gray-100 text-gray-800';
};

const getLogStatusColor = (status: string) => {
   const colors: Record<string, string> = {
      SUCCESS: 'bg-green-100 text-green-800',
      FAILED: 'bg-red-100 text-red-800',
      PENDING: 'bg-yellow-100 text-yellow-800',
   };
   return colors[status] || 'bg-gray-100 text-gray-800';
};

const formatDate = (dateString: string) => {
   if (!dateString) return '—';
   const date = new Date(dateString);
   const resolvedLocale = locale.value === 'fr' ? 'fr-FR' : 'en-US';
   return new Intl.DateTimeFormat(resolvedLocale, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
   }).format(date);
};

onMounted(() => {
   loadActions();
});
</script>
