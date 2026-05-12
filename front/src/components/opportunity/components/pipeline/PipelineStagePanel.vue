<template>
   <component
      :is="resolvedComponent"
      :opportunity="opportunity"
      :account="account"
      :contacts="contacts"
      :isLoading="isLoading"
      :stage="stage"
      @stageUpdated="(stage: string, status: string) => $emit('stageUpdated', stage, status)"
   />
</template>

<script setup lang="ts">
import { computed } from 'vue';
import PipelineStageDefault from './components/PipelineStageDefault/PipelineStageDefault.vue';
import PipelineStageRfp from './components/PipelineStageRfp/PipelineStageRfp.vue';
import PipelineStageOffer from './components/PipelineStageOffer/PipelineStageOffer.vue';
import PipelineStageCommitment from './components/PipelineStageCommitment/PipelineStageCommitment.vue';
import PipelineStagePreparation from './components/PipelineStagePreparation/PipelineStagePreparation.vue';
import PipelineStageDelivery from './components/PipelineStageDelivery/PipelineStageDelivery.vue';
import PipelineStageAccepted from './components/PipelineStageAccepted/PipelineStageAccepted.vue';
import PipelineStageInvoiced from './components/PipelineStageInvoiced/PipelineStageInvoiced.vue';
import PipelineStagePaid from './components/PipelineStagePaid/PipelineStagePaid.vue';
import PipelineStageClosedWon from './components/PipelineStageClosedWon/PipelineStageClosedWon.vue';

const props = defineProps<{
   stage?: string | null;
   opportunity: any | null;
   account: any | null;
   contacts: any[];
   isLoading: boolean;
}>();

const emit = defineEmits<{
   (e: 'stageUpdated', stage: string, status: string): void;
}>();

const stageComponentMap: Record<string, any> = {
   RFP_IN_PROGRESS: PipelineStageRfp,
   RFQ_IN_PROGRESS: PipelineStageRfp,
   OFFER_SENT: PipelineStageOffer,
   NEGOTIATION: PipelineStageOffer,
   COMMITMENT: PipelineStageCommitment,
   PREPARATION: PipelineStagePreparation,
   DELIVERY_IN_PROGRESS: PipelineStageDelivery,
   ACCEPTED: PipelineStageAccepted,
   INVOICED: PipelineStageInvoiced,
   PAID: PipelineStagePaid,
   CLOSED_WON: PipelineStageClosedWon,
};

const resolvedComponent = computed(() => {
   const key = (props.stage || '').toUpperCase();
   return stageComponentMap[key] || PipelineStageDefault;
});
</script>
