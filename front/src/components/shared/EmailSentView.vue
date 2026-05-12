<template>
   <div class="space-y-5">
      <div class="flex items-center justify-between">
         <div class="flex items-center gap-2">
            <span class="inline-flex h-8 w-8 items-center justify-center rounded-full bg-green-50">
               <svg
                  class="w-5 h-5 text-green-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
               >
                  <path
                     stroke-linecap="round"
                     stroke-linejoin="round"
                     stroke-width="2"
                     d="M5 13l4 4L19 7"
                  />
               </svg>
            </span>
            <h3 class="text-xl font-semibold text-gray-900">{{ title }}</h3>
         </div>
         <span v-if="sentAtText" class="text-xs text-gray-500">{{ sentAtText }}</span>
      </div>

      <div v-if="description" class="rounded-lg border border-emerald-100 bg-emerald-50 px-4 py-3">
         <p class="text-sm text-emerald-800">{{ description }}</p>
      </div>

      <div class="rounded-lg border border-gray-100 bg-white">
         <div class="grid grid-cols-1 gap-4 px-4 py-3 sm:grid-cols-2">
            <div>
               <div class="text-xs font-medium uppercase tracking-wide text-gray-400">From</div>
               <div class="mt-1 text-sm text-gray-900">{{ from || '—' }}</div>
            </div>

            <div>
               <div class="text-xs font-medium uppercase tracking-wide text-gray-400">To</div>
               <div class="mt-1 text-sm text-gray-900">{{ to || '—' }}</div>
            </div>

            <div v-if="cc">
               <div class="text-xs font-medium uppercase tracking-wide text-gray-400">CC</div>
               <div class="mt-1 text-sm text-gray-900">{{ cc }}</div>
            </div>

            <div class="sm:col-span-2">
               <div class="text-xs font-medium uppercase tracking-wide text-gray-400">Subject</div>
               <div class="mt-1 text-sm text-gray-900">{{ subject || '—' }}</div>
            </div>
         </div>

         <div class="border-t border-gray-100 px-4 py-3">
            <div class="text-xs font-medium uppercase tracking-wide text-gray-400">Message</div>
            <div class="mt-2 text-sm text-gray-900 whitespace-pre-wrap">
               {{ body || '—' }}
            </div>
         </div>

         <div v-if="attachmentName" class="border-t border-gray-100 px-4 py-3">
            <div class="flex items-center justify-between gap-3 text-sm text-gray-700">
               <div class="flex items-center gap-2">
                  <svg
                     class="w-5 h-5 text-gray-500"
                     fill="none"
                     stroke="currentColor"
                     viewBox="0 0 24 24"
                  >
                     <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13"
                     />
                  </svg>
                  <span class="font-medium">Attachment:</span>
                  <span>{{ attachmentName }}</span>
               </div>

               <button
                  v-if="downloadUrl"
                  @click="handleDownload"
                  class="inline-flex items-center gap-1 rounded-md border border-gray-200 px-2.5 py-1 text-xs font-medium text-gray-700 hover:bg-gray-50"
               >
                  <svg
                     class="h-4 w-4 text-gray-500"
                     fill="none"
                     stroke="currentColor"
                     viewBox="0 0 24 24"
                  >
                     <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M4 16v2a2 2 0 002 2h12a2 2 0 002-2v-2M7 10l5 5m0 0l5-5m-5 5V4"
                     />
                  </svg>
                  Download
               </button>
            </div>
         </div>
      </div>
   </div>
</template>

<script setup lang="ts">
const props = defineProps<{
   title: string;
   description?: string;
   from?: string;
   to?: string;
   cc?: string;
   subject?: string;
   body?: string;
   attachmentName?: string;
   downloadUrl?: string;
   sentAtText?: string;
}>();

const handleDownload = () => {
   if (!props.downloadUrl) return;

   // Create a temporary link and trigger download
   const link = document.createElement('a');
   link.href = props.downloadUrl;
   link.download = props.attachmentName || 'download';
   document.body.appendChild(link);
   link.click();
   document.body.removeChild(link);
};
</script>
