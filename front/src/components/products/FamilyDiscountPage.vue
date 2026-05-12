<template>
   <div>
      <ProductsSubHeader />
      <div class="p-6 max-w-5xl mx-auto space-y-6">
         <div class="flex items-center justify-between">
            <div>
               <h1 class="text-3xl font-bold text-gray-900">Family Discount</h1>
               <p class="text-sm text-gray-500">Manage the discount lines for this family.</p>
            </div>
            <button type="button" class="text-sm text-gray-600 hover:text-gray-900" @click="goBack">
               Back to Families
            </button>
         </div>

         <div v-if="errorMessage" class="rounded-lg bg-red-50 text-red-700 p-4">
            {{ errorMessage }}
         </div>

         <div class="bg-white rounded-lg border border-gray-200 shadow-sm">
            <div v-if="isLoading" class="p-6 text-gray-500">Loading...</div>
            <div v-else-if="!family" class="p-6 text-gray-500">Family not found.</div>
            <div v-else class="p-6 space-y-4">
               <div>
                  <div class="text-sm text-gray-500">Family</div>
                  <div class="text-lg font-semibold text-gray-900">{{ family.name }}</div>
               </div>
               <div class="grid gap-4 sm:grid-cols-2">
                  <div>
                     <div class="text-xs uppercase tracking-wide text-gray-400">Code</div>
                     <div class="text-sm text-gray-700">{{ family.code || '-' }}</div>
                  </div>
                  <div>
                     <div class="text-xs uppercase tracking-wide text-gray-400">Type</div>
                     <div class="text-sm text-gray-700">{{ family.type }}</div>
                  </div>
                  <div>
                     <div class="text-xs uppercase tracking-wide text-gray-400">Brand</div>
                     <div class="text-sm text-gray-700">{{ family.brand_id }}</div>
                  </div>
               </div>
               <div class="space-y-4">
                  <div class="flex items-center justify-between">
                     <div class="text-sm font-semibold text-gray-900">Discount lines</div>
                     <div class="flex items-center gap-2">
                        <button
                           type="button"
                           class="inline-flex items-center rounded-md border border-gray-300 px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50"
                           :disabled="!documentId"
                           @click="addLine"
                        >
                           Add line
                        </button>
                        <button
                           type="button"
                           class="inline-flex items-center rounded-md bg-gray-900 px-3 py-1.5 text-sm text-white hover:bg-gray-800"
                           :disabled="!documentId || isSaving"
                           @click="saveLines"
                        >
                           {{ isSaving ? 'Saving...' : 'Save' }}
                        </button>
                     </div>
                  </div>

                  <div class="rounded-lg border border-gray-200">
                     <div class="overflow-x-auto">
                        <table class="min-w-full text-sm">
                           <thead class="bg-gray-50 text-gray-600">
                              <tr>
                                 <th class="px-3 py-2 text-left">Pos</th>
                                 <th class="px-3 py-2 text-left">SKU</th>
                                 <th class="px-3 py-2 text-right">Qty</th>
                                 <th class="px-3 py-2 text-left">Unit</th>
                                 <th class="px-3 py-2 text-right">Unit Price</th>
                                 <th class="px-3 py-2 text-right">Discount %</th>
                                 <th class="px-3 py-2 text-right">Line Total</th>
                              </tr>
                           </thead>
                           <tbody class="divide-y divide-gray-200">
                              <tr v-for="line in lines" :key="line.id" class="hover:bg-gray-50">
                                 <td class="px-3 py-2 text-gray-500">{{ line.position }}</td>
                                 <td class="px-3 py-2">
                                    <input
                                       v-model="line.sku"
                                       class="w-full rounded border border-gray-300 px-2 py-1 text-sm"
                                       type="text"
                                       placeholder="SKU"
                                    />
                                 </td>
                                 <td class="px-3 py-2">
                                    <input
                                       v-model.number="line.quantity"
                                       class="w-20 rounded border border-gray-300 px-2 py-1 text-right text-sm"
                                       type="number"
                                       min="0"
                                       step="0.001"
                                    />
                                 </td>
                                 <td class="px-3 py-2">
                                    <input
                                       v-model="line.unit"
                                       class="w-16 rounded border border-gray-300 px-2 py-1 text-sm"
                                       type="text"
                                       placeholder="U"
                                    />
                                 </td>
                                 <td class="px-3 py-2">
                                    <input
                                       v-model.number="line.unit_price_excl_tax"
                                       class="w-24 rounded border border-gray-300 px-2 py-1 text-right text-sm"
                                       type="number"
                                       min="0"
                                       step="0.0001"
                                    />
                                 </td>
                                 <td class="px-3 py-2">
                                    <input
                                       v-model.number="line.discount_rate"
                                       class="w-20 rounded border border-gray-300 px-2 py-1 text-right text-sm"
                                       type="number"
                                       min="0"
                                       max="100"
                                       step="0.01"
                                    />
                                 </td>
                                 <td class="px-3 py-2 text-right text-gray-700">
                                    {{ formatAmount(computeLineTotal(line)) }}
                                 </td>
                              </tr>
                           </tbody>
                        </table>
                     </div>
                     <div
                        v-if="linesError"
                        class="border-t border-gray-200 p-3 text-sm text-red-600"
                     >
                        {{ linesError }}
                     </div>
                     <div
                        v-else-if="!lines.length"
                        class="border-t border-gray-200 p-3 text-sm text-gray-500"
                     >
                        No discount lines yet.
                     </div>
                  </div>
               </div>
            </div>
         </div>
      </div>
   </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import ProductsSubHeader from './ProductsSubHeader.vue';
