<template>
   <div v-if="quoteDocument" class="">
      <!--div class="grid grid-cols-2 md:grid-cols-2 gap-3 text-sm">
         title: {{ quoteDocument.title }} <br />line counts:
         {{ quoteDocument.document_line?.length || 0 }}
      </div>
      <div>saving: {{ isSavingDraft }} <br /></div-->

      <div class="ao-document relative border border-gray-200 rounded overflow-visible">
         <table class="min-w-full text-xs">
            <QuoteTableHead
               :hideValidation="props.hideValidation"
               @set-all-verification="setAllVerification"
            />

            <QuoteTableBody
               ref="quoteTableBodyRef"
               :hideValidation="props.hideValidation"
               :quoteDocument="props.quoteDocument"
               :getProductBySku="getProductBySku"
               :getLineDiscount="getLineDiscount"
               :isEditable="isEditable"
               :isSavingDraft="isSavingDraft"
               :flashedFields="flashedFields"
               :pendingSaveFields="pendingSaveFields"
               @field-changed="markFieldChanged"
               :mark-field-changed="markFieldChanged"
            />
         </table>
      </div>
   </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';

import { supabase } from '../../../../lib/supabase';
import QuoteTableHead from './QuoteTableHead.vue';
import QuoteTableBody from './QuoteTableBody.vue';
import { formatNumber, priceWithoutTax } from './format.vue';

const props = defineProps<{
   quoteDocument: any | null;
   isEditable: boolean;
   isSavingDraft: boolean;
   hideValidation?: boolean;
   flashedFields?: Set<string>;
   pendingSaveFields?: Set<string>;
}>();

const emit = defineEmits<{
   save: [];
   'field-changed': [key: string];
}>();

const quoteTableBodyRef = ref<{ appendLineAndFocusBrand?: () => void } | null>(null);

const setAllVerification = (field: string, value: boolean) => {
   console.log(`Setting all verification for ${field} to ${value}`);
   if (!props.quoteDocument?.document_line) return;
   props.quoteDocument.document_line.forEach((line: any, idx: number) => {
      line[field] = value;
      markFieldChanged(idx, field);
   });
};

const getProductBySku = (sku: string) => {
   return productsRef.value[sku];
};

const netPriceFamilyBySku = ref<Record<string, any>>({});

const getLineDiscount = (product: { product_family?: any[] | null }) => {
   const sku = String((product as any)?.sku || '').trim();
   const directNetPriceFamily = sku ? netPriceFamilyBySku.value[sku] : null;
   if (directNetPriceFamily) {
      return directNetPriceFamily;
   }

   const links = Array.isArray(product?.product_family) ? product.product_family : [];
   if (links.length === 0) return null;

   let bestDiscountFamily: any | null = null;
   for (const link of links) {
      const family = link?.family;
      if (!family) continue;

      // Net price always wins over any discount family.
      if ((family.type || '').toLowerCase() === 'net_price') {
         return family;
      }

      if ((family.type || '').toLowerCase() !== 'discount') {
         continue;
      }

      const currentDiscount = Number(family.discount ?? 0);
      const bestDiscount = Number(bestDiscountFamily?.discount ?? -Infinity);
      if (currentDiscount > bestDiscount) {
         bestDiscountFamily = family;
      }
   }

   return bestDiscountFamily;
};
const productsRef = ref<Record<string, any>>({});
const fieldKey = (idx: number | null, field: string) =>
   idx === null ? field : `line:${idx}:${field}`;

const updateLineUnitPrice = (line: any) => {
   const product = getProductBySku(line.sku);
   const best_family = getLineDiscount(product);
   line.unit_price_excl_tax = priceWithoutTax({ line, product, best_family });
};

const updateAllLinePrices = () => {
   if (!props.quoteDocument?.document_line) return;
   props.quoteDocument.document_line.forEach(updateLineUnitPrice);
};

