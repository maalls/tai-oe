<template>
   <div class="bg-white rounded-lg shadow p-6">
      <div class="space-y-4">
         <!-- Current Stage Display -->
         <div class="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
            <div>
               <div class="text-sm text-gray-600 mb-1">
                  {{ t('opportunities.stageManager.currentStage') }}
               </div>
               <div class="text-lg font-semibold text-gray-900">
                  {{ getStageLabel(currentStage) }}
               </div>
            </div>
            <div
               :class="getStageColorClass(currentStage)"
               class="px-3 py-1 rounded-full text-sm font-medium"
            >
               {{ getStatusLabel(currentStatus) }}
            </div>
         </div>

         <!-- Quick Actions -->
         <div v-if="nextActions.length > 0" class="space-y-2">
            <div class="flex items-center justify-between mb-2">
               <div class="text-sm font-medium text-gray-700">
                  {{ t('opportunities.stageManager.nextActions') }}
               </div>
               <button
                  type="button"
                  class="text-xs text-gray-600 hover:text-gray-900 underline disabled:opacity-50"
                  :disabled="!canUndo || isUpdating"
                  @click="undoLastTransition"
               >
                  {{ t('opportunities.stageManager.undo') }}
               </button>
            </div>
            <button
               v-for="action in nextActions"
               :key="action.stage || action.path"
               @click="handleAction(action)"
               :class="action.color"
               class="w-full px-4 py-3 rounded-lg font-medium text-left hover:opacity-90 transition-opacity flex items-center justify-between"
            >
               <div>
                  <div class="font-semibold">{{ action.label }}</div>
                  <div class="text-sm opacity-90">{{ action.description }}</div>
               </div>
               <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                     stroke-linecap="round"
                     stroke-linejoin="round"
                     stroke-width="2"
                     d="M9 5l7 7-7 7"
                  />
               </svg>
            </button>
         </div>

         <!-- Manual Stage Selection -->
         <details class="mt-4">
            <summary class="cursor-pointer text-sm text-gray-600 hover:text-gray-900 py-2">
               {{ t('opportunities.stageManager.manualStageSelection') }}
            </summary>
            <div class="mt-3 space-y-2">
               <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">
                     {{ t('opportunities.stageManager.stageLabel') }}
                  </label>
                  <select
                     v-model="manualStage"
                     class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                     <option v-for="stage in allStages" :key="stage" :value="stage">
                        {{ getStageLabel(stage) }}
                     </option>
                  </select>
               </div>
               <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">
                     {{ t('opportunities.stageManager.statusLabel') }}
                  </label>
                  <select
                     v-model="manualStatus"
                     class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                     <option value="OPEN">{{ getStatusLabel('OPEN') }}</option>
                     <option value="WON">{{ getStatusLabel('WON') }}</option>
                     <option value="LOST">{{ getStatusLabel('LOST') }}</option>
                     <option value="ON_HOLD">{{ getStatusLabel('ON_HOLD') }}</option>
                  </select>
               </div>
               <button
                  @click="updateStage(manualStage, manualStatus)"
                  :disabled="isUpdating"
                  class="w-full px-4 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-800 disabled:bg-gray-400 font-medium"
               >
                  {{
                     isUpdating
                        ? t('opportunities.stageManager.updating')
                        : t('opportunities.stageManager.updateStage')
                  }}
               </button>
            </div>
         </details>

         <!-- Stage History -->
         <div v-if="stageHistory.length > 0" class="mt-6 pt-6">
            <div class="text-sm font-medium text-gray-700 mb-3">
               {{ t('opportunities.stageManager.stageHistory') }}
            </div>
            <div class="space-y-2">
               <div
                  v-for="(transition, index) in stageHistory"
                  :key="index"
                  class="text-sm flex items-center gap-3 py-2"
               >
                  <div class="w-2 h-2 rounded-full bg-blue-500"></div>
                  <div class="flex-1">
                     <span class="font-medium">{{ getStageLabel(transition.from_stage) }}</span>
                     →
                     <span class="font-medium">{{ getStageLabel(transition.to_stage) }}</span>
                  </div>
                  <div class="text-gray-500 text-xs">
                     {{ formatDate(transition.changed_at) }}
                  </div>
               </div>
            </div>
         </div>
      </div>
   </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { supabase } from '../../../../../lib/supabase';
import { useAuth } from '../../../../../stores/auth';
import { useI18n } from '../../../../../i18n/useI18n';

const props = defineProps<{
   opportunityId: string;
}>();