import { supabase } from '../../lib/supabase';

interface FamilyRecord {
   id: string;
   name: string;
   code: string | null;
   type: string;
   brand_id: string;
}

interface DocumentLineRecord {
   id: string;
   position: number;
   quantity: number;
   unit: string;
   unit_price_excl_tax: number;
   discount_rate: number;
   sku: string | null;
   line_total_excl_tax: number;
   isNew?: boolean;
}

interface NewLineInput {
   sku: string;
   quantity: number;
   unit: string;
   unit_price_excl_tax: number;
   discount_rate: number;
}

interface LineTotalsInput {
   quantity: number;
   unit_price_excl_tax: number;
   discount_rate: number;
}

const route = useRoute();
const router = useRouter();
const family = ref<FamilyRecord | null>(null);
const documentId = ref<string | null>(null);
const lines = ref<DocumentLineRecord[]>([]);
const linesError = ref('');
const isLoading = ref(false);
const isSaving = ref(false);
const errorMessage = ref('');

const newLine = ref<NewLineInput>({
   sku: '',
   quantity: 1,
   unit: 'U',
   unit_price_excl_tax: 0,
   discount_rate: 0,
});

const loadFamily = async () => {
   const familyId = String(route.params.id || '').trim();
   if (!familyId) {
      errorMessage.value = 'Missing family id.';
      return;
   }

   isLoading.value = true;
   errorMessage.value = '';

   try {
      const { data, error } = await supabase
         .from('family')
         .select('id,name,code,type,brand_id')
         .eq('id', familyId)
         .single();

      if (error) throw error;
      family.value = data as FamilyRecord;
      await loadDocument();
      await loadLines();
   } catch (error) {
      errorMessage.value =
         error instanceof Error ? error.message : 'Failed to load family information.';
   } finally {
      isLoading.value = false;
   }
};

const loadDocument = async () => {
   documentId.value = null;
   if (!family.value?.brand_id) return;

   try {
      const { data, error } = await supabase
         .from('document')
         .select('id')
         .eq('type', 'FAMILY_DISCOUNT')
         .eq('external_ref', family.value.brand_id)
         .limit(1);

      if (error) throw error;
      const rows = (data as any[]) || [];
      documentId.value = rows.length > 0 ? String(rows[0].id) : null;
   } catch (error) {
      errorMessage.value =
         error instanceof Error ? error.message : 'Failed to load discount document.';
   }
};

