<template>
   <div>
      <AccountNavHeader />
      <div class="p-6">
         <!-- Header -->
         <div class="mb-6 flex items-center justify-between">
            <div>
               <router-link
                  to="/accounts"
                  class="text-blue-600 hover:text-blue-700 text-sm mb-2 inline-block"
               >
                  ← Back to Accounts
               </router-link>
               <h1 class="text-3xl font-bold text-gray-900">
                  {{ isNewAccount ? 'Create Account' : 'Edit Account' }}
               </h1>
            </div>
            <button
               v-if="!isNewAccount"
               @click="handleDelete"
               :disabled="isDeleting"
               class="px-4 py-2 bg-red-600 hover:bg-red-700 disabled:bg-gray-400 text-white rounded-lg font-medium"
            >
               {{ isDeleting ? 'Deleting...' : 'Delete' }}
            </button>
         </div>

         <!-- Error Message -->
         <div v-if="errorMessage" class="mb-4 p-4 bg-red-100 text-red-700 rounded-lg">
            {{ errorMessage }}
         </div>

         <!-- Success Message -->
         <div v-if="successMessage" class="mb-4 p-4 bg-green-100 text-green-700 rounded-lg">
            {{ successMessage }}
         </div>

         <!-- Loading State -->
         <div v-if="isLoading" class="flex justify-center items-center py-12">
            <div class="text-gray-500">Loading...</div>
         </div>

         <!-- Form -->
         <div v-else class="bg-white rounded-lg shadow p-6 max-w-2xl">
            <form @submit.prevent="handleSave" class="space-y-6">
               <!-- Name -->
               <div>
                  <label for="name" class="block text-sm font-medium text-gray-700 mb-2">
                     Company Name *
                  </label>
                  <input
                     id="name"
                     v-model="formData.name"
                     type="text"
                     required
                     placeholder="Company name"
                     class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
               </div>

               <!-- VAT Number -->
               <div>
                  <label for="vat_number" class="block text-sm font-medium text-gray-700 mb-2">
                     VAT Number
                  </label>
                  <input
                     id="vat_number"
                     v-model="formData.vat_number"
                     type="text"
                     placeholder="FR12345678901"
                     class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
               </div>

               <!-- SIRET -->
               <div>
                  <label for="siret" class="block text-sm font-medium text-gray-700 mb-2">
                     SIRET
                  </label>
                  <input
                     id="siret"
                     v-model="formData.siret"
                     type="text"
                     placeholder="12345678901234"
                     class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
               </div>

               <!-- Address Line 1 -->
               <div>
                  <label for="address_line1" class="block text-sm font-medium text-gray-700 mb-2">
                     Address Line 1
                  </label>
                  <input
                     id="address_line1"
                     v-model="formData.address_line1"
                     type="text"
                     placeholder="Street address"
                     class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
               </div>

               <!-- Address Line 2 -->
               <div>
                  <label for="address_line2" class="block text-sm font-medium text-gray-700 mb-2">
                     Address Line 2
                  </label>
                  <input
                     id="address_line2"
                     v-model="formData.address_line2"
                     type="text"
                     placeholder="Apartment, suite, etc. (optional)"
                     class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
               </div>

               <!-- Postal Code -->
               <div>
                  <label for="postal_code" class="block text-sm font-medium text-gray-700 mb-2">
                     Postal Code
                  </label>
                  <input
                     id="postal_code"
                     v-model="formData.postal_code"
                     type="text"
                     placeholder="75001"
                     class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
               </div>

               <!-- City -->
               <div>
                  <label for="city" class="block text-sm font-medium text-gray-700 mb-2">
                     City
                  </label>
                  <input
                     id="city"
                     v-model="formData.city"
                     type="text"
                     placeholder="Paris"
                     class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
               </div>

               <!-- Country Code -->
               <div>
                  <label for="country_code" class="block text-sm font-medium text-gray-700 mb-2">
                     Country Code
                  </label>
                  <input
                     id="country_code"
                     v-model="formData.country_code"
                     type="text"
                     maxlength="2"
                     placeholder="FR"
                     class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
               </div>

               <!-- Payment Terms Default -->
               <div>
                  <label
                     for="payment_terms_default"
                     class="block text-sm font-medium text-gray-700 mb-2"
                  >
                     Default Payment Terms
                  </label>
                  <input
                     id="payment_terms_default"
                     v-model="formData.payment_terms_default"
                     type="text"
                     placeholder="e.g., 30 days EOM"
                     class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
               </div>

               <!-- Form Actions -->
               <div class="flex gap-4 pt-6 border-t">
                  <button
                     type="submit"
                     :disabled="isSaving"
                     class="px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg font-medium"
                  >
                     {{ isSaving ? 'Saving...' : isNewAccount ? 'Create' : 'Update' }}
                  </button>
                  <router-link
                     to="/accounts"
                     class="px-6 py-2 bg-gray-200 hover:bg-gray-300 text-gray-900 rounded-lg font-medium"
                  >
                     Cancel
                  </router-link>
               </div>
            </form>
         </div>
      </div>
   </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { createAccount, deleteAccount, getAccount, updateAccount } from '../../api/account';