const markFieldChanged = (idx: number | null, field: string) => {
   const key = fieldKey(idx, field);
   console.log(
      'Marking field as changed:',
      key,
      'to value:',
      idx !== null ? props.quoteDocument?.document_line?.[idx]?.[field] : null,
      'Current pending fields:',
      props.pendingSaveFields
   );
   console.log('Emiting field change:', props.flashedFields);
   props.flashedFields?.add(key);

   // Recompute unit_price_excl_tax when price-affecting fields change
   if (idx !== null && (field === 'client_discount_rate' || field === 'sku')) {
      const line = props.quoteDocument?.document_line?.[idx];
      if (line) {
         if (field === 'sku' && line.sku) {
            // Fetch product data for new SKU, then update price
            Promise.all([
               supabase
                  .from('product')
                  .select('*, brand(*), product_family(family(*))')
                  .eq('sku', line.sku)
                  .maybeSingle(),
               supabase
                  .from('family')
                  .select('*')
                  .eq('product_code', line.sku)
                  .ilike('type', 'net_price')
                  .limit(1)
                  .maybeSingle(),
            ]).then(([productResponse, netPriceFamilyResponse]) => {
               const { data, error } = productResponse;
               if (!error && data) {
                  const product = data as any;
                  productsRef.value[product.sku] = product;
               }

               if (!netPriceFamilyResponse.error && netPriceFamilyResponse.data) {
                  netPriceFamilyBySku.value[line.sku] = netPriceFamilyResponse.data;
               } else {
                  delete netPriceFamilyBySku.value[line.sku];
               }

               updateLineUnitPrice(line);
            });
         } else {
            updateLineUnitPrice(line);
         }
      }
   }

   emit('field-changed', key);
};

// Incrementally hydrate product/family cache so table rows do not temporarily lose values.
const initializeDisplays = async () => {
   if (!props.quoteDocument?.document_line) return;

   const skus: string[] = Array.from(
      new Set(
         props.quoteDocument.document_line
            .map((line: any) => String(line?.sku || '').trim())
            .filter((sku: string) => sku.length > 0)
      )
   );

   if (skus.length === 0) {
      updateAllLinePrices();
      return;
   }

   // Keep existing cache entries and only fetch missing SKUs.
   const missingSkus = skus.filter((sku) => !productsRef.value[sku]);
   if (missingSkus.length > 0) {
      const [productResponse, netPriceFamilyResponse] = await Promise.all([
         supabase
            .from('product')
            .select('*, brand(*), product_family(family(*))')
            .in('sku', missingSkus),
         supabase
            .from('family')
            .select('*')
            .in('product_code', missingSkus)
            .ilike('type', 'net_price'),
      ]);

      const { data, error } = productResponse;

      if (error) {
         console.error('Error fetching product:', error);
      } else {
         (data as any[] | null)?.forEach((product: any) => {
            if (product?.sku) {
               productsRef.value[product.sku] = product;
            }
         });
      }

      if (netPriceFamilyResponse.error) {
         console.error('Error fetching net_price families:', netPriceFamilyResponse.error);
      } else {
         (netPriceFamilyResponse.data as any[] | null)?.forEach((family: any) => {
            const sku = String(family?.product_code || '').trim();
            if (sku) {
               netPriceFamilyBySku.value[sku] = family;
            }
         });
      }
   }

   updateAllLinePrices();
};

watch(
   () =>
      props.quoteDocument?.document_line
         ?.map((line: any) => String(line?.sku || '').trim())
         .join('|') || '',
   initializeDisplays,
   { immediate: true }
);

const addLine = () => {
   if (quoteTableBodyRef.value?.appendLineAndFocusBrand) {
      quoteTableBodyRef.value.appendLineAndFocusBrand();
      return;
   }

   if (!props.quoteDocument) return;
   props.quoteDocument.document_line = [
      ...props.quoteDocument.document_line,
      {
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
      },
   ];
   markFieldChanged(null, 'document_line');
};
</script>