const emit = defineEmits<{
   (e: 'stageUpdated', stage: string, status: string): void;
}>();

const { user, getValidToken } = useAuth();
const { t, te, locale } = useI18n();
const router = useRouter();
const isLoading = ref(true);
const isUpdating = ref(false);
const currentStage = ref('NEW_LEAD');
const currentStatus = ref('OPEN');
const manualStage = ref('NEW_LEAD');
const manualStatus = ref('OPEN');
const stageHistory = ref<any[]>([]);

const allStages = [
   'NEW_LEAD',
   'QUALIFYING',
   'NEEDS_DEFINED',
   'RFP_IN_PROGRESS',
   'RFQ_IN_PROGRESS',
   'OFFER_SENT',
   'NEGOTIATION',
   'COMMITMENT',
   'PREPARATION',
   'DELIVERY_IN_PROGRESS',
   'ACCEPTED',
   'INVOICED',
   'PAID',
   'CLOSED_WON',
   'CLOSED_LOST',
   'ON_HOLD',
];

const stageWorkflow = computed(
   (): Record<
      string,
      Array<{
         stage?: string;
         status?: string;
         type?: string;
         path?: string;
         label: string;
         description: string;
         color: string;
      }>
   > => ({
      NEW_LEAD: [
         {
            stage: 'QUALIFYING',
            status: 'OPEN',
            label: t('opportunities.stageActions.startQualifying.label'),
            description: t('opportunities.stageActions.startQualifying.description'),
            color: 'bg-blue-600 text-white',
         },
         {
            stage: 'CLOSED_LOST',
            status: 'LOST',
            label: t('opportunities.stageActions.reject.label'),
            description: t('opportunities.stageActions.reject.description'),
            color: 'bg-red-600 text-white',
         },
      ],
      QUALIFYING: [
         {
            stage: 'NEEDS_DEFINED',
            status: 'OPEN',
            label: t('opportunities.stageActions.needsDefined.label'),
            description: t('opportunities.stageActions.needsDefined.description'),
            color: 'bg-indigo-600 text-white',
         },
         {
            stage: 'CLOSED_LOST',
            status: 'LOST',
            label: t('opportunities.stageActions.disqualify.label'),
            description: t('opportunities.stageActions.disqualify.description'),
            color: 'bg-red-600 text-white',
         },
      ],
      NEEDS_DEFINED: [
         {
            stage: 'RFP_IN_PROGRESS',
            status: 'OPEN',
            label: t('opportunities.stageActions.rfpReceived.label'),
            description: t('opportunities.stageActions.rfpReceived.description'),
            color: 'bg-purple-600 text-white',
         },
         {
            stage: 'RFQ_IN_PROGRESS',
            status: 'OPEN',
            label: t('opportunities.stageActions.rfqReceived.label'),
            description: t('opportunities.stageActions.rfqReceived.description'),
            color: 'bg-fuchsia-600 text-white',
         },
      ],
      RFP_IN_PROGRESS: [
         {
            stage: 'OFFER_SENT',
            status: 'OPEN',
            label: t('opportunities.stageActions.sendProposal.label'),
            description: t('opportunities.stageActions.sendProposal.description'),
            color: 'bg-pink-600 text-white',
         },
      ],
      RFQ_IN_PROGRESS: [
         {
            type: 'navigation',
            path: '/opportunities/' + props.opportunityId + '/quote',
            label: t('opportunities.stageActions.editQuote.label'),
            description: t('opportunities.stageActions.editQuote.description'),
            color: 'bg-indigo-600 text-white',
         },
         {
            stage: 'OFFER_SENT',
            status: 'OPEN',
            label: t('opportunities.stageActions.sendQuote.label'),
            description: t('opportunities.stageActions.sendQuote.description'),
            color: 'bg-pink-600 text-white',
         },
      ],
      OFFER_SENT: [
         {
            stage: 'NEGOTIATION',
            status: 'OPEN',
            label: t('opportunities.stageActions.startNegotiation.label'),
            description: t('opportunities.stageActions.startNegotiation.description'),
            color: 'bg-orange-600 text-white',
         },
         {
            stage: 'COMMITMENT',
            status: 'OPEN',
            label: t('opportunities.stageActions.commitment.label'),
            description: t('opportunities.stageActions.commitment.description'),
            color: 'bg-green-600 text-white',
         },
         {
            stage: 'CLOSED_LOST',
            status: 'LOST',
            label: t('opportunities.stageActions.rejected.label'),
            description: t('opportunities.stageActions.rejected.description'),
            color: 'bg-red-600 text-white',
         },
      ],
      NEGOTIATION: [
         {
            type: 'navigation',
            path: '/opportunities/' + props.opportunityId + '/quote',
            label: t('opportunities.stageActions.editQuote.label'),
            description: t('opportunities.stageActions.editQuote.description'),
            color: 'bg-blue-600 text-white',
         },
         {
            stage: 'COMMITMENT',
            status: 'OPEN',
            label: t('opportunities.stageActions.commitment.label'),
            description: t('opportunities.stageActions.commitment.description'),
            color: 'bg-emerald-600 text-white',
         },
         {
            stage: 'CLOSED_LOST',
            status: 'LOST',
            label: t('opportunities.stageActions.lostDeal.label'),
            description: t('opportunities.stageActions.lostDeal.description'),
            color: 'bg-red-600 text-white',
         },
      ],
      COMMITMENT: [
         {
            stage: 'PREPARATION',
            status: 'OPEN',
            label: t('opportunities.stageActions.startPreparation.label'),
            description: t('opportunities.stageActions.startPreparation.description'),
            color: 'bg-amber-600 text-white',
         },
      ],
      PREPARATION: [
         {
            stage: 'DELIVERY_IN_PROGRESS',
            status: 'OPEN',
            label: t('opportunities.stageActions.startDelivery.label'),
            description: t('opportunities.stageActions.startDelivery.description'),
            color: 'bg-amber-600 text-white',
         },
      ],
      DELIVERY_IN_PROGRESS: [
         {
            stage: 'ACCEPTED',
            status: 'OPEN',
            label: t('opportunities.stageActions.delivered.label'),
            description: t('opportunities.stageActions.delivered.description'),
            color: 'bg-green-600 text-white',
         },
      ],
      ACCEPTED: [
         {
            type: 'generate-invoice',
            label: t('opportunities.stageActions.sendInvoice.label'),
            description: t('opportunities.stageActions.sendInvoice.description'),
            color: 'bg-blue-600 text-white',
         },
      ],
      INVOICED: [
         {
            stage: 'PAID',
            status: 'OPEN',
            label: t('opportunities.stageActions.paymentReceived.label'),
            description: t('opportunities.stageActions.paymentReceived.description'),
            color: 'bg-green-600 text-white',
         },
      ],
      PAID: [
         {
            stage: 'CLOSED_WON',
            status: 'WON',
            label: t('opportunities.stageActions.closeWon.label'),
            description: t('opportunities.stageActions.closeWon.description'),
            color: 'bg-green-700 text-white',
         },
      ],
   })
);

