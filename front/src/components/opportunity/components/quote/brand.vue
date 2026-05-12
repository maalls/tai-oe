<template>
   <td class="line-brand">
      <input
         ref="brandInputRef"
         v-model="item.line.brand"
         type="text"
         :placeholder="t('opportunities.quoteTable.brand')"
         :readonly="!isEditable"
         @keydown.enter.prevent="props.addLineAfter(idx)"
         @input="props.markFieldChanged(idx, 'brand')"
         :class="[]"
         @keydown.delete="props.handleRemoveOnEmpty($event, item.line.brand, idx)"
         @keydown.backspace="props.handleRemoveOnEmpty($event, item.line.brand, idx)"
      />

      <p style="padding-top: 2px; color: grey; font-size: 10px; text-align: right">
         <RouterLink
            v-if="item.product?.brand?.id"
            :to="`/vendors/brand/${item.product.brand.id}?edit=true`"
         >
            {{ item.product?.brand?.minimum_margin || 'n/a' }}% -
            {{ item.product?.brand?.target_margin || 'n/a' }}%
         </RouterLink>
      </p>
   </td>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useI18n } from '../../../../i18n/useI18n';

const { t } = useI18n();
const brandInputRef = ref<HTMLInputElement | null>(null);

const props = defineProps<{
   idx: number;
   item: any;
   isEditable: boolean;
   markFieldChanged: (idx: number, field: string) => void;
   addLineAfter: (idx: number) => void;
   handleRemoveOnEmpty: any;
}>();

defineExpose({
   focus: () => {
      brandInputRef.value?.focus();
   },
});
</script>
