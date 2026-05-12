<template>
   <td class="line-unit" style="text-align: right">
      <input
         v-model="item.line.unit"
         style="text-align: right"
         type="text"
         :placeholder="t('opportunities.unitPlaceholder')"
         :readonly="!isEditable"
         @keydown.enter.prevent="addLineAfter(idx)"
         @input="props.markFieldChanged(idx, 'unit')"
         :class="['w-full ']"
      />
   </td>
</template>

<script setup lang="ts">
import { useI18n } from '../../../../i18n/useI18n';

const { t } = useI18n();

const props = defineProps<{
   idx: number;
   item: any;
   isEditable: boolean;
   markFieldChanged: (idx: number, field: string) => void;
   addLineAfter: (idx: number) => void;
}>();
</script>
