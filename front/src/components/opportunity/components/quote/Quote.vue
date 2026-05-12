<template>
   <Loading v-if="isLoading" />
   <div v-else class="opportunity-page-section quote-page-root" style="border: 0px solid green">
      <div
         v-if="accountInfo || contactInfo"
         class="rounded-lg border border-gray-200 bg-white p-3 grid grid-cols-1 md:grid-cols-2 gap-3"
      >
         <div class="flex flex-wrap items-top justify-between">
            <div style="border: 0px solid hotpink">
               <div class="text-base font-semibold text-gray-900">
                  {{ accountInfo?.name || '—' }}
                  <span
                     v-if="quoteDocument?.status"
                     :class="quoteStatusClass"
                     class="px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wide rounded-full"
                  >
                     {{ quoteDocument.status }}
                  </span>
               </div>
               <div class="text-xs text-gray-600">
                  {{ contactInfo?.name || '—' }}
                  {{ contactInfo?.email ? ` <${contactInfo.email}>` : '' }}
               </div>
               <div class="mt-2 text-xs text-gray-600">
                  {{ t('opportunities.quoteIdLabel') }}: {{ quoteDocument?.id }}
               </div>
            </div>
            <div style="border: 0px solid chocolate">
               <div>
                  <label class="gap-1">
                     <span class="text-gray-700 font-medium pr-2">
                        {{ t('opportunities.currencyLabel') }}:
                     </span>
                     <select
                        v-model="quoteDocument.currency"
                        disabled
                        class="px-1 py-0.5 text-xs w-16 border border-gray-300 rounded bg-white text-gray-700 cursor-not-allowed"
                     >
                        <option value="EUR">EUR</option>
                     </select>
                  </label>
               </div>
            </div>
         </div>
         <div
            style="border: 0px solid yellow"
            class="flex flex-wrap items-center justify-between gap-3 mb-3"
         >
            <div class="gap-2 text-sm text-gray-600">
               <div class="flex items-center gap-2"></div>
            </div>
            <div class="flex flex-wrap items-center gap-2">
               <!--button
                  type="button"
                  class="px-3 py-2 text-xs font-medium border border-gray-200 rounded"
                  :class="
                     viewParams.isAdminMode
                        ? 'bg-gray-900 text-white'
                        : 'bg-white text-gray-700 hover:bg-gray-100'
                  "
                  :title="t('opportunities.adminMode')"
                  :aria-label="t('opportunities.adminMode')"
                  @click="viewParams.isAdminMode = !viewParams.isAdminMode"
               >
                  {{ t('opportunities.adminMode') }}
               </button-->
               <div class="inline-flex rounded border border-gray-200 overflow-hidden">
                  <button
                     type="button"
                     class="p-2 text-sm font-medium"
                     :class="
                        viewParams.quoteViewMode === 'quote'
                           ? 'bg-gray-900 text-white'
                           : 'bg-white text-gray-700 hover:bg-gray-100'
                     "
                     :title="t('opportunities.quoteOnly')"
                     :aria-label="t('opportunities.quoteOnly')"
                     @click="viewParams.quoteViewMode = 'quote'"
                  >
                     <svg
                        class="h-5 w-5"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="1.5"
                        stroke-linecap="round"
                        stroke-linejoin="round"
                     >
                        <rect x="3" y="4" width="18" height="16" rx="2" />
                     </svg>
                     <span class="sr-only">{{ t('opportunities.quoteOnly') }}</span>
                  </button>
                  <button
                     type="button"
                     class="p-2 text-sm font-medium"
                     :class="
                        viewParams.quoteViewMode === 'split'
                           ? 'bg-gray-900 text-white'
                           : 'bg-white text-gray-700 hover:bg-gray-100'
                     "
                     :title="t('opportunities.splitView')"
                     :aria-label="t('opportunities.splitView')"
                     @click="viewParams.quoteViewMode = 'split'"
                  >
                     <svg
                        class="h-5 w-5"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="1.5"
                        stroke-linecap="round"
                        stroke-linejoin="round"
                     >
                        <rect x="3" y="4" width="18" height="16" rx="2" />
                        <path d="M12 4v16" />
                     </svg>
                     <span class="sr-only">{{ t('opportunities.splitView') }}</span>
                  </button>
               </div>

               <div
                  v-if="quoteDocument && quoteDocument.pdf_filename"
                  class="relative flex items-center gap-1"
               >
                  <button
                     type="button"
                     @click="
                        opportunityId
                           ? router.push(`/opportunities/${opportunityId}/preview`)
                           : null
                     "
                     class="p-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 cursor-pointer"
                  >
                     {{ t('opportunities.pdfGenerated') }}
                  </button>
               </div>

               <button
                  v-if="!quoteDocument"
                  type="button"
                  @click="generateQuote"
                  :disabled="isGeneratingQuote || !isEditable"
                  class="p-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-300 disabled:text-gray-600"
               >
                  {{
                     isGeneratingQuote
                        ? t('opportunities.extracting')
                        : t('opportunities.extractFromSource')
                  }}
               </button>
               <button
                  v-if="quoteDocument && !quoteDocument.pdf_filename"
                  type="button"
                  @click="generateQuotePdf"
                  :disabled="isGeneratingPdf || !isEditable"
                  style="margin-right: 8px"
                  class="p-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-300 disabled:text-gray-600"
               >
                  {{
                     isGeneratingPdf
                        ? t('opportunities.generatingPdf')
                        : t('opportunities.generatePdf')
                  }}
               </button>
            </div>
         </div>
      </div>

      <div
         v-if="!isEditable"
         style="border: 0px solid orchid"
         class="mt-4 p-3 rounded-lg border text-sm"
         :class="{
            'bg-green-50 border-green-200 text-green-700':
               opportunity && opportunity.status === 'WON',
            'bg-red-50 border-red-200 text-red-700': opportunity && opportunity.status === 'LOST',
            'bg-yellow-50 border-yellow-200 text-yellow-700':
               quoteDocument && quoteDocument.status === 'SENT',
            'bg-blue-50 border-blue-200 text-blue-700':
               opportunity &&
               opportunity.status !== 'WON' &&
               opportunity &&
               opportunity.status !== 'LOST' &&
               quoteDocument &&
               quoteDocument.status !== 'SENT',
         }"
      >
         <span v-if="opportunity && opportunity.status === 'WON'">{{
            t('opportunities.opportunityWonLocked')
         }}</span>
         <span v-else-if="opportunity && opportunity.status === 'LOST'">{{
            t('opportunities.opportunityLostLocked')
         }}</span>
         <span v-else-if="quoteDocument && quoteDocument.status === 'SENT'">
            {{ t('opportunities.quoteSentCannotEdit') }}
         </span>
         <span v-else>{{ t('opportunities.quoteSentLocked') }}</span>
      </div>
      <div
         class="mt-4"
         style="border: 0px solid cyan"
         :class="
            viewParams.quoteViewMode === 'split'
               ? 'grid grid-cols-1 xl:grid-cols-2 h-[calc(100vh-240px)] gap-2 overflow-hidden'
               : ''
         "
      >
         <div
            style="border: 0px solid grey"
            class="space-y-3 min-w-0"
            :class="viewParams.quoteViewMode === 'split' ? 'min-h-0 overflow-y-auto' : ''"
         >
            <div>
               <QuoteDocument
                  v-if="quoteDocument"
                  :quoteDocument="quoteDocument"
                  :isEditable="isEditable"
                  :isSavingDraft="isSavingDraft"
                  :hideValidation="viewParams.isAdminMode"
                  :flashedFields="flashedFields"
                  :pendingSaveFields="pendingSaveFields"
                  @save="saveQuotDocument"
                  @field-changed="markFieldChanged"
               />
               <div v-else class="text-sm text-gray-600 py-8 text-center">
                  {{ t('opportunities.noQuoteGenerated') }}
               </div>
            </div>
            <!-- Quote Editor -->
         </div>
         <div
            style=""
            v-if="viewParams.quoteViewMode === 'split'"
            class="rounded-lg border border-gray-200 bg-white p-3"
            :class="viewParams.quoteViewMode === 'split' ? 'min-h-0 overflow-y-auto pr-2' : ''"
         >
            <SourceViewer :source="source" />
         </div>
      </div>
   </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, computed, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { supabase } from '../../../../lib/supabase';
