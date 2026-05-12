<template>
   <tbody class="text-xs quote-number-table" v-if="props.quoteDocument">
      <tr
         v-for="(item, idx) in lines"
         :key="item.line.id || item.line._clientKey || `line-${idx}`"
         class="line"
         style="border-top: 1px solid #dddddd; font-size: 11px"
      >
         <rank
            :idx="Number(idx)"
            :rank="Number(idx) + 1"
            :quoteDocument="props.quoteDocument"
            :isEditable="isEditable"
            :moveLineUp="moveLineUp"
            :moveLineDown="moveLineDown"
         />
         <brand
            :ref="(el) => setBrandInputRef(el, Number(idx))"
            :item="item"
            :idx="Number(idx)"
            :isEditable="isEditable"
            :markFieldChanged="props.markFieldChanged"
            :addLineAfter="addLineAfter"
            :handleRemoveOnEmpty="handleRemoveOnEmpty"
         />
         <sku
            :item="item"
            :idx="Number(idx)"
            :active-sku-index="activeSkuIndex"
            :quoteDocument="props.quoteDocument"
            :getProductBySku="props.getProductBySku"
            :isEditable="isEditable"
            :skuSuggestionStatus="skuSuggestionStatus"
            :skuSuggestions="skuSuggestions"
            :skuSuggestionErrors="skuSuggestionErrors"
            :addLineAfter="addLineAfter"
            :handleSkuInput="handleSkuInput"
            :openSkuSuggestions="openSkuSuggestions"
            :closeSkuSuggestions="closeSkuSuggestions"
            :selectSkuSuggestion="selectSkuSuggestion"
         />

         <description
            :item="item"
            :idx="Number(idx)"
            :isEditable="isEditable"
            :markFieldChanged="props.markFieldChanged"
            :addLineAfter="addLineAfter"
         />
         <td class="text-right">
            {{ formatNumber(item.product?.price || 0) }}
         </td>
         <family
            :item="item"
            :idx="Number(idx)"
            :isEditable="isEditable"
            :markFieldChanged="props.markFieldChanged"
            :addLineAfter="addLineAfter"
         />
         <purchasedprice
            :idx="Number(idx)"
            :item="item"
            :isEditable="isEditable"
            :markFieldChanged="props.markFieldChanged"
            :addLineAfter="addLineAfter"
            :hideValidation="props.hideValidation"
            :handleVerificationChange="handleVerificationChange"
         />
         <!--td class="text-right">{{ formatNumber(item.best_family?.minimum_margin || 0) }}%</td>
         <target_margin
            :idx="idx"
            :item="item"
            :isEditable="isEditable"
            :markFieldChanged="props.markFieldChanged"
            :addLineAfter="addLineAfter"
            :quoteDocument="props.quoteDocument"
            :parseNumberInput="parseNumberInput"
         /-->

         <!--td class="line-price px-1 py-1 align-top text-right" style="min-width: 80px">
            {{ formatNumber(targetUnitPrice(item)) }}
         </td>
         <td class="text-right">{{ formatNumber(maxDiscount(item)) }}%</td>
         <td class="text-right">{{ formatNumber(targetDiscount(item)) }}%</td-->

         <td
            v-if="!props.hideValidation"
            class="line-ref-verified px-1 py-2 align-top flex items-center justify-center"
            style=""
         >
            <input
               v-model="item.line.is_ref_verified"
               type="checkbox"
               :class="['w-4 h-4 cursor-pointer transition-colors', ,]"
               @change="handleVerificationChange(Number(idx), 'is_ref_verified')"
            />
         </td>

         <td class="marge text-right">
            <span :class="{ 'text-red-600': minMargin(item) > targetMargin(item) }">{{
               formatNumber(marginAmount(item))
            }}</span>
         </td>
         <td class="marge-percent text-right">
            <p>{{ formatNumber(marginPercent(item)) }}</p>
            <p
               :title="
                  minMargin(item) <= targetMargin(item)
                     ? t('opportunities.minimumAndTargetMargin')
                     : t('opportunities.minimumMarginAboveTarget')
               "
               style="font-size: 10px; padding-top: 2px"
               class="text-right"
               :class="{
                  'text-red-600': minMargin(item) > targetMargin(item),
                  'text-gray-600': minMargin(item) <= targetMargin(item),
               }"
            >
               [<a
                  class="cursor-pointer hover:underline"
                  @click="applySuggestedDiscount(Number(idx), maxDiscount(item))"
               >
                  {{ minMargin(item) }}%</a
               >,
               <a
                  class="cursor-pointer hover:underline"
                  @click="applySuggestedDiscount(Number(idx), targetDiscount(item))"
               >
                  {{ targetMargin(item) }}%</a
               >]
            </p>
         </td>

         <td style="min-width: 90px; width: 90px" class="discount line-discount number text-right">
            <input
               :value="item.line.client_discount_rate ?? ''"
               style="text-align: right"
               type="text"
               inputmode="decimal"
               :placeholder="t('opportunities.discountPlaceholder')"
               :readonly="!isEditable"
               @blur="
                  (e) => {
                     const val = parseNumberInput((e.target as HTMLInputElement).value);
                     item.line.client_discount_rate = val;
                     props.markFieldChanged(Number(idx), 'client_discount_rate');
                  }
               "
               :class="{ 'text-red-600': item.line.client_discount_rate < 0, 'w-full ': true }"
            />
            <p style="padding-top: 2px; color: grey; font-size: 10px; text-align: right">
               [<a
                  class="cursor-pointer hover:underline"
                  @click="applySuggestedDiscount(Number(idx), targetDiscount(item))"
               >
                  {{ targetDiscount(item).toFixed(1) }}%
               </a>
               ,
               <a
                  class="cursor-pointer hover:underline"
                  @click="applySuggestedDiscount(Number(idx), maxDiscount(item))"
               >
                  {{ maxDiscount(item).toFixed(1) }}%</a
               >]
            </p>
         </td>

         <discounted_price :item="item" />

         <quantity
            :idx="Number(idx)"
            :item="item"
            :isEditable="isEditable"
            :markFieldChanged="props.markFieldChanged"
            :addLineAfter="addLineAfter"
            :hideValidation="props.hideValidation"
            :handleVerificationChange="handleVerificationChange"
         />

         <!--unit
            :idx="idx"
            :item="item"
            :isEditable="isEditable"
            :markFieldChanged="props.markFieldChanged"
            :addLineAfter="addLineAfter"
         /-->

         <!--td class="total-cost text-right">
            {{ formatNumber(totalCost(item)) }}
         </td-->
         <!--td class="marge text-right">
            {{ formatNumber(totalMarginAmount(item)) }}
         </td-->
         <td style="min-width: 120px; width: 120px" class="ht text-right">
            {{ formatNumber(totalPriceWithoutTax(item)) }}
         </td>

         <!--tax
            :item="item"
            :idx="idx"
            :isEditable="isEditable"
            :markFieldChanged="props.markFieldChanged"
            :addLineAfter="addLineAfter"
         />
         <price_with_tax :item="item" :currency="props.quoteDocument.currency" /-->
      </tr>
      <tr style="font-weight: bold">
         <td colspan="11"></td>
         <td class="text-right py-1 px-1">{{ t('opportunities.quoteTable.totalExclTax') }}</td>
         <td class="text-right py-1 px-1">{{ formatNumber(tableTotals.totalExclTax) }}</td>
      </tr>
      <tr style="font-weight: bold">
         <td colspan="11"></td>
         <td class="text-right py-1 px-1">{{ t('opportunities.quoteTable.tax') }}</td>
         <td class="text-right py-1 px-1">{{ formatNumber(tableTotals.totalTax) }}</td>
      </tr>
      <tr style="font-weight: bold">
         <td colspan="11"></td>
         <td class="text-right py-1 px-1">{{ t('opportunities.quoteTable.totalInclTax') }}</td>
         <td class="text-right py-1 px-1">
            {{ formatNumber(tableTotals.totalInclTax) }}
         </td>
      </tr>
      <tr style="font-weight: bold; color: blue; font-size: 14px">
         <td colspan="10"></td>
         <td colspan="2" class="text-right py-1 px-1">
            {{ t('opportunities.quoteTable.marginPercent') }}
         </td>
         <td class="text-right py-1 px-1">{{ formatNumber(quoteGrandTotalMarginPercent) }}%</td>
      </tr>
   </tbody>
