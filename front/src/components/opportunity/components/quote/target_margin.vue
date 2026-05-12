<template>
   <td class="line-margin-rate text-right">
      <!--input
         style="width: 40px; white-space: nowrap; padding: 0px; margin: 0px; text-align: right"
         v-model="props.item.line.discount_rate"
         @focus=""
         @blur="
            (e) => {
               const val = props.parseNumberInput((e.target as HTMLInputElement).value);
               props.quoteDocument.document_line[idx].price = val;
               props.markFieldChanged(idx, 'discount_rate');
            }
         "
         @keydown.enter.prevent="props.addLineAfter(idx)"
         type="text"
         inputmode="decimal"
         :readonly="!props.isEditable"
         :class="['w-full text-right', ,]"
      /-->
      {{ targetMargin(props.item).toFixed(2) }}%
   </td>
</template>
<script setup lang="ts">
import { targetMargin } from './format.vue';
const props = defineProps<{
   idx: number;
   item: any;
   isEditable: boolean;
   markFieldChanged: (idx: number, field: string) => void;
   addLineAfter: (idx: number) => void;
   quoteDocument: any;
   parseNumberInput: (value: string) => number;
}>();
</script>
