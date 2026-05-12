<template>
   <div class="bg-white">
      <form @submit.prevent="$emit('submitRFQ')" class="space-y-2">
         <!-- Message -->
         <div>
            <label for="rfq-message" class="block text-sm font-medium text-gray-700 mb-2">
               {{ t('opportunities.rfqMessage') }}
            </label>
            <textarea
               ref="messageInputRef"
               id="rfq-message"
               name="ao rfq-message"
               v-model="rfqForm.message"
               @input="handleMessageInput"
               rows="6"
               :placeholder="t('opportunities.rfqMessagePlaceholder')"
               class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
            />
            <div class="mt-2 flex justify-end gap-2">
               <button
                  type="button"
                  @click="applyTest1"
                  class="px-2 py-1 text-xs font-medium text-gray-600 border border-gray-300 rounded hover:text-gray-900 hover:bg-gray-50"
               >
                  test
               </button>
               <button
                  type="button"
                  @click="applyTest2"
                  class="px-2 py-1 text-xs font-medium text-gray-600 border border-gray-300 rounded hover:text-gray-900 hover:bg-gray-50"
               >
                  test 2
               </button>
            </div>
         </div>

         <!-- File Upload -->
         <div>
            <label for="rfq-file" class="block text-sm font-mediumxs text-gray-700">
               {{ t('opportunities.rfqAttachment') }}
            </label>
            <div class="flex items-center gap-3">
               <input
                  id="rfq-file"
                  name="rfq-file"
                  type="file"
                  @change="$emit('onFileSelected', $event)"
                  class="ao flex-1 px-4 py-2 border border-gray-300 rounded-lg cursor-pointer"
               />
               <span
                  v-if="rfqForm.file"
                  class="text-sm text-green-600 font-medium whitespace-nowrap"
               >
                  {{ t('opportunities.rfqFileSelected', { fileName: rfqForm.file.name }) }}
               </span>
            </div>
         </div>

         <!-- Submit Buttons -->
         <div class="flex gap-3">
            <button
               type="submit"
               :disabled="isCreatingRFQ || (!rfqForm.message.trim() && !rfqForm.file)"
               class="flex-1 px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
            >
               {{ isCreatingRFQ ? t('opportunities.rfqSubmitting') : t('opportunities.rfqSubmit') }}
            </button>
         </div>

         <!-- Status Messages -->
         <div v-if="rfqSuccessMessage" class="p-4 bg-green-50 border border-green-200 rounded-lg">
            <p class="text-green-800">✓ {{ rfqSuccessMessage }}</p>
         </div>

         <div v-if="rfqErrorMessage" class="p-4 bg-red-50 border border-red-200 rounded-lg">
            <p class="text-red-800">✗ {{ rfqErrorMessage }}</p>
         </div>
      </form>
   </div>
</template>

<script setup lang="ts">
import { ref, nextTick, watch } from 'vue';
import { useI18n } from '../../../../i18n/useI18n';

const { t } = useI18n();

const props = defineProps({
   rfqForm: { type: Object, required: true },
   isCreatingRFQ: { type: Boolean, required: true },
   rfqErrorMessage: { type: String, required: true },
   rfqSuccessMessage: { type: String, required: true },
});

defineEmits(['submitRFQ', 'onFileSelected']);

const messageInputRef = ref<HTMLTextAreaElement | null>(null);

const getScrollParent = (el: HTMLElement | null) => {
   if (!el) return null;
   let parent = el.parentElement;
   while (parent) {
      const style = window.getComputedStyle(parent);
      if (style.overflowY === 'auto' || style.overflowY === 'scroll') {
         return parent;
      }
      parent = parent.parentElement;
   }
   return document.scrollingElement;
};

const resizeMessageTextarea = () => {
   const el = messageInputRef.value;
   if (!el) return;
   const scrollParent = getScrollParent(el);
   const prevScrollTop =
      scrollParent instanceof HTMLElement ? scrollParent.scrollTop : window.scrollY;
   el.style.height = 'auto';
   el.style.height = `${el.scrollHeight}px`;
   if (scrollParent instanceof HTMLElement) {
      scrollParent.scrollTop = prevScrollTop;
   } else if (typeof prevScrollTop === 'number') {
      window.scrollTo({ top: prevScrollTop });
   }
};

const handleMessageInput = () => {
   resizeMessageTextarea();
};

const focusMessageEnd = async () => {
   await nextTick();
   const el = messageInputRef.value;
   if (!el) return;
   resizeMessageTextarea();
   const length = el.value.length;
   el.focus();
   el.setSelectionRange(length, length);
};

defineExpose({ focusMessageEnd });

watch(
   () => props.rfqForm.message,
   () => nextTick(() => resizeMessageTextarea()),
   { immediate: true }
);

const RFQ_TEST_1 = `Bonjour, 
Je vous présente mes Meilleurs Vœux pour cette Nouvelle Année 

Nous souhaiterions avoir votre meilleure offre de prix revendeur et vos délais pour la demande ci-dessous :

Produit : Industrial VRLA Battery, 12 V, 7 Ah, AGM construction 
Manufacturer: YUASA 
P/N: NP7-12FR 
Quantité : 18 

Produit : Battery Smart Charger, 12 V, 12 A 
Manufacturer: YUASA 
P/N: YCX12 
Quantité : 2 

Livraison : France Par avance merci pour votre retour et à votre entière
disposition pour tout complément d'information. 

Bonne fin de journée. 

Bien cordialement,

Malo Yamakado 
Service Export 
Contact & Whatsapp : +33 6 11 72 19 85 
Email : malo@ai-oe.co 
Website : ai-oe.co 
Address : 3 rue Herault, 92190 Meudon – France`;

const RFQ_TEST_2 = `S.A.R.L. CABLOMAN Devis N° Date Client
160, AVENUE PAUL VAILLANT COUTURIER DE093466 07/01/2026 006
93120 La Courneuve
Tél : 0148359099
Capital : 19 000,00 Euros
R.C.S. : 491 638 458 PARIS
SIRET : 49163845800027
N° TVA intracom : FR 25 491638458
SC GM DIFF
152 RUE DE PARIS
92190 MEUDON
SIRET client : 49833576900010
Référence Désignation Quantité P.U. HT % REM Remise HT Montant HT TVA
LEG600801 PLAQUE 1P BLANC 24 000,... 3
LEG600802 PLAQUE 2P BLANC 2 000,000 3
LEG600803 PLAQUE 3P BLANC 1 000,000 3
LEG600804 PLAQUE 4P BLANC 300,000 3
LEG600001 INTER OU VV BLANC 4 000,000 3
LEG600004 POUSSOIR BLANC 1 000,000 3
LEG600002 DOUBLE VV BLANC 1 000,000 3
LEG600009 VV TEMOINS BLANC 300,000 3
LEG600016 POUSSOIR LUMINEUX BLANC 300,000 3
LEG600018 POUSSOIR LUM SYM SONN 200,000 3
BLANC
LEG600021 INTER VOLETS ROULANTS 500,000 3
BLANC
LEG600031 TRANSFORMEUR SIMPLE 1 000,000 3
BLANC
LEG600044 OBTURATEUR BLANC 500,000 3`;

const applyTest1 = () => {
   props.rfqForm.message = RFQ_TEST_1;
};

const applyTest2 = () => {
   props.rfqForm.message = RFQ_TEST_2;
};
</script>
