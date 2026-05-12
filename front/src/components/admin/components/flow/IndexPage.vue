<template>
   <div>
      <AdminNavHeader />
      <div class="p-6 space-y-6">
         <div>
            <h1 class="text-2xl font-bold text-slate-900">Flow</h1>
            <p class="text-sm text-slate-600">
               Pipeline next-step actions, their relations, and color mapping.
            </p>
         </div>

         <div class="grid grid-cols-1 xl:grid-cols-2 gap-6">
            <div
               v-for="stage in flow"
               :key="stage.stage"
               class="bg-white rounded-lg shadow border border-slate-200 p-4"
            >
               <div class="flex items-center justify-between mb-3">
                  <div>
                     <div class="text-xs uppercase tracking-wide text-slate-500">Stage</div>
                     <div class="text-lg font-semibold text-slate-900">
                        {{ t(stage.stageLabelKey) }}
                     </div>
                  </div>
                  <span class="text-xs text-slate-500">{{ stage.stage }}</span>
               </div>

               <div v-if="stage.actions.length === 0" class="text-sm text-slate-500">
                  No next actions.
               </div>

               <div v-else class="space-y-3">
                  <div
                     v-for="(action, index) in stage.actions"
                     :key="index"
                     class="flex items-start justify-between gap-3"
                  >
                     <div>
                        <div class="text-sm font-semibold text-slate-900">
                           {{ t(action.labelKey) }}
                        </div>
                        <div class="text-xs text-slate-500">
                           {{ t(action.descriptionKey) }}
                        </div>
                        <div class="mt-2 flex flex-wrap items-center gap-2 text-xs text-slate-600">
                           <span class="font-medium text-slate-700">
                              {{ t(stage.stageLabelKey) }}
                           </span>
                           <span class="text-slate-400">→</span>
                           <span>{{ t(action.labelKey) }}</span>
                           <span class="text-slate-400">→</span>
                           <span v-if="action.targetStage" class="font-medium text-slate-700">
                              {{ t(`opportunities.stages.${action.targetStage}`) }}
                           </span>
                           <span v-else-if="action.type">{{ action.typeLabel }}</span>
                        </div>
                     </div>
                     <span
                        class="px-2.5 py-1 rounded-full text-xs font-semibold whitespace-nowrap"
                        :class="action.color"
                     >
                        {{ action.color }}
                     </span>
                  </div>
               </div>
            </div>
         </div>
      </div>
   </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import AdminNavHeader from '../../AdminNavHeader.vue';
import { useI18n } from '../../../../i18n/useI18n';

const { t } = useI18n();

