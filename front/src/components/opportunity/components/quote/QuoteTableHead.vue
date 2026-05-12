<style scoped>
th.head-brand,
.line-brand input {
   width: 80px;
}
th.head-unit {
   text-align: right;
}

th.total-without-tax {
   text-align: right;
}
th.head-tax {
   text-align: right;
}
th.head-total {
   text-align: right;
   width: 120px;
   min-width: 120px;
}
th.head-marge {
   width: 80px;
   min-width: 80px;
   text-align: right;
}
th.head-margin-percent {
   text-align: right;
   width: 80px;
   min-width: 80px;
}
th.head-remise {
   text-align: right;
   width: 120px;
   min-width: 120px;
}
</style>
<template>
   <thead class="bg-gray-100 text-gray-700">
      <tr class="text-xs">
         <th class="px-1 py-1"></th>
         <th class="head-brand px-1 py-1 text-left">{{ t('opportunities.quoteTable.brand') }}</th>
         <th class="head-sku px-1 py-1 text-left">{{ t('opportunities.quoteTable.sku') }}</th>
         <th class="head-description px-1 py-1 text-left">
            {{ t('opportunities.quoteTable.description') }}
         </th>
         <th class="head-ref px-1 py-1 text-left">{{ t('opportunities.quoteTable.listPrice') }}</th>
         <th class="head-ref px-1 py-1 text-right">
            {{ t('opportunities.quoteTable.supplierDiscount') }}
         </th>
         <th class="head-cost px-1 py-1 text-right w-30">
            {{ t('opportunities.quoteTable.purchasedPrice') }}
         </th>
         <!--th class="text-right">Minimum Margin</th>
         <th class="text-right">Target Margin</th-->

         <th
            v-if="!props.hideValidation"
            class="px-1 py-1 flex items-center justify-center relative"
            style=""
         >
            <button
               type="button"
               class="flex items-center gap-1 text-xs text-gray-700 hover:text-gray-900"
               @click.stop="toggleVerificationMenu('is_price_verified')"
            >
               ✓
               <svg class="w-3 h-3" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                  <path
                     fill-rule="evenodd"
                     d="M5.23 7.21a.75.75 0 011.06.02L10 10.94l3.71-3.71a.75.75 0 111.06 1.06l-4.24 4.25a.75.75 0 01-1.06 0L5.21 8.29a.75.75 0 01.02-1.08z"
                     clip-rule="evenodd"
                  />
               </svg>
            </button>
            <div
               v-if="verificationMenuOpen === 'is_price_verified'"
               class="absolute top-full mt-1 z-10 bg-white border border-gray-200 rounded shadow text-xs min-w-[110px]"
            >
               <button
                  type="button"
                  class="block w-full text-left px-2 py-1 hover:bg-gray-100"
                  @click="setAllVerification('is_price_verified', true)"
               >
                  {{ t('opportunities.quoteTable.checkAll') }}
               </button>
               <button
                  type="button"
                  class="block w-full text-left px-2 py-1 hover:bg-gray-100"
                  @click="setAllVerification('is_price_verified', false)"
               >
                  {{ t('opportunities.quoteTable.uncheckAll') }}
               </button>
            </div>
         </th>

         <th
            v-if="!props.hideValidation"
            class="px-1 py-1 flex items-center justify-center relative"
            style=""
         >
            <button
               type="button"
               class="flex items-center gap-1 text-xs text-gray-700 hover:text-gray-900"
               @click.stop="toggleVerificationMenu('is_quantity_verified')"
            >
               ✓
               <svg class="w-3 h-3" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                  <path
                     fill-rule="evenodd"
                     d="M5.23 7.21a.75.75 0 011.06.02L10 10.94l3.71-3.71a.75.75 0 111.06 1.06l-4.24 4.25a.75.75 0 01-1.06 0L5.21 8.29a.75.75 0 01.02-1.08z"
                     clip-rule="evenodd"
                  />
               </svg>
            </button>
            <div
               v-if="verificationMenuOpen === 'is_quantity_verified'"
               class="absolute top-full mt-1 z-10 bg-white border border-gray-200 rounded shadow text-xs min-w-[110px]"
            >
               <button
                  type="button"
                  class="block w-full text-left px-2 py-1 hover:bg-gray-100"
                  @click="setAllVerification('is_quantity_verified', true)"
               >
                  {{ t('opportunities.quoteTable.checkAll') }}
               </button>
               <button
                  type="button"
                  class="block w-full text-left px-2 py-1 hover:bg-gray-100"
                  @click="setAllVerification('is_quantity_verified', false)"
               >
                  {{ t('opportunities.quoteTable.uncheckAll') }}
               </button>
            </div>
         </th>
         <!--th class="head head-unit px-1 py-1 text-left">Target Price</th>
         <th class="head head-cost px-1 py-1 text-right">Maximum Discount</th>
         <th class="head head-unit-total px-1 py-1 text-right">Target Discount</th-->
         <th class="head head-margin head-marge px-1 py-1">
            {{ t('opportunities.quoteTable.margin') }}
         </th>
         <th class="head head-margin head-margin-percent px-1 py-1">
            {{ t('opportunities.quoteTable.marginPercent') }}
         </th>
         <th class="head head-unit-total head-remise px-1 py-1 text-right">
            {{ t('opportunities.quoteTable.discount') }} %
         </th>
         <th class="text-right">{{ t('opportunities.quoteTable.salePrice') }}</th>

         <th class="head head-discount px-1 py-1 text-right">
            {{ t('opportunities.quoteTable.quantity') }}
         </th>
         <!--th class="px-1 py-1 text-right">Unit</th-->
         <th
            v-if="!props.hideValidation"
            class="px-1 py-1 flex items-center justify-center relative"
            style=""
         >
            <button
               type="button"
               class="flex items-center gap-1 text-xs text-gray-700 hover:text-gray-900"
               @click.stop="toggleVerificationMenu('is_ref_verified')"
            >
               ✓
               <svg class="w-3 h-3" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                  <path
                     fill-rule="evenodd"
                     d="M5.23 7.21a.75.75 0 011.06.02L10 10.94l3.71-3.71a.75.75 0 111.06 1.06l-4.24 4.25a.75.75 0 01-1.06 0L5.21 8.29a.75.75 0 01.02-1.08z"
                     clip-rule="evenodd"
                  />
               </svg>
            </button>
            <div
               v-if="verificationMenuOpen === 'is_ref_verified'"
               class="absolute top-full mt-1 z-10 bg-white border border-gray-200 rounded shadow text-xs min-w-[110px]"
            >
               <button
                  type="button"
                  class="block w-full text-left px-2 py-1 hover:bg-gray-100"
                  @click="setAllVerification('is_ref_verified', true)"
               >
                  {{ t('opportunities.quoteTable.checkAll') }}
               </button>
               <button
                  type="button"
                  class="block w-full text-left px-2 py-1 hover:bg-gray-100"
                  @click="setAllVerification('is_ref_verified', false)"
               >
                  {{ t('opportunities.quoteTable.uncheckAll') }}
               </button>
            </div>
         </th>
         <!--th class="head head-cost px-1 py-1">Total Cost</th-->

         <th class="head head-total px-1 py-1">{{ t('opportunities.quoteTable.total') }}</th>

         <!--th class="head head-tax px-1 py-1 w-20">Tax %</th>
         <th class="head head-total px-1 py-1q">Total TTC</th-->
      </tr>
   </thead>
</template>
<script setup lang="ts">
import { ref } from 'vue';
import { useI18n } from '../../../../i18n/useI18n';

const { t } = useI18n();

const props = defineProps<{ hideValidation: boolean }>();
const emit = defineEmits<{
   'set-all-verification': [field: string, value: boolean];
}>();

const verificationMenuOpen = ref<string | null>(null);

const toggleVerificationMenu = (field: string) => {
   verificationMenuOpen.value = verificationMenuOpen.value === field ? null : field;
};

const setAllVerification = (field: string, value: boolean) => {
   emit('set-all-verification', field, value);
   verificationMenuOpen.value = null;
};
</script>