import { useAuth } from '../../stores/auth';
import AccountNavHeader from './AccountNavHeader.vue';

const router = useRouter();
const route = useRoute();
useAuth();

const isNewAccount = computed(() => route.params.id === 'new');
const accountId = computed(() => (isNewAccount.value ? null : (route.params.id as string)));

const isLoading = ref(false);
const isSaving = ref(false);
const isDeleting = ref(false);
const errorMessage = ref('');
const successMessage = ref('');

interface FormData {
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

const formData = ref<FormData>({
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

const loadAccount = async () => {
   if (isNewAccount.value) {
      isLoading.value = false;
      return;
   }

   if (!accountId.value) {
      isLoading.value = false;
      errorMessage.value = 'Missing account id';
      return;
   }

   isLoading.value = true;
   errorMessage.value = '';

   try {
      const account = await getAccount(accountId.value);
      formData.value = {
         name: account.name || '',
         vat_number: account.vat_number || '',
         siret: account.siret || '',
         address_line1: account.address_line1 || '',
         address_line2: account.address_line2 || '',
         postal_code: account.postal_code || '',
         city: account.city || '',
         country_code: account.country_code || 'FR',
         payment_terms_default: account.payment_terms_default || '',
      };
   } catch (error) {
      errorMessage.value = `Error: ${error instanceof Error ? error.message : 'Unknown error'}`;
   } finally {
      isLoading.value = false;
   }
};

const handleSave = async () => {
   isSaving.value = true;
   errorMessage.value = '';
   successMessage.value = '';

   try {
      if (!formData.value.name) {
         errorMessage.value = 'Company name is required';
         return;
      }

      const accountData = {
         name: formData.value.name,
         vat_number: formData.value.vat_number || null,
         siret: formData.value.siret || null,
         address_line1: formData.value.address_line1 || null,
         address_line2: formData.value.address_line2 || null,
         postal_code: formData.value.postal_code || null,
         city: formData.value.city || null,
         country_code: formData.value.country_code || 'FR',
         payment_terms_default: formData.value.payment_terms_default || null,
         updated_at: new Date().toISOString(),
      };

      if (isNewAccount.value) {
         const created = await createAccount(accountData);
         if (created?.id) {
            successMessage.value = 'Account created successfully';
            setTimeout(() => {
               router.push('/accounts');
            }, 1500);
         }
      } else {
         // Update existing account
         if (!accountId.value) {
            errorMessage.value = 'Missing account id';
            return;
         }
         await updateAccount(accountId.value, accountData);

         successMessage.value = 'Account updated successfully';
         setTimeout(() => {
            successMessage.value = '';
         }, 3000);
      }
   } catch (error) {
      errorMessage.value = `Error: ${error instanceof Error ? error.message : 'Unknown error'}`;
   } finally {
      isSaving.value = false;
   }
};

const handleDelete = async () => {
   if (!confirm('Are you sure you want to delete this account? This action cannot be undone.')) {
      return;
   }

   isDeleting.value = true;
   errorMessage.value = '';

   try {
      if (!accountId.value) {
         errorMessage.value = 'Missing account id';
         return;
      }
      await deleteAccount(accountId.value);

      successMessage.value = 'Account deleted successfully';
      setTimeout(() => {
         router.push('/accounts');
      }, 1500);
   } catch (error) {
      errorMessage.value = `Error: ${error instanceof Error ? error.message : 'Unknown error'}`;
   } finally {
      isDeleting.value = false;
   }
};

onMounted(() => {
   loadAccount();
});
</script>
