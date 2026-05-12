<template>
   <td class="line-total-without-tax number" style="">
      <div class="text-xs text-gray-800">
         {{ formatNumber(priceWithoutTax(props.item)) }}
      </div>
   </td>
</template>
<script lang="ts" setup>
import { priceWithoutTax, formatNumber } from './format.vue';
const props = defineProps<{
   item: any;
}>();
</script>
