<template>
   <div class="opportunity-page">
      <OpportunityHeader ref="headerRef" :opportunityId="opportunityId" activeTab="pipeline" />

      <div class="opportunity-page-section grid grid-cols-1 lg:grid-cols-4 gap-6">
         <!-- Stage Manager -->
         <StageManager :opportunityId="opportunityId" @stageUpdated="handleStageUpdated" />

         <!-- Stage-aware content -->
         <div class="lg:col-span-3">
            <PipelineStagePanel
               :stage="opportunity?.stage"
               :opportunity="opportunity"
               :account="account"
               :contacts="contacts"
               :isLoading="isLoading"
               @stageUpdated="handleStageUpdated"
            />
         </div>
      </div>
   </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { getAccount } from '../../../../api/account';
import { listContacts } from '../../../../api/contact';
import { getOpportunitySummary } from '../../../../api/opportunity';
import OpportunityHeader from '../../OpportunityHeader.vue';
import StageManager from './components/StageManager.vue';
import PipelineStagePanel from './PipelineStagePanel.vue';

const route = useRoute();
const opportunityId = route.params.id as string;

const isLoading = ref(true);
const opportunity = ref<any>(null);
const account = ref<any>(null);
const contacts = ref<any[]>([]);
const headerRef = ref<any>(null);

const loadOpportunity = async () => {
   try {
      const opportunityData = (await getOpportunitySummary(opportunityId)) as any;

      if (opportunityData) {
         opportunity.value = opportunityData;
         account.value = null;

         if (opportunityData.account_id) {
            try {
               account.value = await getAccount(opportunityData.account_id);
            } catch (accountError) {
               console.error('[PipelinePage] Error loading account:', accountError);
            }
         }

         // Load contacts for this account
         if (opportunityData.account_id) {
            const contactsData = await listContacts();
            contacts.value = contactsData
               .filter((contact) => contact.account_id === opportunityData.account_id)
               .sort((a, b) => (a.name || '').localeCompare(b.name || ''));
         } else {
            contacts.value = [];
         }
      }
   } catch (error) {
      console.error('[PipelinePage] Error loading opportunity:', error);
   }
};

const handleStageUpdated = async () => {
   // Reload opportunity to reflect changes
   await loadOpportunity();

   // Refresh header to show updated stage
   if (headerRef.value?.refreshOpportunity) {
      await headerRef.value.refreshOpportunity();
   }
};

onMounted(async () => {
   isLoading.value = true;
   await loadOpportunity();
   isLoading.value = false;
});
</script>
