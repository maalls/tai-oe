<template>
   <div>
      <AccountNavHeader />
      <div class="p-6">
         <div class="mb-6">
            <!-- Breadcrumb -->
            <div class="flex items-center justify-between mb-4">
               <nav class="text-sm text-gray-600">
                  <router-link to="/contacts" class="hover:text-gray-900"> Contacts </router-link>
                  <span class="mx-2">/</span>
                  <span class="text-gray-900">
                     {{ isNew ? 'New Contact' : contactData?.name || '#' + contactId }}
                  </span>
               </nav>
               <button
                  v-if="!isNew"
                  @click="deleteContact"
                  :disabled="isDeleting"
                  class="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium text-sm disabled:bg-gray-400"
               >
                  {{ isDeleting ? 'Deleting...' : 'Delete' }}
               </button>
            </div>
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
         <div v-else class="bg-white rounded-lg shadow p-6">
            <form @submit.prevent="saveContact" class="space-y-6">
               <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <!-- Name -->
                  <div>
                     <label class="block text-sm font-medium text-gray-700 mb-2"> Name * </label>
                     <input
                        v-model="formData.name"
                        type="text"
                        required
                        placeholder="John Doe"
                        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                     />
                  </div>

                  <!-- Email -->
                  <div>
                     <label class="block text-sm font-medium text-gray-700 mb-2"> Email </label>
                     <input
                        v-model="formData.email"
                        type="email"
                        placeholder="john@example.com"
                        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                     />
                  </div>

                  <!-- Phone -->
                  <div>
                     <label class="block text-sm font-medium text-gray-700 mb-2"> Phone </label>
                     <input
                        v-model="formData.phone"
                        type="tel"
                        placeholder="+1 (555) 000-0000"
                        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                     />
                  </div>

                  <!-- Title -->
                  <div>
                     <label class="block text-sm font-medium text-gray-700 mb-2"> Title </label>
                     <input
                        v-model="formData.role_title"
                        type="text"
                        placeholder="Sales Manager"
                        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                     />
                  </div>

                  <!-- Account -->
                  <div class="md:col-span-2">
                     <label class="block text-sm font-medium text-gray-700 mb-2"> Account * </label>
                     <select
                        v-model="formData.account_id"
                        required
                        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                     >
                        <option value="">Select an account...</option>
                        <option v-for="account in accounts" :key="account.id" :value="account.id">
                           {{ account.name }}
                        </option>
                     </select>
                  </div>
               </div>

               <!-- Buttons -->
               <div class="flex gap-3 pt-4">
                  <button
                     type="submit"
                     :disabled="isSaving"
                     class="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium disabled:bg-gray-400"
                  >
                     {{ isSaving ? 'Saving...' : 'Save Contact' }}
                  </button>
                  <router-link
                     to="/contacts"
                     class="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
                  >
                     Cancel
                  </router-link>
               </div>
            </form>
         </div>

         <!-- Relationships -->
         <div v-if="!isNew" class="mt-6 grid grid-cols-1 lg:grid-cols-2 gap-6">
            <!-- Account Relationship -->
            <div class="bg-white rounded-lg shadow p-6">
               <h3 class="text-sm font-semibold text-gray-900 mb-3">Account</h3>
               <div v-if="contactAccount" class="flex items-center justify-between">
                  <div>
                     <p class="text-sm text-gray-900">{{ contactAccount.name }}</p>
                     <p class="text-xs text-gray-600">ID: {{ contactAccount.id }}</p>
                  </div>
                  <router-link
                     :to="`/accounts/${contactAccount.id}`"
                     class="text-xs px-3 py-1.5 border border-gray-300 rounded hover:bg-gray-50 text-gray-700"
                  >
                     View Account
                  </router-link>
               </div>
               <div v-else class="text-sm text-gray-500">No account linked.</div>
            </div>

            <!-- Opportunities Relationship -->
            <div class="bg-white rounded-lg shadow p-6">
               <h3 class="text-sm font-semibold text-gray-900 mb-3">Opportunities</h3>
               <div v-if="relatedOpps.length > 0" class="space-y-2">
                  <div
                     v-for="opp in relatedOpps"
                     :key="opp.id"
                     class="flex items-center justify-between p-3 rounded border border-gray-200"
                  >
                     <div>
                        <p class="text-sm font-medium text-gray-900">{{ opp.name }}</p>
                        <p class="text-xs text-gray-600">
                           Role: {{ formatRole(opp.role) }} • Stage: {{ formatStage(opp.stage) }}
                        </p>
                     </div>
                     <router-link
                        :to="`/opportunities/${opp.id}/pipeline`"
                        class="text-xs px-3 py-1.5 border border-gray-300 rounded hover:bg-gray-50 text-gray-700"
                     >
                        Open
                     </router-link>
                  </div>
               </div>
               <div v-else class="text-sm text-gray-500">No related opportunities.</div>
            </div>
         </div>
      </div>
   </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { supabase } from '../../lib/supabase';