</template>

<script setup lang="ts">
import { searchProductBySku } from '../../../../composables/useSuggestionSearch';
import { nextTick, ref, computed, watch } from 'vue';
import { useI18n } from '../../../../i18n/useI18n';
import {
   totalPriceWithoutTax,
   marginAmount,
   grandTotalCost,
   grandTotalMargin,
   formatNumber,
   marginPercent,
   targetDiscount,
   maxDiscount,
   targetMargin,
   minMargin,
} from './format.vue';
import sku from './sku.vue';
import rank from './rank.vue';
import quantity from './quantity.vue';
import Brand from './brand.vue';
//import unit from './unit.vue';
import purchasedprice from './purchasedprice.vue';
import family from './family.vue';
import description from './description.vue';
import discounted_price from './discounted_price.vue';

const { t } = useI18n();

const skuSuggestionStatus = ref<Record<number, { loading: boolean; queried: boolean }>>({});
const skuSuggestions = ref<Record<number, any[]>>({});
const skuSuggestionErrors = ref<Record<number, string>>({});
const skuSearchTimeout = ref<Record<number, ReturnType<typeof setTimeout>>>({});
const activeSkuIndex = ref<number | null>(null);
const discountFamilies = ref<Record<number, any | null>>({});
const brandInputRefs = ref<Array<{ focus?: () => void } | null>>([]);
const pendingBrandFocusIndex = ref<number | null>(null);
const pendingBrandFocusTimer = ref<ReturnType<typeof setTimeout> | null>(null);

