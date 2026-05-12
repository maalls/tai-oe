<template>
   <div class="opportunity-page">
      <OpportunityHeader :opportunityId="opportunityId" activeTab="account" />

      <div v-if="errorMessage" class="bg-red-100 text-red-700 rounded-lg">
         {{ errorMessage }}
      </div>

      <div v-if="successMessage" class="bg-green-100 text-green-700 rounded-lg">
         {{ successMessage }}
      </div>

      <div v-if="isLoading" class="flex justify-center items-center py-12">
         <div class="text-gray-500">{{ t('opportunities.loadingDots') }}</div>
      </div>

      <div v-else class="opportunity-page-section m-4 bg-white rounded-lg shadow p-6">
         <div class="flex items-center justify-between">
            <div>
               <h3 class="text-sm font-semibold text-gray-700">
                  {{ t('opportunities.accountDetails') }}
               </h3>
               <div v-if="accountForm.id" class="text-xs text-gray-500 mt-1">
                  ID: <span class="font-mono">{{ accountForm.id }}</span>
               </div>
            </div>
            <button
               type="button"
               @click="saveAccountDetails"
               :disabled="isSavingAccount"
               class="px-3 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-300 disabled:text-gray-600"
            >
               {{ isSavingAccount ? t('opportunities.saving') : t('opportunities.saveAccount') }}
            </button>
         </div>

         <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <label class="flex flex-col gap-1 relative">
               <span class="text-gray-700 font-medium">{{ t('opportunities.name') }}</span>
               <input
                  v-model="accountForm.name"
                  type="text"
                  class="px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                  @input="onAccountSearchInput"
                  @focus="onAccountNameFocus"
                  @blur="onAccountNameBlur"
               />
               <div v-if="isSearching" class="text-xs text-gray-500 mt-1">
                  {{ t('opportunities.searching') }}
               </div>
               <div
                  v-if="showAccountResults && accountSearchResults.length > 0"
                  class="mt-2 border border-gray-200 rounded shadow bg-white divide-y absolute top-full left-0 right-0 z-10"
               >
                  <button
                     v-for="acct in accountSearchResults"
                     :key="acct.id"
                     type="button"
                     class="w-full text-left px-3 py-2 text-sm hover:bg-gray-50"
                     @mousedown.prevent
                     @click="assignAccountToOpportunity(acct)"
                  >
                     <div class="font-medium text-gray-900">{{ acct.name }}</div>
                     <div class="text-xs text-gray-500">{{ acct.id }}</div>
                  </button>
               </div>
               <div
                  v-else-if="
                     showAccountResults && searchPerformed && accountForm.name && !isSearching
                  "
                  class="mt-2"
               >
                  <div class="text-xs text-gray-500 mb-2">
                     {{ t('opportunities.noMatchingAccounts') }}
                  </div>
                  <button
                     type="button"
                     class="px-3 py-2 text-xs bg-blue-600 text-white rounded hover:bg-blue-700"
                     @mousedown.prevent
                     @click="createAccountAndAssign"
                  >
                     {{ t('opportunities.createAccountNamed', { name: accountForm.name }) }}
                  </button>
               </div>
            </label>
            <label class="flex flex-col gap-1">
               <span class="text-gray-700 font-medium">{{ t('opportunities.vatNumber') }}</span>
               <input
                  v-model="accountForm.vat_number"
                  type="text"
                  class="px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
               />
            </label>
            <label class="flex flex-col gap-1">
               <span class="text-gray-700 font-medium">{{ t('opportunities.siret') }}</span>
               <input
                  v-model="accountForm.siret"
                  type="text"
                  class="px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
               />
            </label>
            <label class="flex flex-col gap-1">
               <span class="text-gray-700 font-medium">{{ t('opportunities.paymentTerms') }}</span>
               <input
                  v-model="accountForm.payment_terms_default"
                  type="text"
                  class="px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
               />
            </label>
            <label class="flex flex-col gap-1 md:col-span-2">
               <span class="text-gray-700 font-medium">{{ t('opportunities.addressLine1') }}</span>
               <input
                  v-model="accountForm.address_line1"
                  type="text"
                  class="px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
               />
            </label>
            <label class="flex flex-col gap-1 md:col-span-2">
               <span class="text-gray-700 font-medium">{{ t('opportunities.addressLine2') }}</span>
               <input
                  v-model="accountForm.address_line2"
                  type="text"
                  class="px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
               />
            </label>
            <label class="flex flex-col gap-1">
               <span class="text-gray-700 font-medium">{{ t('opportunities.postalCode') }}</span>
               <input
                  v-model="accountForm.postal_code"
                  type="text"
                  class="px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
               />
            </label>
            <label class="flex flex-col gap-1">
               <span class="text-gray-700 font-medium">{{ t('opportunities.city') }}</span>
               <input
                  v-model="accountForm.city"
                  type="text"
                  class="px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
               />
            </label>
            <label class="flex flex-col gap-1">
               <span class="text-gray-700 font-medium">{{ t('opportunities.countryCode') }}</span>
               <input
                  v-model="accountForm.country_code"
                  type="text"
                  maxlength="2"
                  class="px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
               />
            </label>
         </div>

         <!-- Contacts for this Account -->
         <div class="mt-6 border border-gray-300 rounded-lg p-4 bg-gray-50">
            <div class="flex items-center justify-between">
               <h3 class="text-sm font-semibold text-gray-700">
                  {{ t('opportunities.contacts') }}
               </h3>
               <router-link
                  :to="
                     accountForm.id ? `/contacts/new?account_id=${accountForm.id}` : '/contacts/new'
                  "
                  class="px-3 py-1.5 text-xs border border-gray-300 rounded hover:bg-gray-100 text-gray-700"
               >
                  {{ t('opportunities.addContact') }}
               </router-link>
            </div>

            <div v-if="accountContacts.length > 0" class="space-y-2">
               <div
                  v-for="c in accountContacts"
                  :key="c.id"
                  class="flex items-center justify-between p-3 bg-white rounded border border-gray-200"
               >
                  <div>
                     <p class="text-sm font-medium text-gray-900">{{ c.name }}</p>
                     <p class="text-xs text-gray-600">
                        {{ c.email || '—' }}
                        <span v-if="c.phone"> • {{ c.phone }}</span>
                        <span v-if="c.role_title"> • {{ c.role_title }}</span>
                     </p>
                  </div>
                  <router-link
                     :to="`/contacts/${c.id}`"
                     class="text-xs px-3 py-1.5 border border-gray-300 rounded hover:bg-gray-50 text-gray-700"
                  >
                     {{ t('opportunities.view') }}
                  </router-link>
               </div>
            </div>
            <div v-else class="text-sm text-gray-500">
               {{ t('opportunities.noContactsForAccount') }}
            </div>
         </div>
      </div>
   </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { supabase } from '../../../../lib/supabase';
