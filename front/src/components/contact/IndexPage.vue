<template>
   <div>
      <AccountNavHeader>
         <template #actions>
            <button @click="loadContacts" :disabled="isLoading" class="btn btn-neutral">
               🔄 Refresh
            </button>
            <router-link to="/contacts/new" class="btn btn-primary"> + Add Contact </router-link>
         </template>
      </AccountNavHeader>
      <div class="p-6">
         <div class="mb-6">
            <h1 class="text-3xl font-bold text-gray-900">Contacts</h1>
            <p class="text-gray-600 mt-2">Manage your contacts</p>
         </div>

         <!-- Error Message -->
         <div v-if="errorMessage" class="mb-4 p-4 bg-red-100 text-red-700 rounded-lg">
            {{ errorMessage }}
         </div>

         <!-- Loading State -->
         <div v-if="isLoading" class="flex justify-center items-center py-12">
            <div class="text-gray-500">Loading contacts...</div>
         </div>

         <!-- Contacts Table -->
         <div v-else class="bg-white rounded-lg shadow overflow-hidden">
            <div v-if="contacts.length === 0" class="p-6 text-center text-gray-500">
               No contacts found
            </div>
            <div v-else class="w-full">
               <table class="w-full table-fixed">
                  <thead class="bg-gray-50 border-b">
                     <tr>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">
                           Name
                        </th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">
                           Email
                        </th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">
                           Phone
                        </th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">
                           Title
                        </th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">
                           Account
                        </th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">
                           Created
                        </th>
                     </tr>
                  </thead>
                  <tbody class="divide-y">
                     <tr
                        v-for="contact in contacts"
                        :key="contact.id"
                        @click="goToDetail(contact.id)"
                        class="hover:bg-gray-50 transition-colors cursor-pointer"
                     >
                        <td class="px-6 py-4 text-sm font-medium text-gray-900 wrap-break-word">
                           {{ contact.name }}
                        </td>
                        <td class="px-6 py-4 text-sm text-gray-600 wrap-break-word">
                           {{ contact.email || '-' }}
                        </td>
                        <td class="px-6 py-4 text-sm text-gray-600 wrap-break-word">
                           {{ contact.phone || '-' }}
                        </td>
                        <td class="px-6 py-4 text-sm text-gray-600 wrap-break-word">
                           {{ contact.role_title || '-' }}
                        </td>
                        <td class="px-6 py-4 text-sm text-gray-600 wrap-break-word">
                           {{ contact.account?.name || '-' }}
                        </td>
                        <td class="px-6 py-4 text-sm text-gray-600 wrap-break-word">
                           {{ formatDate(contact.created_at) }}
                        </td>
                     </tr>
                  </tbody>
               </table>
            </div>
         </div>
      </div>
   </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { supabase } from '../../lib/supabase';
import AccountNavHeader from '../account/AccountNavHeader.vue';

interface Contact {
   id: string;
   name: string;
   email?: string;
   phone?: string;
   role_title?: string;
   created_at?: string;
   account_id: string;
   account?: {
      id: string;
      name: string;
   };
}

const contacts = ref<Contact[]>([]);
const isLoading = ref(false);
const errorMessage = ref('');
const router = useRouter();
const pageSize = 50; // Increased page size to load more contacts

const loadContacts = async () => {
   isLoading.value = true;
   errorMessage.value = '';

   try {
      // Load contacts ordered by created_at DESC to show newest first
      const { data, error } = await supabase
         .from('contact')
         .select('*, account:account_id(id, name)')
         .order('created_at', { ascending: false })
         .limit(pageSize);

      if (error) {
         errorMessage.value = `Failed to load contacts: ${error.message}`;
         console.error('[ContactPage] Error:', error);
         return;
      }

      contacts.value = data || [];
      console.log('[ContactPage] Loaded contacts:', contacts.value.length);
   } catch (error) {
      errorMessage.value = `Error: ${error instanceof Error ? error.message : 'Unknown error'}`;
      console.error('[ContactPage] Unexpected error:', error);
   } finally {
      isLoading.value = false;
   }
};

const goToDetail = (id: string) => {
   router.push(`/contacts/${id}`);
};

const formatDate = (dateString?: string) => {
   if (!dateString) return '-';
   const date = new Date(dateString);
   return new Intl.DateTimeFormat('fr-FR', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
   }).format(date);
};

onMounted(() => {
   loadContacts();
});
</script>
