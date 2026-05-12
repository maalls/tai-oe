<template>
   <td
      class="line-cost text-right"
      style="min-width: 40px"
      :title="formatNumber(item.product?.price || 0)"
   >
      <span style=""> {{ formatNumber(purchasedPrice(item)) }}</span>
   </td>
   <td
      v-if="!props.hideValidation"
      class="line-price-verified px-1 py-1 align-top flex items-center justify-center"
      style=""
   >
      <input
         v-model="item.line.is_price_verified"
         type="checkbox"
         :class="['w-4 h-4 cursor-pointer transition-colors', ,]"
         @change="props.handleVerificationChange(idx, 'is_price_verified')"
      />
   </td>
</template>
<script setup lang="ts">
import { purchasedPrice, formatNumber } from './format.vue';
const props = defineProps<{
   idx: number;
   item: any;
   isEditable: boolean;
   markFieldChanged: (idx: number, field: string) => void;
   addLineAfter: (idx: number) => void;
   hideValidation?: boolean;
   handleVerificationChange: (idx: number, field: string) => void;
}>();
</script>
