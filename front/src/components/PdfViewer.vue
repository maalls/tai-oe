<template>
   <div class="flex flex-col w-full h-full bg-white rounded-lg shadow">
      <!-- Error Message -->
      <div v-if="errorMessage" class="p-3 bg-red-50 border-b border-red-200 text-red-700 text-sm">
         {{ errorMessage }}
      </div>

      <!-- PDF Container -->
      <div class="relative overflow-auto bg-gray-50" style="flex: 1; min-height: 0">
         <!-- PDF iframe with blob URL to prevent browser auto-download -->
         <iframe
            v-if="blobUrl"
            :src="`${blobUrl}#toolbar=1&navpanes=0&scrollbar=1&zoom=page-fit`"
            class="w-full h-full border-0"
            style="min-height: 100%"
         />
         <div v-else class="flex items-center justify-center h-full text-gray-400">
            Loading PDF...
         </div>
      </div>
   </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import { useAuth } from '../stores/auth';

interface Props {
   pdfUrl: string;
}

const props = defineProps<Props>();
const { session } = useAuth();

const errorMessage = ref('');
const blobUrl = ref<string>('');

// Fetch PDF as blob and create a local blob URL to prevent browser auto-download
const loadPdfAsBlob = async () => {
   try {
      errorMessage.value = '';
      if (!props.pdfUrl) return;

      const headers: HeadersInit = {};
      if (session.value?.access_token) {
         headers['Authorization'] = `Bearer ${session.value.access_token}`;
      }

      const response = await fetch(props.pdfUrl, { headers });
      if (!response.ok) {
         errorMessage.value = `Failed to load PDF: ${response.statusText}`;
         return;
      }

      const blob = await response.blob();
      // Create a blob URL that the iframe can use
      // This prevents the browser from auto-downloading the PDF
      if (blobUrl.value) {
         URL.revokeObjectURL(blobUrl.value);
      }
      blobUrl.value = URL.createObjectURL(blob);
   } catch (error) {
      errorMessage.value = `Error loading PDF: ${error instanceof Error ? error.message : String(error)}`;
   }
};

onMounted(() => {
   loadPdfAsBlob();
});

watch(
   () => props.pdfUrl,
   () => {
      loadPdfAsBlob();
   }
);
</script>

<style scoped>
/* No additional styles needed */
</style>
