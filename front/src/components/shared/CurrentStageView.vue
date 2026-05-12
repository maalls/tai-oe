<template>
   <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <!-- Header -->
      <div class="mb-4">
         <h3 class="text-sm font-semibold text-gray-600 uppercase tracking-wide">
            {{ t('opportunities.stageManager.currentStage') }}
         </h3>
      </div>

      <!-- Stage Badge -->
      <div class="flex items-center justify-between mb-6">
         <div class="flex items-center gap-4">
            <!-- Stage Icon Circle -->
            <div
               :class="getStageIconClass()"
               class="w-12 h-12 rounded-full flex items-center justify-center text-lg font-semibold"
            >
               {{ getStageIcon() }}
            </div>

            <!-- Stage Info -->
            <div>
               <div class="text-2xl font-bold text-gray-900">
                  {{ getStageLabel(stage) }}
               </div>
               <div class="text-sm text-gray-500 mt-1">
                  {{ getStageDescription(stage) }}
               </div>
            </div>
         </div>

         <!-- Status Badge -->
         <div
            :class="getStatusClass(status)"
            class="px-4 py-2 rounded-full text-sm font-semibold whitespace-nowrap"
         >
            {{ getStatusLabel(status) }}
         </div>
      </div>

      <!-- Stage Progress Bar -->
      <div class="mb-6">
         <div class="flex items-center justify-between mb-2">
            <span class="text-xs font-medium text-gray-600">{{
               t('opportunities.stageManager.progress')
            }}</span>
            <span class="text-xs font-medium text-gray-600">{{ getStageProgress() }}%</span>
         </div>
         <div class="w-full bg-gray-200 rounded-full h-2">
            <div
               class="bg-gradient-to-r from-blue-500 to-emerald-500 h-2 rounded-full transition-all duration-300"
               :style="{ width: getStageProgress() + '%' }"
            />
         </div>
      </div>

      <!-- Preparation Custom View -->
      <div v-if="stage === 'PREPARATION'" class="mb-6">
         <div class="bg-amber-50 border border-amber-200 rounded-lg p-4">
            <div class="text-sm font-semibold text-amber-900 mb-2">
               {{ t('opportunities.stageManager.preparationTitle') || 'Preparation' }}
            </div>
            <ul class="space-y-2 text-sm text-amber-900">
               <li class="flex items-start gap-2">
                  <span class="mt-0.5">•</span>
                  <span>{{
                     t('opportunities.stageManager.preparationItem1') ||
                     'Confirm order details and quantities'
                  }}</span>
               </li>
               <li class="flex items-start gap-2">
                  <span class="mt-0.5">•</span>
                  <span>{{
                     t('opportunities.stageManager.preparationItem2') ||
                     'Check stock and reserve items'
                  }}</span>
               </li>
               <li class="flex items-start gap-2">
                  <span class="mt-0.5">•</span>
                  <span>{{
                     t('opportunities.stageManager.preparationItem3') ||
                     'Prepare packaging and shipping documents'
                  }}</span>
               </li>
            </ul>
         </div>
      </div>

      <!-- Stage Timeline (Optional) -->
      <div v-if="showTimeline" class="pt-6 border-t border-gray-200">
         <div class="space-y-4">
            <div class="flex items-start gap-4">
               <div
                  class="w-8 h-8 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center flex-shrink-0 text-sm font-semibold"
               >
                  ✓
               </div>
               <div>
                  <div class="text-sm font-medium text-gray-900">{{ getStageLabel(stage) }}</div>
                  <div class="text-xs text-gray-500 mt-1">
                     {{ t('opportunities.stageManager.current') }}
                  </div>
               </div>
            </div>

            <div
               v-for="nextStage in getNextStages()"
               :key="nextStage"
               class="flex items-start gap-4"
            >
               <div
                  class="w-8 h-8 rounded-full bg-gray-200 text-gray-400 flex items-center justify-center flex-shrink-0 text-sm font-semibold"
               >
                  →
               </div>
               <div>
                  <div class="text-sm text-gray-600">{{ getStageLabel(nextStage) }}</div>
               </div>
            </div>
         </div>
      </div>

      <!-- Empty State -->
      <div v-if="!stage" class="text-center py-8">
         <div class="text-gray-400 text-sm">{{ t('common.noData') }}</div>
      </div>
   </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n';

interface Props {
   stage?: string;
   status?: string;
   showTimeline?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
   stage: '',
   status: 'OPEN',
   showTimeline: false,
});

const { t } = useI18n();

// Stage definitions with colors and emojis
const stageConfig: Record<
   string,
   { icon: string; description: string; progress: number; color: string; iconBg: string }
