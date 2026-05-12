<template>
   <div class="opportunity-page h-full flex flex-col">
      <OpportunityHeader :opportunityId="opportunityId" activeTab="chat" />
      <div
         :class="[
            'flex-1 min-h-0',
            isChatCollapsed ? 'opportunity-page-section-collapsed' : 'opportunity-page-section',
         ]"
      >
         <ChatPanel
            v-model:collapsed="isChatCollapsed"
            :context="{ opportunity_id: opportunityId, section: 'chat' }"
            :placeholder="t('opportunities.askAboutOpportunity')"
            :forceOpen="true"
         />
      </div>
   </div>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router';
import { computed, ref } from 'vue';
import OpportunityHeader from '../../OpportunityHeader.vue';
import ChatPanel from '../../../chat/ChatPanel.vue';
import { useI18n } from '../../../../i18n/useI18n';

const { t } = useI18n();

const route = useRoute();
const opportunityId = computed(() => route.params.id as string);
const isChatCollapsed = ref(false);
</script>
