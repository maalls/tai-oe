<template>
   <td class="line-total number ttc">
      {{ formatNumber(totalPriceWithTax(props.item)) }}
   </td>
</template>
<script lang="ts" setup>
import { totalPriceWithTax, formatNumber } from './format.vue';
const props = defineProps<{
   item: any;
   currency: string;
}>();
</script>