const flow = computed(() => [
   {
      stage: 'NEW_LEAD',
      stageLabelKey: 'opportunities.stages.NEW_LEAD',
      actions: [
         {
            labelKey: 'opportunities.stageActions.startQualifying.label',
            descriptionKey: 'opportunities.stageActions.startQualifying.description',
            targetStage: 'QUALIFYING',
            color: 'bg-blue-600 text-white',
         },
         {
            labelKey: 'opportunities.stageActions.reject.label',
            descriptionKey: 'opportunities.stageActions.reject.description',
            targetStage: 'CLOSED_LOST',
            color: 'bg-red-600 text-white',
         },
      ],
   },
   {
      stage: 'QUALIFYING',
      stageLabelKey: 'opportunities.stages.QUALIFYING',
      actions: [
         {
            labelKey: 'opportunities.stageActions.needsDefined.label',
            descriptionKey: 'opportunities.stageActions.needsDefined.description',
            targetStage: 'NEEDS_DEFINED',
            color: 'bg-indigo-600 text-white',
         },
         {
            labelKey: 'opportunities.stageActions.disqualify.label',
            descriptionKey: 'opportunities.stageActions.disqualify.description',
            targetStage: 'CLOSED_LOST',
            color: 'bg-red-600 text-white',
         },
      ],
   },
   {
      stage: 'NEEDS_DEFINED',
      stageLabelKey: 'opportunities.stages.NEEDS_DEFINED',
      actions: [
         {
            labelKey: 'opportunities.stageActions.rfpReceived.label',
            descriptionKey: 'opportunities.stageActions.rfpReceived.description',
            targetStage: 'RFP_IN_PROGRESS',
            color: 'bg-purple-600 text-white',
         },
         {
            labelKey: 'opportunities.stageActions.rfqReceived.label',
            descriptionKey: 'opportunities.stageActions.rfqReceived.description',
            targetStage: 'RFQ_IN_PROGRESS',
            color: 'bg-fuchsia-600 text-white',
         },
      ],
   },
   {
      stage: 'RFP_IN_PROGRESS',
      stageLabelKey: 'opportunities.stages.RFP_IN_PROGRESS',
      actions: [
         {
            labelKey: 'opportunities.stageActions.sendProposal.label',
            descriptionKey: 'opportunities.stageActions.sendProposal.description',
            targetStage: 'OFFER_SENT',
            color: 'bg-pink-600 text-white',
         },
      ],
   },
   {
      stage: 'RFQ_IN_PROGRESS',
      stageLabelKey: 'opportunities.stages.RFQ_IN_PROGRESS',
      actions: [
         {
            labelKey: 'opportunities.stageActions.editQuote.label',
            descriptionKey: 'opportunities.stageActions.editQuote.description',
            type: 'navigation',
            typeLabel: 'Navigation → /opportunities/:id/quote',
            color: 'bg-indigo-600 text-white',
         },
         {
            labelKey: 'opportunities.stageActions.sendQuote.label',
            descriptionKey: 'opportunities.stageActions.sendQuote.description',
            targetStage: 'OFFER_SENT',
            color: 'bg-pink-600 text-white',
         },
      ],
   },
   {
      stage: 'OFFER_SENT',
      stageLabelKey: 'opportunities.stages.OFFER_SENT',
      actions: [
         {
            labelKey: 'opportunities.stageActions.startNegotiation.label',
            descriptionKey: 'opportunities.stageActions.startNegotiation.description',
            targetStage: 'NEGOTIATION',
            color: 'bg-orange-600 text-white',
         },
         {
            labelKey: 'opportunities.stageActions.commitment.label',
            descriptionKey: 'opportunities.stageActions.commitment.description',
            targetStage: 'COMMITMENT',
            color: 'bg-green-600 text-white',
         },
         {
            labelKey: 'opportunities.stageActions.rejected.label',
            descriptionKey: 'opportunities.stageActions.rejected.description',
            targetStage: 'CLOSED_LOST',
            color: 'bg-red-600 text-white',
         },
      ],
   },
   {
      stage: 'NEGOTIATION',
      stageLabelKey: 'opportunities.stages.NEGOTIATION',
      actions: [
         {
            labelKey: 'opportunities.stageActions.editQuote.label',
            descriptionKey: 'opportunities.stageActions.editQuote.description',
            type: 'navigation',
            typeLabel: 'Navigation → /opportunities/:id/quote',
            color: 'bg-blue-600 text-white',
         },
         {
            labelKey: 'opportunities.stageActions.commitment.label',
            descriptionKey: 'opportunities.stageActions.commitment.description',
            targetStage: 'COMMITMENT',
            color: 'bg-emerald-600 text-white',
         },
         {
            labelKey: 'opportunities.stageActions.lostDeal.label',
            descriptionKey: 'opportunities.stageActions.lostDeal.description',
            targetStage: 'CLOSED_LOST',
            color: 'bg-red-600 text-white',
         },
      ],
   },
   {
      stage: 'COMMITMENT',
      stageLabelKey: 'opportunities.stages.COMMITMENT',
      actions: [
         {
            labelKey: 'opportunities.stageActions.startPreparation.label',
            descriptionKey: 'opportunities.stageActions.startPreparation.description',
            targetStage: 'PREPARATION',
            color: 'bg-amber-600 text-white',
         },
      ],
   },
   {
      stage: 'PREPARATION',
      stageLabelKey: 'opportunities.stages.PREPARATION',
      actions: [
         {
            labelKey: 'opportunities.stageActions.startDelivery.label',
            descriptionKey: 'opportunities.stageActions.startDelivery.description',
            targetStage: 'DELIVERY_IN_PROGRESS',
            color: 'bg-amber-600 text-white',
         },
      ],
   },
   {
      stage: 'DELIVERY_IN_PROGRESS',
      stageLabelKey: 'opportunities.stages.DELIVERY_IN_PROGRESS',
      actions: [
         {
            labelKey: 'opportunities.stageActions.delivered.label',
            descriptionKey: 'opportunities.stageActions.delivered.description',
            targetStage: 'ACCEPTED',
            color: 'bg-green-600 text-white',
         },
      ],
   },
   {
      stage: 'ACCEPTED',
      stageLabelKey: 'opportunities.stages.ACCEPTED',
      actions: [
         {
            labelKey: 'opportunities.stageActions.sendInvoice.label',
            descriptionKey: 'opportunities.stageActions.sendInvoice.description',
            type: 'generate-invoice',
            typeLabel: 'Generate invoice → open invoice page',
            color: 'bg-blue-600 text-white',
         },
      ],
   },
   {
      stage: 'INVOICED',
      stageLabelKey: 'opportunities.stages.INVOICED',
      actions: [
         {
            labelKey: 'opportunities.stageActions.paymentReceived.label',
            descriptionKey: 'opportunities.stageActions.paymentReceived.description',
            targetStage: 'PAID',
            color: 'bg-green-600 text-white',
         },
      ],
   },
   {
      stage: 'PAID',
      stageLabelKey: 'opportunities.stages.PAID',
      actions: [
         {
            labelKey: 'opportunities.stageActions.closeWon.label',
            descriptionKey: 'opportunities.stageActions.closeWon.description',
            targetStage: 'CLOSED_WON',
            color: 'bg-green-700 text-white',
         },
      ],
   },
]);
</script>