import {
   createContact,
   deleteContact as deleteContactApi,
   getContact,
   updateContact,
} from '../../api/contact';
import { listAccounts } from '../../api/account';
import AccountNavHeader from '../account/AccountNavHeader.vue';

const route = useRoute();
const router = useRouter();
const contactId = route.params.id as string;
const isNew = contactId === 'new';

const contactData = ref<any>(null);
const accounts = ref<any[]>([]);
const isLoading = ref(false);
const isSaving = ref(false);
const isDeleting = ref(false);
const errorMessage = ref('');
const successMessage = ref('');

const formData = ref({
   name: '',
   email: '',
   phone: '',
   role_title: '',
   account_id: '',
});

const contactAccount = ref<{ id: string; name: string } | null>(null);
const relatedOpps = ref<Array<{ id: string; name: string; stage: string; role: string }>>([]);

const formatStage = (stage: string) =>
   stage
      ?.replace(/_/g, ' ')
      .toLowerCase()
      .replace(/(^|\s)\S/g, (t) => t.toUpperCase());
const formatRole = (role: string) =>
   role
      ?.replace(/_/g, ' ')
      .toLowerCase()
      .replace(/(^|\s)\S/g, (t) => t.toUpperCase());

const loadContact = async () => {
   if (isNew) return;

   isLoading.value = true;
   try {
      const contact = await getContact(contactId);
      contactData.value = contact;
      formData.value = {
         name: contact.name,
         email: contact.email || '',
         phone: contact.phone || '',
         role_title: contact.role_title || '',
         account_id: contact.account_id,
      };
      contactAccount.value =
         contact.account_name && contact.account_id
            ? { id: contact.account_id, name: contact.account_name }
            : null;
      await loadRelatedOpportunities();
   } catch (error) {
      errorMessage.value = `Failed to load contact: ${error instanceof Error ? error.message : 'Unknown error'}`;
   } finally {
      isLoading.value = false;
   }
};

const loadAccounts = async () => {
   try {
      const data = await listAccounts();
      accounts.value = data.map((account) => ({ id: account.id, name: account.name }));
   } catch (error) {
      console.error('Failed to load accounts:', error);
   }
};

const loadRelatedOpportunities = async () => {
   try {
      const { data, error } = await supabase
         .from('opportunity_participant')
         .select('role, opportunity:opportunity_id(id, name, stage)')
         .eq('contact_id', contactId)
         .order('created_at', { ascending: false });

      if (error) throw error;

      relatedOpps.value = (data || [])
         .filter((row: any) => row.opportunity)
         .map((row: any) => ({
            id: row.opportunity.id,
            name: row.opportunity.name,
            stage: row.opportunity.stage,
            role: row.role,
         }));
   } catch (error) {
      console.error('Failed to load related opportunities:', error);
   }
};

const saveContact = async () => {
   if (!formData.value.name || !formData.value.account_id) {
      errorMessage.value = 'Name and Account are required';
      return;
   }

   isSaving.value = true;
   errorMessage.value = '';
   successMessage.value = '';

   try {
      if (isNew) {
         const data = await createContact({
            name: formData.value.name,
            email: formData.value.email || null,
            phone: formData.value.phone || null,
            role_title: formData.value.role_title || null,
            account_id: formData.value.account_id,
         });
         successMessage.value = 'Contact created successfully';
         setTimeout(() => {
            router.push(`/contacts/${(data as any).id}`);
         }, 1000);
      } else {
         await updateContact(contactId, {
            name: formData.value.name,
            email: formData.value.email || null,
            phone: formData.value.phone || null,
            role_title: formData.value.role_title || null,
            account_id: formData.value.account_id,
         });
         successMessage.value = 'Contact updated successfully';
         await loadContact();
      }
   } catch (error) {
      errorMessage.value = `Failed to save contact: ${error instanceof Error ? error.message : 'Unknown error'}`;
   } finally {
      isSaving.value = false;
   }
};

const deleteContact = async () => {
   if (!confirm('Are you sure you want to delete this contact?')) return;

   isDeleting.value = true;
   errorMessage.value = '';

   try {
      await deleteContactApi(contactId);
      successMessage.value = 'Contact deleted successfully';
      setTimeout(() => {
         router.push('/contacts');
      }, 1000);
   } catch (error) {
      errorMessage.value = `Failed to delete contact: ${error instanceof Error ? error.message : 'Unknown error'}`;
   } finally {
      isDeleting.value = false;
   }
};

onMounted(() => {
   loadAccounts();
   // Prefill account from query when creating a new contact
   const qAcc = route.query.account_id as string | undefined;
   if (isNew && qAcc) {
      formData.value.account_id = qAcc;
   }
   loadContact();
});
</script>
