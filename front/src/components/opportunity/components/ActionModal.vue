<template>
   <div
      v-if="show"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
      @click.self="handleClose"
   >
      <div class="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto m-4">
         <div
            class="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between"
         >
            <h2 class="text-xl font-semibold text-gray-900">
               {{ isEdit ? t('actions.editAction') : t('actions.createAction') }}
            </h2>
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

         <form @submit.prevent="handleSubmit" class="p-6 space-y-6">
            <!-- Action Type -->
            <div>
               <label class="block text-sm font-medium text-gray-700 mb-2">
                  {{ t('actions.actionType') }} <span class="text-red-500">*</span>
               </label>
               <select
                  v-model="formData.action_type"
                  required
                  class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
               >
                  <option value="">{{ t('actions.selectType') }}</option>
                  <option value="recurring_quote">{{ t('actions.types.recurringQuote') }}</option>
                  <option value="recurring_invoice">
                     {{ t('actions.types.recurringInvoice') }}
                  </option>
                  <option value="follow_up_email">{{ t('actions.types.followUpEmail') }}</option>
                  <option value="stage_reminder">{{ t('actions.types.stageReminder') }}</option>
               </select>
            </div>

            <!-- Schedule Type -->
            <div>
               <label class="block text-sm font-medium text-gray-700 mb-2">
                  {{ t('actions.scheduleType') }} <span class="text-red-500">*</span>
               </label>
               <select
                  v-model="formData.schedule_type"
                  required
                  @change="handleScheduleTypeChange"
                  class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
               >
                  <option value="">{{ t('actions.selectSchedule') }}</option>
                  <option value="monthly">{{ t('actions.scheduleTypes.monthly') }}</option>
                  <option value="weekly">{{ t('actions.scheduleTypes.weekly') }}</option>
                  <option value="daily">{{ t('actions.scheduleTypes.daily') }}</option>
                  <option value="one_time">{{ t('actions.scheduleTypes.oneTime') }}</option>
               </select>
            </div>

            <!-- Schedule Configuration -->
            <div v-if="formData.schedule_type" class="space-y-4">
               <!-- Monthly Schedule -->
               <div v-if="formData.schedule_type === 'monthly'" class="grid grid-cols-2 gap-4">
                  <div>
                     <label class="block text-sm font-medium text-gray-700 mb-2">
                        {{ t('actions.dayOfMonth') }}
                     </label>
                     <input
                        v-model.number="formData.schedule_config.day_of_month"
                        type="number"
                        min="1"
                        max="31"
                        required
                        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                     />
                  </div>
                  <div>
                     <label class="block text-sm font-medium text-gray-700 mb-2">{{
                        t('actions.time')
                     }}</label>
                     <input
                        v-model="formData.schedule_config.time"
                        type="time"
                        required
                        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                     />
                  </div>
               </div>

               <!-- Weekly Schedule -->
               <div v-if="formData.schedule_type === 'weekly'" class="grid grid-cols-2 gap-4">
                  <div>
                     <label class="block text-sm font-medium text-gray-700 mb-2">
                        {{ t('actions.dayOfWeek') }}
                     </label>
                     <select
                        v-model.number="formData.schedule_config.day_of_week"
                        required
                        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                     >
                        <option :value="0">{{ t('days.sunday') }}</option>
                        <option :value="1">{{ t('days.monday') }}</option>
                        <option :value="2">{{ t('days.tuesday') }}</option>
                        <option :value="3">{{ t('days.wednesday') }}</option>
                        <option :value="4">{{ t('days.thursday') }}</option>
                        <option :value="5">{{ t('days.friday') }}</option>
                        <option :value="6">{{ t('days.saturday') }}</option>
                     </select>
                  </div>
                  <div>
                     <label class="block text-sm font-medium text-gray-700 mb-2">{{
                        t('actions.time')
                     }}</label>
                     <input
                        v-model="formData.schedule_config.time"
                        type="time"
                        required
                        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                     />
                  </div>
               </div>

               <!-- Daily Schedule -->
               <div v-if="formData.schedule_type === 'daily'">
                  <label class="block text-sm font-medium text-gray-700 mb-2">{{
                     t('actions.time')
                  }}</label>
                  <input
                     v-model="formData.schedule_config.time"
                     type="time"
                     required
                     class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
               </div>

               <!-- One Time Schedule -->
               <div v-if="formData.schedule_type === 'one_time'">
                  <label class="block text-sm font-medium text-gray-700 mb-2">
                     {{ t('actions.executionDate') }}
                  </label>
                  <input
                     v-model="formData.schedule_config.execution_date"
                     type="datetime-local"
                     required
                     class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
               </div>
            </div>

            <!-- Max Executions (optional) -->
            <div>
               <label class="block text-sm font-medium text-gray-700 mb-2">
                  {{ t('actions.maxExecutions') }}
                  <span class="text-gray-500 text-xs">({{ t('common.optional') }})</span>
               </label>
               <input
                  v-model.number="formData.max_executions"
                  type="number"
                  min="1"
                  :placeholder="t('actions.maxExecutionsUnlimited')"
                  class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
               />
            </div>

            <!-- Action-Specific Configuration -->
            <div v-if="formData.action_type" class="border-t border-gray-200 pt-6">
               <h3 class="text-lg font-medium text-gray-900 mb-4">
                  {{ t('actions.actionConfiguration') }}
               </h3>

               <!-- Recurring Quote Config -->
               <div v-if="formData.action_type === 'recurring_quote'" class="space-y-4">
                  <div>
                     <label class="block text-sm font-medium text-gray-700 mb-2">
                        {{ t('actions.config.validityDays') }}
                     </label>
                     <input
                        v-model.number="formData.action_config.validity_days"
                        type="number"
                        min="1"
                        :placeholder="t('actions.defaultDaysPlaceholder')"
                        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                     />
                     <p class="text-xs text-gray-500 mt-1">
                        {{ t('actions.config.validityDaysHelp') }}
                     </p>
                  </div>
                  <div>
                     <label class="block text-sm font-medium text-gray-700 mb-2">
                        {{ t('actions.config.emailSubject') }}
                     </label>
                     <input
                        v-model="formData.action_config.email_subject"
                        type="text"
                        :placeholder="t('actions.config.newQuotePlaceholder')"
                        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                     />
                  </div>
               </div>

               <!-- Recurring Invoice Config -->
               <div v-if="formData.action_type === 'recurring_invoice'" class="space-y-4">
                  <div>
                     <label class="block text-sm font-medium text-gray-700 mb-2">
                        {{ t('actions.config.paymentTermsDays') }}
                     </label>
                     <input
                        v-model.number="formData.action_config.payment_terms_days"
                        type="number"
                        min="1"
                        :placeholder="t('actions.defaultDaysPlaceholder')"
                        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                     />
                     <p class="text-xs text-gray-500 mt-1">
                        {{ t('actions.config.paymentTermsDaysHelp') }}
                     </p>
                  </div>
                  <div>
                     <label class="flex items-center gap-2">
                        <input
                           v-model="formData.action_config.auto_send"
                           type="checkbox"
                           class="rounded"
                        />
                        <span class="text-sm text-gray-700">{{
                           t('actions.config.autoSend')
                        }}</span>
                     </label>
                  </div>
               </div>

               <!-- Follow-up Email Config -->
               <div v-if="formData.action_type === 'follow_up_email'" class="space-y-4">
                  <div>
                     <label class="block text-sm font-medium text-gray-700 mb-2">
                        {{ t('actions.config.emailTemplate') }}
                     </label>
                     <select
                        v-model="formData.action_config.template_id"
                        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                     >
                        <option value="">{{ t('actions.config.selectTemplate') }}</option>
                        <option value="follow_up_general">
                           {{ t('actions.config.templates.followUpGeneral') }}
                        </option>
                        <option value="follow_up_quote">
                           {{ t('actions.config.templates.followUpQuote') }}
                        </option>
                        <option value="follow_up_invoice">
                           {{ t('actions.config.templates.followUpInvoice') }}
                        </option>
                     </select>
                  </div>
                  <div>
                     <label class="block text-sm font-medium text-gray-700 mb-2">
                        {{ t('actions.config.emailSubject') }}
                     </label>
                     <input
                        v-model="formData.action_config.subject"
                        type="text"
                        :placeholder="t('actions.config.followUpPlaceholder')"
                        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                     />
                  </div>
               </div>

               <!-- Stage Reminder Config -->
               <div v-if="formData.action_type === 'stage_reminder'" class="space-y-4">
                  <div>
                     <label class="block text-sm font-medium text-gray-700 mb-2">
                        {{ t('actions.config.reminderMessage') }}
                     </label>
                     <textarea
                        v-model="formData.action_config.message"
                        rows="3"
                        :placeholder="t('actions.config.stageReminderPlaceholder')"
                        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                     ></textarea>
                  </div>
                  <div>
                     <label class="block text-sm font-medium text-gray-700 mb-2">
                        {{ t('actions.config.notifyUsers') }}
                     </label>
                     <input
                        v-model="formData.action_config.notify_users"
                        type="text"
                        :placeholder="t('actions.config.notifyUsersPlaceholder')"
                        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                     />
                     <p class="text-xs text-gray-500 mt-1">
                        {{ t('actions.config.notifyUsersHelp') }}
                     </p>
                  </div>
               </div>
            </div>

            <!-- Form Actions -->
            <div class="flex items-center justify-end gap-3 pt-6 border-t border-gray-200">
               <button
                  type="button"
                  @click="handleClose"
                  class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
               >
                  {{ t('common.cancel') }}
               </button>
               <button
                  type="submit"
                  :disabled="loading"
                  class="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
               >
                  {{
                     loading ? t('common.saving') : isEdit ? t('common.save') : t('common.create')
                  }}
               </button>
            </div>
         </form>
      </div>
   </div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();