import { useI18n } from '../../../../i18n/useI18n';
import { buildAuthHeaders } from '../../utils/auth';
import SourceViewer from '../source/SourceViewer.vue';
import QuoteDocument from './QuoteDocument.vue';
import { useOpportunitySource } from '../../../../composables/useOpportunitySource';
import Loading from '../../../shared/Loading.vue';

const stagesWithSentQuotes = new Set([
   'RFQ_IN_PROGRESS',
   'NEGOTIATION',
   'OFFER_SENT',
   'COMMITMENT',
   'PREPARATION',
   'DELIVERY_IN_PROGRESS',
   'ACCEPTED',
   'INVOICED',
   'PAID',
   'CLOSED_WON',
   'CLOSED_LOST',
]);
const route = useRoute();
const router = useRouter();
const { t } = useI18n();
const opportunityId = route.params.id as string;

// View mode toggle
import { reactive } from 'vue';

const viewParams = reactive({
   quoteViewMode: 'quote' as 'quote' | 'split',
   isAdminMode: true,
});
const opportunity = ref<any>(null);

const applyViewStateFromUrl = () => {
   const view = route.query.view;
   const admin = route.query.admin;
   if (view === 'quote' || view === 'split') {
      viewParams.quoteViewMode = view;
   }
   if (admin === '1' || admin === '0') {
      viewParams.isAdminMode = admin === '1';
   }
};