import OpportunityHeader from '../../OpportunityHeader.vue';
import { useI18n } from '../../../../i18n/useI18n';

const { t } = useI18n();

const route = useRoute();
const opportunityId = route.params.id as string;

const isLoading = ref(true);
const isSavingAccount = ref(false);
const errorMessage = ref('');
const successMessage = ref('');
const accountContacts = ref<any[]>([]);
const accountSearchResults = ref<any[]>([]);
const isSearching = ref(false);
const searchDebounce = ref<ReturnType<typeof setTimeout> | null>(null);
const showAccountResults = ref(false);
const blurTimeout = ref<ReturnType<typeof setTimeout> | null>(null);
const searchPerformed = ref(false);

interface AccountForm {
   id?: string;
   name: string;
   vat_number?: string;
   siret?: string;
   address_line1?: string;
   address_line2?: string;
   postal_code?: string;
   city?: string;
   country_code?: string;
   payment_terms_default?: string;
}

const accountForm = ref<AccountForm>({
   name: '',
   vat_number: '',
   siret: '',
   address_line1: '',
   address_line2: '',
   postal_code: '',
   city: '',
   country_code: 'FR',
   payment_terms_default: '',
});

const loadAccountDetails = async (accountId: string) => {
   if (!accountId) return;
   try {
      const { data, error } = await supabase
         .from('account')
         .select(
            'id, name, vat_number, siret, address_line1, address_line2, postal_code, city, country_code, payment_terms_default'
         )
         .eq('id', accountId)
         .single();

      if (error) {
         console.error('[AccountPage] Error loading account details:', error);
         return;
      }

      if (data) {
         const accountData = data as any;
         accountForm.value = {
            id: accountData.id,
            name: accountData.name || '',
            vat_number: accountData.vat_number || '',
            siret: accountData.siret || '',
            address_line1: accountData.address_line1 || '',
            address_line2: accountData.address_line2 || '',
            postal_code: accountData.postal_code || '',
            city: accountData.city || '',
            country_code: accountData.country_code || 'FR',
            payment_terms_default: accountData.payment_terms_default || '',
         };

         // Load contacts for this account
         await loadAccountContacts(accountData.id);
      }
   } catch (error) {
      console.error('[AccountPage] Unexpected error loading account:', error);
   }
};

const loadAccountContacts = async (accountId: string) => {
   try {
      const { data, error } = await supabase
         .from('contact')
         .select('id, name, email, phone, role_title')
         .eq('account_id', accountId)
         .order('name', { ascending: true });

      if (error) {
         console.error('[AccountPage] Error loading contacts:', error);
         accountContacts.value = [];
         return;
      }

      accountContacts.value = data || [];
   } catch (error) {
      console.error('[AccountPage] Unexpected error loading contacts:', error);
      accountContacts.value = [];
   }
};

const loadOpportunity = async () => {
   console.log('Loading opportunity with ID:', opportunityId);
   isLoading.value = true;

   if (opportunityId === 'new') {
      isLoading.value = false;
      return;
   }

   try {
      const { data, error } = await supabase
         .from('opportunity')
         .select('account_id')
         .eq('id', opportunityId)
         .single();

      if (error) {
         errorMessage.value = t('opportunities.errorLoadingOpportunity', { message: error.message });
         return;
      }

      console.log('loaded opportunity data:', data);
      const opportunityData = data as any;
      if (opportunityData && opportunityData.account_id) {
         await loadAccountDetails(opportunityData.account_id);
      }
   } catch (error) {
      errorMessage.value = t('opportunities.errorLoadingOpportunity', {
         message: error instanceof Error ? error.message : t('opportunities.unknownError'),
      });
   } finally {
      isLoading.value = false;
   }
};

