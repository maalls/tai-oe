<template>
   <td class="line-tax-rate number">
      <input
         v-model="item.line.tax_rate"
         style="text-align: right"
         @blur="
            () => {
               props.markFieldChanged(props.idx, 'tax_rate');
            }
         "
         @keydown.enter.prevent="props.addLineAfter(props.idx)"
         type="text"
         inputmode="decimal"
         :readonly="!props.isEditable"
         :class="['w-full']"
      />
   </td>
</template>
<script lang="ts" setup>
const props = defineProps<{
   item: any;
   idx: number;
   isEditable: boolean;
   markFieldChanged: (idx: number, field: string) => void;
   addLineAfter: (idx: number) => void;
}>();
</script>