const syncViewStateToUrl = async () => {
   const nextQuery = { ...route.query };
   nextQuery.view = viewParams.quoteViewMode;
   nextQuery.admin = viewParams.isAdminMode ? '1' : '0';
   await router.replace({ query: nextQuery });
};

// Source panel state
const { source, loadSourceFromOpportunity } = useOpportunitySource(opportunityId);

const isLoading = ref(true);
const quoteDocument = ref<any>(null);
const isGeneratingQuote = ref(false);
const isGeneratingPdf = ref(false);
const isSavingDraft = ref(false);
const pendingSaveFields = ref<Set<string>>(new Set());
const flashedFields = ref<Set<string>>(new Set());
const pdfMenuOpen = ref(false);
const accountInfo = ref<any>(null);
const contactInfo = ref<any>(null);

const handleDocumentClick = () => {
   if (pdfMenuOpen.value) {
      pdfMenuOpen.value = false;
   }
};

const quoteStatusClass = computed(() => {
   const status = quoteDocument.value?.status || '';
   switch (status) {
      case 'SENT':
         return 'bg-blue-100 text-blue-700';
      case 'DRAFT':
         return 'bg-gray-100 text-gray-700';
      default:
         return 'bg-slate-100 text-slate-700';
   }
});

const finalizeSaveFlash = () => {
   if (pendingSaveFields.value.size === 0) return;
   const savedKeys = new Set(pendingSaveFields.value);
   pendingSaveFields.value.clear();
   flashedFields.value = savedKeys;
   setTimeout(() => {
      savedKeys.clear();
   }, 900);
   window.dispatchEvent(
      new CustomEvent('header-notification', {
         detail: {
            type: 'success',
            content: t('opportunities.quoteUpdatedSuccess'),
         },
      })
   );
};

const isEditable = computed(() => {
   // Cannot edit if quote has been sent
   if (quoteDocument.value?.status === 'SENT') {
      return false;
   }
   // Guard against null opportunity
   if (!opportunity.value || !opportunity.value.stage) {
      return false;
   }
   return (
      (opportunity.value.stage === 'NEGOTIATION' ||
         opportunity.value.stage === 'NEW_LEAD' ||
         opportunity.value.stage === 'RFQ_IN_PROGRESS' ||
         opportunity.value.stage === 'RFP_IN_PROGRESS' ||
         quoteDocument.value?.status === 'DRAFT') &&
      opportunity.value.stage !== 'WON' &&
      opportunity.value.stage !== 'LOST'
   );
});

