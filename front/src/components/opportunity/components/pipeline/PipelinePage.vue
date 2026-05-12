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
import { supabase } from '../../../../lib/supabase';
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
      const { data, error } = await supabase
         .from('opportunity')
         .select(
            'id, name, stage, status, currency, amount_estimated, probability, expected_close_date, created_at, updated_at, account_id, account:account_id(id, name)'
         )
         .eq('id', opportunityId)
         .single();

      if (error) throw error;

      if (data) {
         const opportunityData = data as any;
         opportunity.value = opportunityData;
         account.value = opportunityData.account;

         // Load contacts for this account
         if (opportunityData.account_id) {
            const { data: contactsData, error: contactsError } = await supabase
               .from('contact')
               .select('id, name, email, phone, role_title')
               .eq('account_id', opportunityData.account_id)
               .order('name', { ascending: true });

            if (!contactsError) {
               contacts.value = contactsData || [];
            }
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
