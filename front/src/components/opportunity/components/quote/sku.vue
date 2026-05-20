<template>
   <td class="line-sku" style="position: relative">
      <input
         v-model="props.item.line.sku"
         type="text"
         :placeholder="t('opportunities.quoteTable.sku')"
         :readonly="!props.isEditable"
         @keydown.enter.prevent="props.addLineAfter(props.idx)"
         @input="props.handleSkuInput(props.idx, $event)"
         @focus="props.openSkuSuggestions(props.idx)"
         @blur="props.closeSkuSuggestions(props.idx)"
         :class="[
            'text-right',
            props.item.line.sku &&
            props.skuSuggestionStatus[props.idx]?.queried &&
            (!props.skuSuggestions[props.idx] || props.skuSuggestions[props.idx].length === 0)
               ? 'border-orange-300'
               : 'border-gray-300 focus:ring-blue-500',
            ,
         ]"
      />

      <p
         v-if="props.item?.line?.sku"
         style="padding-top: 2px; color: grey; font-size: 10px; text-align: left"
      >
         <a
            class="cursor-pointer hover:underline"
            :href="
               props.item.product?.id
                  ? `/products/${props.item.product.id}`
                  : `/products?refciale=${encodeURIComponent(props.item.line.sku)}&exactMatch=true`
            "
         >
            {{ t('opportunities.quoteTable.show') }}
         </a>
      </p>

      <!--div>
                        debug: is active:{{ activeSkuIndex === idx }} idx: {{ idx }} sug:
                        {{ skuSuggestions[idx] && skuSuggestions[idx].length }}
                     </div-->
      <!-- SKU Suggestions Dropdown -->
      <div
         v-if="
            activeSkuIndex === idx &&
            ((skuSuggestions[idx] && skuSuggestions[idx].length > 0) ||
               props.skuSuggestionStatus[idx]?.loading ||
               props.skuSuggestionStatus[idx]?.queried ||
               props.skuSuggestionErrors[idx])
         "
         class="absolute z-10 min-w-[320px] w-max max-w-130 top-full mt-1 bg-white border border-gray-300 rounded shadow-lg"
      >
         <template v-if="skuSuggestions[idx] && skuSuggestions[idx].length > 0">
            <div
               v-for="(suggestion, sidx) in skuSuggestions[idx]"
               :key="`${idx}-${sidx}`"
               @mousedown.prevent
               @click="selectSkuSuggestion(idx, suggestion)"
               class="px-2 py-1 cursor-pointer hover:bg-blue-50 border-b last:border-b-0"
            >
               <div class="text-xs font-medium">{{ suggestion.sku }} {{ suggestion.name }}</div>
               <div class="text-xs text-gray-600 flex items-center gap-2">
                  <span class="shrink-0">{{ suggestion.brand.name }}</span>
                  <span
                     v-if="suggestion.description"
                     class="text-gray-500 truncate"
                     style="max-width: 220px"
                  >
                     {{ suggestion.description }}
                  </span>
                  <span class="text-gray-500 ml-auto shrink-0">
                     {{
                        formatCurrency(Number(suggestion.price) || 0, props.quoteDocument?.currency)
                     }}
                  </span>
               </div>
            </div>
         </template>
         <div v-else-if="props.skuSuggestionErrors[idx]" class="px-2 py-1 text-xs text-red-600">
            {{ props.skuSuggestionErrors[idx] }}
         </div>
         <div
            v-else-if="
               props.skuSuggestionStatus[idx]?.queried && !props.skuSuggestionStatus[idx]?.loading
            "
            class="px-2 py-1 text-xs text-gray-500"
         >
            {{ t('opportunities.noMatches') }}
         </div>
         <div
            v-else-if="props.skuSuggestionStatus[idx]?.loading"
            class="px-2 py-1 text-xs text-gray-500"
         >
            {{ t('opportunities.searching') }}
         </div>
      </div>
   </td>
</template>

<script setup lang="ts">
import { formatCurrency } from './format.vue';
import { useI18n } from '../../../../i18n/useI18n';

const { t } = useI18n();

const props = defineProps<{
   quoteDocument: any;
   getProductBySku: (sku: string) => any;
   isEditable: boolean;
   skuSuggestionStatus: any;
   skuSuggestionErrors: any;
   item: any;
   idx: number;
   skuSuggestions: any;
   activeSkuIndex: number | null;
   addLineAfter: (idx: number) => void;
   handleSkuInput: (idx: number, event: any) => void;
   openSkuSuggestions: (idx: number) => void;
   closeSkuSuggestions: (idx: number) => void;
   selectSkuSuggestion: (idx: number, suggestion: any) => void;
}>();
</script>