const markFieldChanged = (key: string) => {
   console.log('Field changed:', key);
   pendingSaveFields.value.add(key);
   saveQuotDocument();
};

const loadOpportunity = async () => {
   //console.log('[QuotePage] Loading opportunity stage for opportunity ID:', opportunityId);
   try {
      const { data, error } = await supabase
         .from('opportunity')
         .select('*')
         .eq('id', opportunityId)
         .single();

      if (error) {
         throw new Error('[QuotePage] Error loading opportunity stage: ' + error.message);
         return;
      }

      if (data) {
         opportunity.value = data;
         watch(
            () => opportunity.value.stage,
            () => {
               loadQuoteDocument();
            }
         );
      }
   } catch (error) {
      console.error('[QuotePage] Unexpected error loading opportunity stage:', error);
   }
};

const loadQuoteDocument = async () => {
   try {
      // Load the most recent quote document
      let query = supabase
         .from('document')
         .select(`*, document_line (*)`)
         .eq('opportunity_id', opportunityId)
         .eq('type', 'QUOTE');

      if (!stagesWithSentQuotes.has(opportunity.value.stage)) {
         query = query.eq('status', 'DRAFT');
      } else {
         query = query.in('status', ['DRAFT', 'SENT']);
      }

      const { data, error } = await query.order('created_at', { ascending: false }).limit(1);

      if (error) {
         console.error('[QuotePage] Error loading quote document:', error);
         return;
      }

      //console.log('[QuotePage] Loaded quote document:', data[0]);
      quoteDocument.value = data[0] || null;

      if (!quoteDocument.value) {
         window.dispatchEvent(
            new CustomEvent('header-notification', {
               detail: {
                  error: t('opportunities.noExistingQuoteDocument'),
               },
            })
         );
      }
   } catch (error) {
      console.error('[QuotePage] Unexpected error loading quote document:', error);
   }
};

const loadAccountAndContact = async () => {
   try {
      const { data: oppData, error: oppError } = await supabase
         .from('opportunity')
         .select('account_id')
         .eq('id', opportunityId)
         .single();

      if (oppError) {
         console.error('[QuotePage] Error loading opportunity for account info:', oppError);
         return;
      }

      const accountId = (oppData as any)?.account_id;

      if (accountId) {
         const { data: accountData, error: accountError } = await supabase
            .from('account')
            .select('id, name, vat_number, siret, city, country_code')
            .eq('id', accountId)
            .single();

         if (!accountError && accountData) {
            accountInfo.value = accountData as any;
         }
      }

      const { data: buyerParticipants, error: participantError } = await supabase
         .from('opportunity_participant')
         .select('contact:contact_id(id, name, email, phone, role_title)')
         .eq('opportunity_id', opportunityId)
         .eq('role', 'BUYER')
         .limit(1);

      if (!participantError && buyerParticipants && buyerParticipants.length > 0) {
         contactInfo.value = (buyerParticipants[0] as any).contact || null;
         return;
      }

      if (accountId) {
         const { data: accountContacts, error: contactError } = await supabase
            .from('contact')
            .select('id, name, email, phone, role_title')
            .eq('account_id', accountId)
            .order('created_at', { ascending: true })
            .limit(1);

         if (!contactError && accountContacts && accountContacts.length > 0) {
            contactInfo.value = accountContacts[0] as any;
         }
      }
   } catch (error) {
      console.error('[QuotePage] Unexpected error loading account/contact info:', error);
   }
};

