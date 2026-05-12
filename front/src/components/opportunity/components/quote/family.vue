<template>
   <td class="text-right pt-2">
      <a
         v-if="props.item.best_family"
         style="margin-right: 2px; margin-top: 2px; padding: 2px; white-space: nowrap"
         :class="{
            'bg-green-100 text-emerald-700': isNetPriceFamily,
            'bg-amber-100 text-gray-700': !isNetPriceFamily,
         }"
         :title="props.item.best_family.name"
         :href="familyHref"
      >
         <span v-if="isNetPriceFamily" style="display: inline-block; margin-top: 1px">
            NET
            {{
               (
                  100 * (props.item.product?.price ? netPriceDiff / props.item.product.price : 0)
               ).toFixed(1)
            }}%
         </span>
         <span v-else style="display: inline-block; margin-top: 1px">
            {{ props.item.best_family.code }} {{ props.item.best_family.discount }}%
         </span>
      </a>
   </td>
</template>

<script setup lang="ts">
import { computed } from 'vue';

const props = defineProps<{
   idx: number;
   item: any;
   isEditable: boolean;
   markFieldChanged: (idx: number, field: string) => void;
}>();

const isNetPriceFamily = computed(
   () => (props.item?.best_family?.type || '').toLowerCase() === 'net_price'
);

const familyHref = computed(() => {
   const family = props.item?.best_family;
   if (!family) return '';

   if (isNetPriceFamily.value) {
      const sku = String(props.item?.product?.sku || family.product_code || '').trim();
      if (!sku) return '';
      return `/vendors/family?tab=net_price&sku=${encodeURIComponent(sku)}`;
   }

   const code = String(family.code || '').trim();
   if (!code) return '';
   return `/vendors/family?code=${encodeURIComponent(code)}`;
});

const netPriceDiff = computed(() => {
   const listPrice = Number(props.item?.product?.price || 0);
   const netPrice = Number(props.item?.best_family?.net_price || 0);
   return listPrice - netPrice;
});
</script>
