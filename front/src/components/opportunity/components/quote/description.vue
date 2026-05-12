<template>
   <td class="line-description" style="">
      <textarea
         v-model="props.item.line.description"
         rows="1"
         :readonly="!isEditable"
         @keydown.enter.prevent="props.addLineAfter(props.idx)"
         @input="props.markFieldChanged(props.idx, 'description')"
         :class="['']"
      ></textarea>
      <div
         class="flex items-between gap-1 text-gray-500"
         v-if="props.item.product?.name && props.item.product.name != props.item.line.description"
         style="font-size: 10px; width: 100%"
      >
         <!--span>{{ t('opportunities.edited') }}</span>
         <a href="" :title="props.item.product.name" style="color: blue">{{ t('opportunities.restore') }}</a-->
      </div>
   </td>
</template>

<script lang="ts" setup>
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