interface Props {
   show: boolean;
   opportunityId: string;
   action?: any;
}

const props = defineProps<Props>();

const emit = defineEmits<{
   close: [];
   save: [data: any];
}>();

const loading = ref(false);

const isEdit = computed(() => !!props.action);

const formData = ref({
   action_type: '',
   schedule_type: '',
   schedule_config: {} as any,
   action_config: {} as any,
   max_executions: null as number | null,
});

// Initialize form when action changes
watch(
   () => props.action,
   (action) => {
      if (action) {
         formData.value = {
            action_type: action.action_type || '',
            schedule_type: action.schedule_type || '',
            schedule_config: action.schedule_config ? { ...action.schedule_config } : {},
            action_config: action.action_config ? { ...action.action_config } : {},
            max_executions: action.max_executions || null,
         };
      } else {
         resetForm();
      }
   },
   { immediate: true }
);

function resetForm() {
   formData.value = {
      action_type: '',
      schedule_type: '',
      schedule_config: {},
      action_config: {},
      max_executions: null,
   };
}

function handleScheduleTypeChange() {
   // Reset schedule config when type changes
   if (formData.value.schedule_type === 'monthly') {
      formData.value.schedule_config = { day_of_month: 1, time: '09:00' };
   } else if (formData.value.schedule_type === 'weekly') {
      formData.value.schedule_config = { day_of_week: 1, time: '09:00' };
   } else if (formData.value.schedule_type === 'daily') {
      formData.value.schedule_config = { time: '09:00' };
   } else if (formData.value.schedule_type === 'one_time') {
      formData.value.schedule_config = { execution_date: '' };
   }
}

function handleClose() {
   emit('close');
   resetForm();
}

async function handleSubmit() {
   try {
      loading.value = true;
      const payload: any = {
         ...formData.value,
         opportunity_id: props.opportunityId,
      };

      if (isEdit.value) {
         payload.id = props.action.id;
      }

      emit('save', payload);
   } catch (error) {
      console.error('Error submitting form:', error);
   } finally {
      loading.value = false;
   }
}
</script>