const loadLines = async () => {
   const docId = documentId.value;
   linesError.value = '';
   lines.value = [];

   if (!docId) {
      return;
   }

   try {
      const { data, error } = await supabase
         .from('document_line')
         .select(
            'id,position,quantity,unit,unit_price_excl_tax,discount_rate,sku,line_total_excl_tax'
         )
         .eq('document_id', docId)
         .order('position', { ascending: true });

      if (error) throw error;
      lines.value = (data as DocumentLineRecord[]) || [];
   } catch (error) {
      linesError.value = error instanceof Error ? error.message : 'Failed to load discount lines.';
   }
};

const addLine = () => {
   if (!documentId.value) return;

   const nextPosition = lines.value.length
      ? Math.max(...lines.value.map((line) => line.position)) + 1
      : 1;

   lines.value.push({
      id: `new-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
      position: nextPosition,
      sku: newLine.value.sku?.trim() || null,
      quantity: newLine.value.quantity || 1,
      unit: newLine.value.unit || 'U',
      unit_price_excl_tax: newLine.value.unit_price_excl_tax || 0,
      discount_rate: newLine.value.discount_rate ?? 0,
      line_total_excl_tax: computeLineTotal(newLine.value),
      isNew: true,
   });

   newLine.value = {
      sku: '',
      quantity: 1,
      unit: 'U',
      unit_price_excl_tax: 0,
      discount_rate: 0,
   };
};

const saveLines = async () => {
   if (!documentId.value) return;

   isSaving.value = true;
   linesError.value = '';

   try {
      const docId = documentId.value;
      if (!docId) return;
      const existingLines = lines.value.filter((line) => !line.isNew);
      const newLines = lines.value.filter((line) => line.isNew);

      if (existingLines.length) {
         const updates = existingLines.map((line) => ({
            id: line.id,
            document_id: docId,
            position: line.position,
            description: line.sku?.trim() || 'Discount line',
            sku: line.sku?.trim() || null,
            quantity: line.quantity || 1,
            unit: line.unit || 'U',
            unit_price_excl_tax: line.unit_price_excl_tax || 0,
            discount_rate: line.discount_rate ?? 0,
            line_total_excl_tax: computeLineTotal(line),
         }));

         const { error: upsertError } = await (supabase.from('document_line') as any).upsert(
            updates,
            { onConflict: 'id' }
         );

         if (upsertError) throw upsertError;
      }

      if (newLines.length) {
         const inserts = newLines.map((line) => ({
            document_id: docId,
            position: line.position,
            description: line.sku?.trim() || 'Discount line',
            sku: line.sku?.trim() || null,
            quantity: line.quantity || 1,
            unit: line.unit || 'U',
            unit_price_excl_tax: line.unit_price_excl_tax || 0,
            discount_rate: line.discount_rate ?? 0,
            line_total_excl_tax: computeLineTotal(line),
         }));

         const { error } = await (supabase.from('document_line') as any).insert(inserts);
         if (error) throw error;
      }

      await loadLines();
   } catch (error) {
      linesError.value = error instanceof Error ? error.message : 'Failed to save lines.';
   } finally {
      isSaving.value = false;
   }
};

const computeLineTotal = (line: LineTotalsInput) => {
   const quantity = Number(line.quantity || 0);
   const unitPrice = Number(line.unit_price_excl_tax || 0);
   const discountRate = Number(line.discount_rate || 0);
   const subtotal = quantity * unitPrice;
   return Number((subtotal * (1 - discountRate / 100)).toFixed(2));
};

const formatAmount = (value: number) => {
   if (!Number.isFinite(value)) return '-';
   return Number(value).toLocaleString(undefined, {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
   });
};

const goBack = () => {
   router.push('/vendors/family');
};

onMounted(() => {
   loadFamily();
});
</script>