const props = defineProps<{
   hideValidation: boolean;
   quoteDocument: any | null;
   getProductBySku: (sku: string) => any;
   getLineDiscount: (product: any) => any;
   markFieldChanged: (idx: number | null, fieldName: string) => void;
   isEditable: boolean;
}>();

const lines = computed(() => {
   if (!props.quoteDocument) return [];
   return props.quoteDocument.document_line.map((line: any) => ({
      line,
      product: props.getProductBySku(line.sku),
      best_family: props.getLineDiscount(props.getProductBySku(line.sku)),
   }));
});

const quoteGrandTotalMarginPercent = computed(() => {
   const totalExclTax = tableTotals.value.totalExclTax;
   if (!Number.isFinite(totalExclTax) || totalExclTax === 0) return 0;
   const totalMargin = grandTotalMargin(lines.value);
   if (!Number.isFinite(totalMargin)) return 0;
   return (totalMargin / totalExclTax) * 100;
});

const tableTotals = computed(() => {
   let totalExclTax = 0;
   let totalTax = 0;

   for (const item of lines.value) {
      const lineExclTax = Number(totalPriceWithoutTax(item)) || 0;
      const taxRate = (Number(item?.line?.tax_rate) || 0) / 100;
      totalExclTax += lineExclTax;
      totalTax += lineExclTax * taxRate;
   }

   return {
      totalExclTax,
      totalTax,
      totalInclTax: totalExclTax + totalTax,
   };
});

const parseNumberInput = (raw: string): number => {
   if (!raw) return 0;
   const normalized = raw.replace(/\s/g, '').replace(',', '.');
   const n = Number.parseFloat(normalized);
   return Number.isFinite(n) ? n : 0;
};

const applySuggestedDiscount = (idx: number, value: number) => {
   if (!props.isEditable || !props.quoteDocument?.document_line?.[idx]) return;
   const line = props.quoteDocument.document_line[idx];
   line.client_discount_rate = Number.isFinite(value) ? Math.round(value * 1000) / 1000 : 0;
   props.markFieldChanged(idx, 'client_discount_rate');
};

const handleVerificationChange = (idx: number, fieldName?: string) => {
   const field = fieldName || 'is_ref_verified';
   props.markFieldChanged(idx, field);
};

const setBrandInputRef = (el: unknown, idx: number) => {
   if (
      el &&
      typeof el === 'object' &&
      'focus' in el &&
      typeof (el as { focus?: () => void }).focus === 'function'
   ) {
      brandInputRefs.value[idx] = el as { focus: () => void };
      return;
   }
   brandInputRefs.value[idx] = null;
};

const focusBrandInput = (idx: number) => {
   brandInputRefs.value[idx]?.focus?.();
};

const requestBrandFocus = (idx: number) => {
   pendingBrandFocusIndex.value = idx;
   if (pendingBrandFocusTimer.value) {
      clearTimeout(pendingBrandFocusTimer.value);
   }

   nextTick(() => {
      focusBrandInput(idx);
   });

   pendingBrandFocusTimer.value = setTimeout(() => {
      pendingBrandFocusIndex.value = null;
      pendingBrandFocusTimer.value = null;
   }, 1200);
};

const createEmptyLine = () => ({
   _clientKey:
      typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function'
         ? crypto.randomUUID()
         : `line-${Date.now()}-${Math.random().toString(16).slice(2)}`,
   description: '',
   quantity: 1,
   price: 0,
   tax_rate: 20,
   unit: 'U',
   brand: '',
   sku: '',
   family_codes: [],
   is_ref_verified: false,
   is_quantity_verified: false,
   is_price_verified: false,
});

const removeLine = (idx: number, focusPrev = true) => {
   if (!props.quoteDocument) return;
   const nextProducts = props.quoteDocument.document_line.filter(
      (_line: any, i: number) => i !== idx
   );
   props.quoteDocument.document_line = nextProducts;
   props.markFieldChanged(null, 'document_line');
   nextTick(() => {
      if (nextProducts.length === 0) return;
      const targetIndex = focusPrev ? Math.max(0, idx - 1) : Math.min(idx, nextProducts.length - 1);
      requestBrandFocus(targetIndex);
   });
};

const moveLineUp = (idx: number) => {
   if (!props.isEditable || !props.quoteDocument || idx <= 0) return;
   const products = [...props.quoteDocument.document_line];
   [products[idx - 1], products[idx]] = [products[idx], products[idx - 1]];
   props.quoteDocument.document_line = products;
   props.markFieldChanged(null, 'document_line');
   nextTick(() => {
      requestBrandFocus(idx - 1);
   });
};