const nextActions = computed(() => {
   return stageWorkflow.value[currentStage.value] || [];
});

const getStageLabel = (stage?: string) => {
   const resolvedStage = stage || 'NEW_LEAD';
   const key = `opportunities.stages.${resolvedStage}` as const;
   return te(key) ? t(key) : resolvedStage.replace(/_/g, ' ');
};

const getStatusLabel = (status?: string) => {
   const resolvedStatus = status || 'OPEN';
   const key = `opportunities.statuses.${resolvedStatus}` as const;
   return te(key) ? t(key) : resolvedStatus.replace(/_/g, ' ');
};

const getStageColorClass = (stage: string) => {
   const colors: Record<string, string> = {
      NEW_LEAD: 'bg-blue-100 text-blue-700',
      QUALIFYING: 'bg-cyan-100 text-cyan-700',
      NEEDS_DEFINED: 'bg-indigo-100 text-indigo-700',
      RFP_IN_PROGRESS: 'bg-purple-100 text-purple-700',
      RFQ_IN_PROGRESS: 'bg-fuchsia-100 text-fuchsia-700',
      OFFER_SENT: 'bg-pink-100 text-pink-700',
      NEGOTIATION: 'bg-rose-100 text-rose-700',
      COMMITMENT: 'bg-orange-100 text-orange-700',
      PREPARATION: 'bg-amber-100 text-amber-700',
      DELIVERY_IN_PROGRESS: 'bg-amber-100 text-amber-700',
      ACCEPTED: 'bg-green-100 text-green-700',
      INVOICED: 'bg-emerald-100 text-emerald-700',
      PAID: 'bg-teal-100 text-teal-700',
      CLOSED_WON: 'bg-green-200 text-green-800',
      CLOSED_LOST: 'bg-red-100 text-red-700',
      ON_HOLD: 'bg-gray-100 text-gray-700',
   };
   return colors[stage] || 'bg-gray-100 text-gray-700';
};

