<template>
   <div>
      <AccountNavHeader>
         <template #actions>
            <router-link
               to="/accounts/new"
               class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium text-sm"
            >
               {{ t('accounts.createAccount') }}
            </router-link>
         </template>
      </AccountNavHeader>
      <div class="p-6">
         <div class="mb-6">
            <div>
               <h1 class="text-3xl font-bold text-gray-900">{{ t('accounts.title') }}</h1>
               <p class="text-gray-600 mt-2">{{ t('accounts.subtitle') }}</p>
            </div>
         </div>

         <!-- Error Message -->
         <div v-if="errorMessage" class="mb-4 p-4 bg-red-100 text-red-700 rounded-lg">
            {{ errorMessage }}
         </div>

         <!-- Loading State -->
         <div v-if="isLoading" class="flex justify-center items-center py-12">
            <div class="text-gray-500">{{ t('accounts.loading') }}</div>
         </div>

         <!-- Accounts Table -->
         <div v-else class="bg-white rounded-lg shadow overflow-hidden">
            <div v-if="accounts.length === 0" class="p-6 text-center text-gray-500">
               {{ t('accounts.empty') }}
            </div>
            <table v-else class="w-full">
               <thead class="bg-gray-50 border-b">
                  <tr>
                     <th class="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">
                        {{ t('accounts.columns.name') }}
                     </th>
                     <th class="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">
                        {{ t('accounts.columns.vatNumber') }}
                     </th>
                     <th class="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">
                        {{ t('accounts.columns.siret') }}
                     </th>
                     <th class="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">
                        {{ t('accounts.columns.city') }}
                     </th>
                     <th class="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">
                        {{ t('accounts.columns.country') }}
                     </th>
                     <th class="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">
                        {{ t('accounts.columns.created') }}
                     </th>
                  </tr>
               </thead>
               <tbody class="divide-y">
                  <tr
                     v-for="account in accounts"
                     :key="account.id"
                     @click="goToDetail(account.id)"
                     class="hover:bg-gray-50 transition-colors cursor-pointer"
                  >
                     <td class="px-6 py-4 text-sm font-medium text-gray-900">
                        {{ account.name }}
                     </td>
                     <td class="px-6 py-4 text-sm text-gray-600">
                        {{ account.vat_number || '-' }}
                     </td>
                     <td class="px-6 py-4 text-sm text-gray-600">
                        {{ account.siret || '-' }}
                     </td>
                     <td class="px-6 py-4 text-sm text-gray-600">
                        {{ account.city || '-' }}
                     </td>
                     <td class="px-6 py-4 text-sm text-gray-600">
                        {{ account.country_code || 'FR' }}
                     </td>
                     <td class="px-6 py-4 text-sm text-gray-600">
                        {{ formatDate(account.created_at) }}
                     </td>
                  </tr>
               </tbody>
            </table>
         </div>
      </div>
   </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { supabase } from '../../lib/supabase';
import { useAuth } from '../../stores/auth';
import AccountNavHeader from './AccountNavHeader.vue';
import { useI18n } from '../../i18n/useI18n';

interface Account {
   id: string;
   name: string;
   vat_number?: string;
   siret?: string;
   address_line1?: string;
   address_line2?: string;
   postal_code?: string;
   city?: string;
   country_code?: string;
   payment_terms_default?: string;
   created_at: string;
   updated_at: string;
}

const accounts = ref<Account[]>([]);
const isLoading = ref(false);
const errorMessage = ref('');
const { user } = useAuth();
const router = useRouter();
const { t } = useI18n();

const formatDate = (dateString: string) => {
   try {
      return new Date(dateString).toLocaleDateString('en-US', {
         year: 'numeric',
         month: 'short',
         day: 'numeric',
      });
   } catch {
      return dateString;
   }
};

const loadAccounts = async () => {
   isLoading.value = true;
   errorMessage.value = '';

   try {
      if (!user.value?.id) {
         errorMessage.value = t('accounts.errors.notAuthenticated');
         return;
      }

      const { data, error } = await supabase
         .from('account')
         .select('*')
         .order('created_at', { ascending: false });

      if (error) {
         // Ignore AbortError - it happens when component unmounts during fetch
         if (error.message.includes('abort')) {
            console.warn('[AccountPage] Request aborted, likely due to navigation');
            return;
         }
         errorMessage.value = `${t('accounts.errors.loadFailed')}: ${error.message}`;
         console.error('[AccountPage] Error:', error);
         return;
      }

      accounts.value = data || [];
      console.log('[AccountPage] Loaded accounts:', accounts.value.length);
   } catch (error) {
      // Ignore AbortError - it happens when component unmounts during fetch
      if (error instanceof Error && error.message.includes('abort')) {
         console.warn('[AccountPage] Request aborted, likely due to navigation');
         return;
      }
      errorMessage.value = `${t('accounts.errors.unexpected')}: ${
         error instanceof Error ? error.message : t('accounts.errors.unknown')
      }`;
      console.error('[AccountPage] Unexpected error:', error);
   } finally {
      isLoading.value = false;
   }
};

onMounted(() => {
   loadAccounts();
});

const goToDetail = (id: string) => {
   router.push(`/accounts/${id}`);
};
</script>
