<template>
   <td class="align-top line-rank" style="min-width: 30px">
      <button
         type="button"
         style="margin: 0px; padding: 1px"
         class="disabled:text-gray-300"
         :disabled="!props.isEditable || idx === 0"
         @click="props.moveLineUp(idx)"
         :title="t('opportunities.moveUp')"
      >
         ▲
      </button>

      <button
         type="button"
         :disabled="!props.isEditable || idx === props.quoteDocument.document_line.length - 1"
         @click="props.moveLineDown(idx)"
         :title="t('opportunities.moveDown')"
      >
         ▼
      </button>
   </td>
</template>

<script setup lang="ts">
import { useI18n } from '../../../../i18n/useI18n';

const { t } = useI18n();

const props = defineProps<{
   rank: number;
   idx: number;
   quoteDocument: any;
   isEditable: boolean;
   moveLineUp: (idx: number) => void;
   moveLineDown: (idx: number) => void;
}>();
</script>