const formatDate = (dateStr: string) => {
   const resolvedLocale = locale.value === 'fr' ? 'fr-FR' : 'en-US';
   const date = new Date(dateStr);
   return date.toLocaleDateString(resolvedLocale, {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
   });
};

const loadOpportunity = async () => {
   try {
      const { data, error } = await supabase
         .from('opportunity')
         .select('stage, status')
         .eq('id', props.opportunityId)
         .single();

      if (error) throw error;

      if (data) {
         const opportunity = data as any;
         currentStage.value = opportunity.stage || 'NEW_LEAD';
         currentStatus.value = opportunity.status || 'OPEN';
         manualStage.value = currentStage.value;
         manualStatus.value = currentStatus.value;
      }
   } catch (error) {
      console.error('[StageManager] Error loading opportunity:', error);
   }
};

const loadStageHistory = async () => {
   try {
      const { data, error } = await supabase
         .from('opportunity_state_transition')
         .select('*')
         .eq('opportunity_id', props.opportunityId)
         .order('changed_at', { ascending: false })
         .limit(10);

      if (error) throw error;

      stageHistory.value = data || [];
   } catch (error) {
      console.error('[StageManager] Error loading stage history:', error);
   }
};

const getStatusForStage = (stage: string) => {
   if (stage === 'CLOSED_WON') return 'WON';
   if (stage === 'CLOSED_LOST') return 'LOST';
   return 'OPEN';
};

const canUndo = computed(() => stageHistory.value.length > 0);

const undoLastTransition = async () => {
   if (!canUndo.value) return;
   const lastTransition = stageHistory.value[0];
   const previousStage = lastTransition?.from_stage;
   if (!previousStage) return;

   const previousStatus = getStatusForStage(previousStage);
   await updateStage(previousStage, previousStatus);
};

// Handle both stage transitions and navigation actions
const handleAction = async (action: any) => {
   if (action.type === 'navigation' && action.path) {
      router.push(action.path);
      return;
   }
   if (action.type === 'generate-invoice') {
      await generateInvoiceAndOpen();
      return;
   }
   if (action.stage && action.status) {
      updateStage(action.stage, action.status);
   }
};

const generateInvoiceAndOpen = async () => {
   if (!props.opportunityId) return;

   isUpdating.value = true;
   try {
      const token = await getValidToken();
      const response = await fetch(`/api/quote/${props.opportunityId}/invoice`, {
         method: 'POST',
         headers: {
            Authorization: `Bearer ${token}`,
         },
      });

      const result = await response.json();
      if (!response.ok) {
         throw new Error(result?.message || t('opportunities.errors.failedToGenerateInvoice'));
      }

      const invoiceId = result?.invoice?.id as string | undefined;
      await updateStage('INVOICED', 'OPEN');

      if (invoiceId) {
         await router.push(`/opportunities/${props.opportunityId}/invoices/${invoiceId}`);
      } else {
         await router.push(`/opportunities/${props.opportunityId}/invoices`);
      }
   } catch (error) {
      console.error('[StageManager] Error generating invoice:', error);
      alert(t('opportunities.errors.failedToGenerateInvoice'));
   } finally {
      isUpdating.value = false;
   }
};

const updateStage = async (newStage: string, newStatus: string) => {
   isUpdating.value = true;

   try {
      // Update opportunity
      const { error: updateError } = await (supabase.from('opportunity') as any)
         .update({
            stage: newStage,
            status: newStatus,
            updated_at: new Date().toISOString(),
         })
         .eq('id', props.opportunityId);

      if (updateError) throw updateError;

      // Record transition
      await (supabase.from('opportunity_state_transition') as any).insert({
         opportunity_id: props.opportunityId,
         from_stage: currentStage.value,
         to_stage: newStage,
         changed_by: user.value?.id,
         changed_at: new Date().toISOString(),
      });

      // Update local state
      currentStage.value = newStage;
      currentStatus.value = newStatus;
      manualStage.value = newStage;
      manualStatus.value = newStatus;

      // Reload history
      await loadStageHistory();

      // Emit event
      emit('stageUpdated', newStage, newStatus);
   } catch (error) {
      console.error('[StageManager] Error updating stage:', error);
      alert(t('opportunities.stageManager.failedToUpdateStage'));
   } finally {
      isUpdating.value = false;
   }
};

onMounted(async () => {
   isLoading.value = true;
   await Promise.all([loadOpportunity(), loadStageHistory()]);
   isLoading.value = false;
});
</script>