const moveLineDown = (idx: number) => {
   if (
      !props.isEditable ||
      !props.quoteDocument ||
      idx >= props.quoteDocument.document_line.length - 1
   )
      return;
   const products = [...props.quoteDocument.document_line];
   [products[idx + 1], products[idx]] = [products[idx], products[idx + 1]];
   props.quoteDocument.document_line = products;
   props.markFieldChanged(null, 'document_line');
   nextTick(() => {
      requestBrandFocus(idx + 1);
   });
};

const handleRemoveOnEmpty = (event: KeyboardEvent, value: string, idx: number) => {
   if (!value || value.length === 0) {
      event.preventDefault();
      removeLine(idx, true);
   }
};

const addLineAfter = (idx: number) => {
   if (!props.isEditable || !props.quoteDocument) return;
   const products = [...props.quoteDocument.document_line];
   products.splice(idx + 1, 0, createEmptyLine());
   props.quoteDocument.document_line = products;
   props.markFieldChanged(null, 'document_line');
   nextTick(() => {
      requestBrandFocus(idx + 1);
   });
};

const appendLineAndFocusBrand = () => {
   if (!props.isEditable || !props.quoteDocument) return;
   const products = [...props.quoteDocument.document_line, createEmptyLine()];
   props.quoteDocument.document_line = products;
   props.markFieldChanged(null, 'document_line');
   nextTick(() => {
      requestBrandFocus(products.length - 1);
   });
};

watch(
   () => props.quoteDocument?.document_line,
   () => {
      const idx = pendingBrandFocusIndex.value;
      if (idx === null) return;
      nextTick(() => {
         focusBrandInput(idx);
      });
   }
);

defineExpose({
   appendLineAndFocusBrand,
});

const performSkuSearch = (idx: number, sku: string, markChanged: boolean) => {
   // Clear previous timeout
   if (skuSearchTimeout.value[idx]) {
      clearTimeout(skuSearchTimeout.value[idx]);
   }

   if (markChanged) {
      props.markFieldChanged(idx, 'sku');
   }

   skuSuggestionErrors.value[idx] = '';

   // Clear suggestions if SKU is empty
   if (!sku || sku.length < 2) {
      skuSuggestions.value[idx] = [];
      skuSuggestionStatus.value[idx] = { loading: false, queried: false };
      discountFamilies.value[idx] = null;
      return;
   }

   skuSuggestionStatus.value[idx] = { loading: true, queried: true };

   // Debounce search
   skuSearchTimeout.value[idx] = setTimeout(async () => {
      searchProductBySku(
         sku,
         (products, error) => {
            skuSuggestions.value[idx] = products;
            if (error) {
               skuSuggestionErrors.value[idx] = error;
            }
            skuSuggestionStatus.value[idx] = { loading: false, queried: true };
         },
         (loading) => {
            if (!loading) {
               skuSuggestionStatus.value[idx] = { loading: false, queried: true };
            }
         }
      );
   }, 300);
};

const handleSkuInput = async (idx: number, event: Event) => {
   const target = event.target as HTMLInputElement;
   const sku = target.value.trim();
   performSkuSearch(idx, sku, true);
};

const openSkuSuggestions = (idx: number) => {
   activeSkuIndex.value = idx;
   const sku = props.quoteDocument?.document_line?.[idx]?.sku?.trim() || '';
   performSkuSearch(idx, sku, false);
};

const closeSkuSuggestions = (idx: number) => {
   window.setTimeout(() => {
      if (activeSkuIndex.value === idx) {
         activeSkuIndex.value = null;
      }
   }, 150);
};

const selectSkuSuggestion = (idx: number, suggestion: any) => {
   if (!props.quoteDocument || !props.quoteDocument.document_line[idx]) return;

   console.log(`[selectSkuSuggestion] Selected suggestion for index ${idx}:`, suggestion);
   const line = props.quoteDocument.document_line[idx];
   line.sku = suggestion.sku;
   line.brand = suggestion.brand.name;
   line.description = suggestion.name || line.description;
   line.price = Number(suggestion.price) || line.price || 0;
   //fetchDiscountFamily(suggestion.sku, suggestion.brand, idx);

   // Clear suggestions
   skuSuggestions.value[idx] = [];
   skuSuggestionErrors.value[idx] = '';
   skuSuggestionStatus.value[idx] = { loading: false, queried: false };
   activeSkuIndex.value = null;

   // Mark fields as changed
   props.markFieldChanged(idx, 'sku');
};
</script>

<style scoped>
.quote-number-table {
   font-variant-numeric: tabular-nums lining-nums;
   font-feature-settings:
      'tnum' 1,
      'lnum' 1;
}
</style>
