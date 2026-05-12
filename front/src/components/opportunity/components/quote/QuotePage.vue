<template>
   <div class="opportunity-page">
      <OpportunityHeader :opportunityId="opportunityId" activeTab="quote" />
      <Quote />
   </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRoute } from 'vue-router';
import Quote from './Quote.vue';
import OpportunityHeader from '../../OpportunityHeader.vue';

const route = useRoute();
const opportunityId = computed(() => (route.params.id as string) || '');
</script>