const generateQuote = async () => {
   isGeneratingQuote.value = true;

   try {
      const headers = await buildAuthHeaders(true);

      const response = await fetch(`/api/opportunity/${opportunityId}/rfq/generate`, {
         method: 'POST',
         headers,
      });

      //console.log('[QuotePage] Generate quote response status:', response.status);

      const result = await response.json();
      if (!response.ok) {
         throw new Error(result?.message || t('opportunities.errors.failedToGenerateQuote'));
      }

      // Reload the full document with lines (the generation response is a partial object
      // without document_line, so we need to re-fetch to get client_discount_rate etc.)
      await loadQuoteDocument();
      window.dispatchEvent(
         new CustomEvent('header-notification', {
            detail: { success: t('opportunities.quoteDraftGeneratedSuccess') },
         })
      );
   } catch (error: any) {
      //console.log('[QuotePage] Error generating quote:', error);
      window.dispatchEvent(
         new CustomEvent('header-notification', {
            detail: { error: error?.message || t('opportunities.errors.failedToGenerateQuote') },
         })
      );
   } finally {
      isGeneratingQuote.value = false;
   }
};

const saveQuotDocument = async () => {
   //console.log('[QuotePage] Saving quote document with current data:', quoteDocument.value);
   if (!quoteDocument.value?.id) return;

   isSavingDraft.value = true;

   try {
      const headers = await buildAuthHeaders(true);
      //console.log('[QuotePage] Saving quote with data:', quoteDocument.value);

      try {
         const response = await fetch(`/api/quote/${quoteDocument.value.id}`, {
            method: 'POST',
            headers,
            body: JSON.stringify(quoteDocument.value),
         });

         const payload = await response.json();

         if (!response.ok) {
            throw new Error(payload?.error || t('opportunities.errors.failedToSaveQuoteDraft'));
         }

         //console.log('[QuotePage] Quote document saved successfully:', payload);

         quoteDocument.value = payload;
         finalizeSaveFlash();
      } catch (error: any) {
         console.error('[QuotePage] Error saving quote draft 1', error);
         window.dispatchEvent(
            new CustomEvent('header-notification', {
               detail: {
                  type: 'error',
                  content: error?.message || t('opportunities.errors.failedToSaveDraft'),
               },
            })
         );
      }
   } catch (error: any) {
      console.error('[QuotePage] Error saving quote draft:= 2', error);
      window.dispatchEvent(
         new CustomEvent('header-notification', {
            detail: {
               type: 'error',
               content: error?.message || t('opportunities.errors.failedToSaveDraft'),
            },
         })
      );
   } finally {
      isSavingDraft.value = false;
   }
};

applyViewStateFromUrl();
watch(() => [viewParams.quoteViewMode, viewParams.isAdminMode], syncViewStateToUrl);

const generateQuotePdf = async () => {
   if (!quoteDocument.value?.id) return;

   isGeneratingPdf.value = true;

   try {
      const headers = await buildAuthHeaders(true);

      const response = await fetch(`/api/quote/${quoteDocument.value.id}/pdf`, {
         method: 'POST',
         headers,
      });

      const result = await response.json();
      if (!response.ok) {
         throw new Error(result?.message || t('opportunities.errors.failedToGeneratePdf'));
      }

      quoteDocument.value = {
         ...quoteDocument.value,
         pdf_filename: result?.pdf_filename,
      };
      // Navigate to Preview page
      if (opportunityId) {
         router.push(`/opportunities/${opportunityId}/preview`);
      }
   } catch (error: any) {
      window.dispatchEvent(
         new CustomEvent('header-notification', {
            detail: { error: error?.message || t('opportunities.errors.failedToGeneratePdf') },
         })
      );
   } finally {
      isGeneratingPdf.value = false;
   }
};

onMounted(async () => {
   isLoading.value = true;
   document.addEventListener('click', handleDocumentClick);

   try {
      // Load opportunity first, then quote document (which depends on stage)
      await loadOpportunity();
      await Promise.all([
         loadQuoteDocument(),
         loadSourceFromOpportunity(),
         loadAccountAndContact(),
      ]);
   } finally {
      //console.log('[QuotePage] Finished loading data, setting isLoading to false');
      isLoading.value = false;
   }
});

// Watch for stage changes and reload quote

onBeforeUnmount(() => {
   document.removeEventListener('click', handleDocumentClick);
});
</script>

<style scoped>
@keyframes saveFlash {
   0% {
      background-color: rgb(209, 250, 229);
   }
   100% {
      background-color: transparent;
   }
}

.save-flash {
   animation: saveFlash 1s ease-out;
}
</style>