> = {
   NEW_LEAD: {
      icon: '🔍',
      description: 'New lead identified',
      progress: 5,
      color: 'text-blue-600',
      iconBg: 'bg-blue-100',
   },
   QUALIFYING: {
      icon: '📋',
      description: 'Evaluating fit and interest',
      progress: 15,
      color: 'text-cyan-600',
      iconBg: 'bg-cyan-100',
   },
   NEEDS_DEFINED: {
      icon: '🎯',
      description: 'Customer needs identified',
      progress: 30,
      color: 'text-purple-600',
      iconBg: 'bg-purple-100',
   },
   RFP_IN_PROGRESS: {
      icon: '📝',
      description: 'RFP/Proposal in progress',
      progress: 50,
      color: 'text-fuchsia-600',
      iconBg: 'bg-fuchsia-100',
   },
   RFQ_IN_PROGRESS: {
      icon: '📝',
      description: 'RFQ/Quote in progress',
      progress: 50,
      color: 'text-fuchsia-600',
      iconBg: 'bg-fuchsia-100',
   },
   OFFER_SENT: {
      icon: '✉️',
      description: 'Offer/Quote sent to customer',
      progress: 60,
      color: 'text-orange-600',
      iconBg: 'bg-orange-100',
   },
   NEGOTIATION: {
      icon: '🤝',
      description: 'Terms and conditions under discussion',
      progress: 70,
      color: 'text-yellow-600',
      iconBg: 'bg-yellow-100',
   },
   COMMITMENT: {
      icon: '✅',
      description: 'Customer committed to purchase',
      progress: 80,
      color: 'text-lime-600',
      iconBg: 'bg-lime-100',
   },
   PREPARATION: {
      icon: '📦',
      description: 'Order preparation before shipping',
      progress: 83,
      color: 'text-amber-600',
      iconBg: 'bg-amber-100',
   },
   DELIVERY_IN_PROGRESS: {
      icon: '🚚',
      description: 'Delivery in progress',
      progress: 85,
      color: 'text-emerald-600',
      iconBg: 'bg-emerald-100',
   },
   ACCEPTED: {
      icon: '📦',
      description: 'Delivery accepted by customer',
      progress: 90,
      color: 'text-teal-600',
      iconBg: 'bg-teal-100',
   },
   INVOICED: {
      icon: '💰',
      description: 'Invoice sent',
      progress: 95,
      color: 'text-green-600',
      iconBg: 'bg-green-100',
   },
   PAID: {
      icon: '✔️',
      description: 'Payment received',
      progress: 99,
      color: 'text-emerald-600',
      iconBg: 'bg-emerald-100',
   },
   CLOSED_WON: {
      icon: '🏆',
      description: 'Opportunity won',
      progress: 100,
      color: 'text-emerald-600',
      iconBg: 'bg-emerald-100',
   },
   CLOSED_LOST: {
      icon: '❌',
      description: 'Opportunity lost',
      progress: 0,
      color: 'text-red-600',
      iconBg: 'bg-red-100',
   },
   ON_HOLD: {
      icon: '⏸️',
      description: 'On hold',
      progress: 50,
      color: 'text-gray-600',
      iconBg: 'bg-gray-100',
   },
};

// Status color mapping
const statusConfig: Record<string, string> = {
   OPEN: 'bg-blue-100 text-blue-700',
   WON: 'bg-emerald-100 text-emerald-700',
   LOST: 'bg-red-100 text-red-700',
   ON_HOLD: 'bg-gray-100 text-gray-700',
};

// Stage order for timeline
const stageOrder = [
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
];

const getStageLabel = (stage: string) => {
   return t(`opportunities.stages.${stage}`) || stage;
};

const getStatusLabel = (status: string) => {
   return t(`opportunities.statuses.${status}`) || status;
};

const getStageDescription = (stage: string) => {
   return stageConfig[stage]?.description || '';
};

const getStageIcon = () => {
   return stageConfig[props.stage]?.icon || '●';
};

const getStageIconClass = () => {
   return stageConfig[props.stage]?.iconBg || 'bg-gray-100';
};

const getStatusClass = (status: string) => {
   return statusConfig[status] || 'bg-gray-100 text-gray-700';
};

const getStageProgress = () => {
   return stageConfig[props.stage]?.progress || 0;
};

const getNextStages = () => {
   if (!props.stage) return [];
   const currentIndex = stageOrder.indexOf(props.stage);
   return stageOrder.slice(currentIndex + 1, currentIndex + 3);
};
</script>

<i18n>
{
  "en": {
    "opportunities": {
      "stageManager": {
        "progress": "Progress",
        "current": "Current stage"
      }
    }
  },
  "fr": {
    "opportunities": {
      "stageManager": {
        "progress": "Progression",
        "current": "Étape actuelle"
      }
    }
  }
}
</i18n>
