<template>
   <div id="message-composer" class="border border-gray-200 p-2 m-1 overflow-visible">
      <form @submit.prevent="sendMessage" class="flex flex-col gap-3 overflow-visible">
         <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
               <input ref="localFileInputRef" type="file" class="hidden" @change="onFileSelected" />
               <button
                  type="button"
                  @click="onTriggerFilePicker"
                  class="p-1 hover:bg-gray-100 rounded text-gray-600"
                  title="Attach file"
               >
                  <svg
                     xmlns="http://www.w3.org/2000/svg"
                     class="h-5 w-5"
                     viewBox="0 0 24 24"
                     fill="none"
                     stroke="currentColor"
                     stroke-width="1.5"
                     stroke-linecap="round"
                     stroke-linejoin="round"
                  >
                     <path
                        d="M21.44 11.05l-9.19 9.19a6 6 0 11-8.49-8.49l10.6-10.6a4 4 0 015.66 5.66l-10.6 10.6a2 2 0 01-2.83-2.83l9.19-9.19"
                     />
                  </svg>
               </button>
               <div v-if="selectedFile" class="flex items-center gap-2 min-w-0">
                  <span class="text-xs text-gray-700 truncate max-w-[220px]">
                     {{ formatAttachmentName(selectedFile) }}
                  </span>
                  <span class="text-xs text-gray-400">
                     {{ formatFileSize(selectedFile.size) }}
                  </span>
                  <button
                     type="button"
                     class="p-1 text-gray-400 hover:text-gray-600"
                     @click="onClearSelectedFile"
                     title="Remove attachment"
                  >
                     <svg
                        xmlns="http://www.w3.org/2000/svg"
                        class="h-3.5 w-3.5"
                        viewBox="0 0 20 20"
                        fill="currentColor"
                     >
                        <path
                           fill-rule="evenodd"
                           d="M10 8.586 4.293 2.879a1 1 0 0 0-1.414 1.414L8.586 10l-5.707 5.707a1 1 0 1 0 1.414 1.414L10 11.414l5.707 5.707a1 1 0 0 0 1.414-1.414L11.414 10l5.707-5.707a1 1 0 0 0-1.414-1.414L10 8.586Z"
                           clip-rule="evenodd"
                        />
                     </svg>
                  </button>
               </div>
            </div>
            <div class="relative" ref="localMenuContainerRef">
               <button
                  @click="emit('update:menuOpen', !menuOpen)"
                  class="p-1 hover:bg-gray-100 rounded text-gray-600"
                  type="button"
               >
                  <svg
                     xmlns="http://www.w3.org/2000/svg"
                     class="h-5 w-5"
                     viewBox="0 0 20 20"
                     fill="currentColor"
                  >
                     <path
                        d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z"
                     />
                  </svg>
               </button>
               <div
                  v-if="menuOpen"
                  class="absolute right-0 bottom-full mb-2 w-48 bg-white rounded-md shadow-lg border border-gray-200 z-30"
               >
                  <button
                     @click="
                        clearChat();
                        emit('update:menuOpen', false);
                     "
                     class="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-md"
                  >
                     Clear Chat
                  </button>
                  <button
                     type="button"
                     @click="
                        emit('update:showContextPayload', !showContextPayload);
                        emit('update:menuOpen', false);
                     "
                     class="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-md"
                  >
                     {{ showContextPayload ? 'Hide Context' : 'Show Context' }}
                  </button>
                  <button
                     type="button"
                     @click="
                        emit('update:showDebugPanel', !showDebugPanel);
                        emit('update:menuOpen', false);
                     "
                     class="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-md"
                  >
                     {{ showDebugPanel ? 'Disable Debug' : 'Enable Debug' }}
                  </button>
               </div>
            </div>
         </div>
         <div class="flex gap-3 items-end">
            <textarea
               :value="modelValue"
               rows="2"
               class="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
               :placeholder="placeholder"
               @input="onInput"
               @keydown.enter.exact.prevent="isSourceChat ? sendMessage() : undefined"
            ></textarea>
            <button
               v-if="!isSourceChat"
               type="submit"
               :disabled="loading || isUploading || (!modelValue.trim() && !selectedFile)"
               class="px-4 py-2 bg-blue-600 text-white rounded-md disabled:opacity-50"
            >
               {{ isUploading ? 'Uploading...' : 'Send' }}
            </button>
         </div>
      </form>
      <div v-if="fileError" class="mt-2 text-sm text-red-600">{{ fileError }}</div>
      <div v-if="error" class="mt-2 text-sm text-red-600">{{ error }}</div>
   </div>
</template>

<script setup lang="ts">
import { ref, watchEffect } from 'vue';
const props = defineProps<{
   modelValue: string;
   placeholder?: string;
   isSourceChat: boolean;
   loading: boolean;
   isUploading: boolean;
   selectedFile: File | null;
   fileError: string;
   error: string;
   menuOpen: boolean;
   showContextPayload: boolean;
   showDebugPanel: boolean;
   fileInputRef: any;
   menuContainer: any;
   sendMessage: () => void;
   triggerFilePicker: () => void;
   onFileSelected: (event: Event) => void;
   clearSelectedFile: () => void;
   formatFileSize: (size: number) => string;
   clearChat: () => void;
}>();

const emit = defineEmits<{
   (e: 'update:modelValue', value: string): void;
   (e: 'update:menuOpen', value: boolean): void;
   (e: 'update:showContextPayload', value: boolean): void;
   (e: 'update:showDebugPanel', value: boolean): void;
}>();

const localFileInputRef = ref<HTMLInputElement | null>(null);
const localMenuContainerRef = ref<HTMLElement | null>(null);

watchEffect(() => {
   if (props.fileInputRef && 'value' in props.fileInputRef) {
      props.fileInputRef.value = localFileInputRef.value;
   }
   if (props.menuContainer && 'value' in props.menuContainer) {
      props.menuContainer.value = localMenuContainerRef.value;
   }
});

const onInput = (event: Event) => {
   const target = event.target as HTMLTextAreaElement;
   emit('update:modelValue', target.value);
};

const onTriggerFilePicker = () => {
   if (localFileInputRef.value) {
      localFileInputRef.value.click();
      return;
   }
   props.triggerFilePicker();
};

const onClearSelectedFile = () => {
   props.clearSelectedFile();
   if (localFileInputRef.value) {
      localFileInputRef.value.value = '';
   }
};

const formatAttachmentName = (file: File | null) => {
   if (!file) return '';
   const name = file.name || '';
   const lastDot = name.lastIndexOf('.');
   if (lastDot <= 0) {
      return name.length > 24 ? `${name.slice(0, 21)}…` : name;
   }
   const base = name.slice(0, lastDot);
   const ext = name.slice(lastDot);
   const maxBase = 22;
   if (base.length <= maxBase) {
      return `${base}${ext}`;
   }
   return `${base.slice(0, maxBase - 1)}…${ext}`;
};
</script>
