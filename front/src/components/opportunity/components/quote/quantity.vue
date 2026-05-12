<style>
.line-quantity {
   text-align: right;
   width: 60px;
   max-width: 60px;
}
.line-quantity input {
   padding-right: 0.25rem;
   text-align: right;
   width: 100%;
}
</style>
<template>
   <td class="line-quantity" style="">
      <input
         v-model="props.item.line.quantity"
         @keydown.enter.prevent="props.addLineAfter(props.idx)"
         @input="props.markFieldChanged(props.idx, 'quantity')"
         type="text"
         inputmode="decimal"
         :readonly="!props.isEditable"
         :class="{ 'text-red-700': minQuantity(props.item) > props.item.line.quantity }"
      />
      <p style="font-size: 10px; color: grey; padding-top: 2px; padding-right: 4px">
         min: {{ minQuantity(props.item) }}
      </p>
   </td>
   <td
      v-if="!props.hideValidation"
      class="line-quantity-verified px-1 py-1 align-top flex items-center justify-center"
      style=""
   >
      <input
         v-model="props.item.line.is_quantity_verified"
         type="checkbox"
         :class="[
            'w-4 h-4 cursor-pointer transition-colors',
            {
               'save-flash': false,
            },
         ]"
         @change="props.handleVerificationChange(props.idx, 'is_quantity_verified')"
      />
   </td>
</template>
<script setup lang="ts">
import { minQuantity } from './format.vue';
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