const onAccountSearchInput = () => {
   if (searchDebounce.value) {
      clearTimeout(searchDebounce.value);
   }

   const query = accountForm.value.name.trim();
   if (!query) {
      accountSearchResults.value = [];
      showAccountResults.value = false;
      searchPerformed.value = false;
      return;
   }

   showAccountResults.value = true;
   searchPerformed.value = false;

   searchDebounce.value = setTimeout(async () => {
      isSearching.value = true;
      try {
         const { data, error } = await supabase
            .from('account')
            .select('id, name')
            .ilike('name', `%${query}%`)
            .order('name', { ascending: true })
            .limit(10);

         if (error) {
            console.error('[AccountPage] Error searching accounts:', error);
            accountSearchResults.value = [];
            return;
         }

         accountSearchResults.value = data || [];
      } catch (err) {
         console.error('[AccountPage] Unexpected error searching accounts:', err);
         accountSearchResults.value = [];
      } finally {
         isSearching.value = false;
         searchPerformed.value = true;
      }
   }, 250);
};

const onAccountNameFocus = () => {
   if (blurTimeout.value) {
      clearTimeout(blurTimeout.value);
      blurTimeout.value = null;
   }
   if (accountForm.value.name.trim()) {
      onAccountSearchInput();
   }
   showAccountResults.value = true;
};

const onAccountNameBlur = () => {
   if (blurTimeout.value) {
      clearTimeout(blurTimeout.value);
   }
   blurTimeout.value = setTimeout(() => {
      showAccountResults.value = false;
   }, 150);
};

const assignAccountToOpportunity = async (acct: { id: string; name: string }) => {
   if (!opportunityId || opportunityId === 'new') return;
   errorMessage.value = '';
   successMessage.value = '';

   try {
      const { error } = await (supabase.from('opportunity') as any)
         .update({ account_id: acct.id })
         .eq('id', opportunityId);

      if (error) {
         throw new Error(error.message);
      }

      accountForm.value.name = acct.name;
      accountSearchResults.value = [];
      showAccountResults.value = false;
      await loadAccountDetails(acct.id);
      successMessage.value = t('opportunities.accountReassignedSuccess');
      setTimeout(() => {
         successMessage.value = '';
      }, 2000);
   } catch (err: any) {
      errorMessage.value = err?.message || t('opportunities.errors.failedToAssignAccount');
   }
};

const createAccountAndAssign = async () => {
   if (!opportunityId || opportunityId === 'new') return;
   const name = accountForm.value.name.trim();
   if (!name) return;

   errorMessage.value = '';
   successMessage.value = '';
   isSearching.value = true;

   try {
      const { data: newAccount, error: createError } = await (supabase.from('account') as any)
         .insert({ name })
         .select('id, name')
         .single();

      if (createError) {
         throw new Error(createError.message);
      }

      const { error: assignError } = await (supabase.from('opportunity') as any)
         .update({ account_id: newAccount.id })
         .eq('id', opportunityId);

      if (assignError) {
         throw new Error(assignError.message);
      }

      accountForm.value.name = newAccount.name;
      accountSearchResults.value = [];
      showAccountResults.value = false;
      await loadAccountDetails(newAccount.id);
      successMessage.value = t('opportunities.accountCreatedAndLinkedSuccess');
      setTimeout(() => {
         successMessage.value = '';
      }, 2000);
   } catch (err: any) {
      errorMessage.value = err?.message || t('opportunities.errors.failedToCreateAccount');
   } finally {
      isSearching.value = false;
   }
};

const saveAccountDetails = async () => {
   if (!accountForm.value.id) return;
   isSavingAccount.value = true;
   errorMessage.value = '';
   successMessage.value = '';

   try {
      const payload = {
         name: accountForm.value.name,
         vat_number: accountForm.value.vat_number || null,
         siret: accountForm.value.siret || null,
         address_line1: accountForm.value.address_line1 || null,
         address_line2: accountForm.value.address_line2 || null,
         postal_code: accountForm.value.postal_code || null,
         city: accountForm.value.city || null,
         country_code: accountForm.value.country_code || 'FR',
         payment_terms_default: accountForm.value.payment_terms_default || null,
         updated_at: new Date().toISOString(),
      };

      const { error } = await (supabase.from('account') as any)
         .update(payload)
         .eq('id', accountForm.value.id);

      if (error) {
         throw new Error(error.message);
      }

      successMessage.value = t('opportunities.accountUpdatedSuccess');
      setTimeout(() => {
         successMessage.value = '';
      }, 2000);
   } catch (err: any) {
      errorMessage.value = err?.message || t('opportunities.errors.failedToUpdateAccount');
   } finally {
      isSavingAccount.value = false;
   }
};

onMounted(() => {
   loadOpportunity();
});
</script>
