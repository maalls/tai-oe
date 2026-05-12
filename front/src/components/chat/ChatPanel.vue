<template>
   <div class="flex flex-col h-full min-h-0">
      <div class="bg-white shadow p-0 overflow-hidden flex-1 flex flex-col min-h-0 relative">
         <div
            v-if="isCollapsed"
            class="flex flex-col items-start h-full cursor-pointer border-b border-gray-200 pt-2 pl-2 hover:bg-gray-100 rounded-md"
            @click="toggleCollapsed()"
         >
            <button
               type="button"
               class="p-1 hover:bg-gray-100 rounded text-gray-600 cursor-pointer"
               @click.stop="toggleCollapsed"
               title="Toggle chat"
            >
               <img src="/favicon.png" alt="Chat" class="h-4 w-4" />
            </button>
         </div>

         <button
            v-else
            type="button"
            class="absolute top-2 left-2 p-1 hover:bg-gray-100 rounded text-gray-600 z-10 cursor-pointer"
            @click.stop="toggleCollapsed"
            title="Toggle chat"
         >
            <img src="/favicon.png" alt="Chat" class="h-4 w-4" />
         </button>

         <!-- Messages -->
         <div
            v-if="!isCollapsed"
            class="flex-1 overflow-y-auto p-6 space-y-4 min-h-0"
            ref="scrollContainer"
         >
            <div
               v-for="(m, idx) in messages"
               :key="idx"
               class="flex"
               :class="m.role === 'user' ? 'justify-end' : 'justify-start'"
            >
               <div
                  class="max-w-[75%] px-4 py-2 rounded-2xl text-sm whitespace-pre-wrap"
                  :class="
                     m.role === 'user'
                        ? 'bg-blue-600 text-white rounded-br-none'
                        : m.role === 'tool'
                          ? 'bg-purple-50 text-purple-900 border border-purple-200 rounded-bl-none'
                          : 'bg-gray-100 text-gray-900 rounded-bl-none'
                  "
               >
                  <div
                     v-if="m.role === 'tool'"
                     class="overflow-x-auto max-h-24 text-xs font-semibold mb-1"
                  >
                     Tool: {{ m.name }}
                     <div
                        v-if="m.tool_arguments"
                        class="font-normal text-purple-700 mt-1 message-tool"
                     ></div>
                  </div>
                  <div v-if="m.role === 'tool'" class="max-h-24 overflow-y-auto">
                     <pre class="text-xs">
                        
                        {{ formatToolContent(m.tool_arguments ?? null) }}<br />
                        {{ formatToolContent(m.content) }}
                     </pre>
                  </div>
                  <div
                     v-else-if="
                        getDisplayContent(m.content) &&
                        getDisplayContent(m.content).includes('<table')
                     "
                     v-html="getDisplayContent(m.content)"
                  ></div>
                  <div
                     v-else-if="getDisplayContent(m.content)"
                     v-html="renderMarkdown(getDisplayContent(m.content))"
                  ></div>
               </div>
            </div>
            <div v-if="loading" class="flex justify-start">
               <div class="px-4 py-2 bg-gray-100 text-gray-500 rounded-2xl text-sm rounded-bl-none">
                  Thinking...
               </div>
            </div>
         </div>

         <Composer
            v-if="!isCollapsed"
            v-model="userInput"
            :placeholder="placeholder"
            :isSourceChat="isSourceChat"
            :loading="loading"
            :isUploading="isUploading"
            :selectedFile="selectedFile"
            :fileError="fileError"
            :error="error"
            :menuOpen="isMenuOpen"
            :showContextPayload="showContextPayload"
            :showDebugPanel="showDebugPanel"
            :fileInputRef="fileInputRef"
            :menuContainer="menuContainer"
            :sendMessage="sendMessage"
            :triggerFilePicker="triggerFilePicker"
            :onFileSelected="onFileSelected"
            :clearSelectedFile="clearSelectedFile"
            :formatFileSize="formatFileSize"
            :clearChat="clearChat"
            @update:menuOpen="isMenuOpen = $event"
            @update:showContextPayload="showContextPayload = $event"
            @update:showDebugPanel="showDebugPanel = $event"
         />
      </div>

      <!-- Debug Panel -->
      <details
         v-if="showDebugPanel && !isCollapsed"
         class="mt-1 bg-white rounded-lg shadow p-2 flex-shrink-0"
      >
         <summary class="text-xs text-gray-600 cursor-pointer select-none">Debug</summary>

         <div class="grid grid-cols-1 gap-3 mt-3">
            <div>
               <pre
                  class="bg-gray-50 border border-gray-200 rounded p-2 text-xs whitespace-pre-wrap"
               ><strong>System Prompt</strong>: {{ getSystemPromptDisplay() }}</pre>
            </div>

            <div>
               <div class="text-xs font-semibold text-gray-600 mb-1">Context</div>
               <pre
                  class="bg-gray-50 border border-gray-200 rounded p-2 text-xs whitespace-pre-wrap"
                  >{{ JSON.stringify(props.context ?? {}, null, 2) }}</pre
               >
            </div>

            <div>
               <div class="text-xs font-semibold text-gray-600 mb-1">Tools</div>
               <pre
                  class="bg-gray-50 border border-gray-200 rounded p-2 text-xs whitespace-pre-wrap"
                  >{{ toolPrompt }}</pre
               >
            </div>

            <div>
               <div class="text-xs font-semibold text-gray-600 mb-1">Model</div>
               <div
                  class="text-xs text-gray-800 bg-gray-50 border border-gray-200 rounded px-2 py-1"
               >
                  {{ model || '—' }}
               </div>
            </div>
         </div>
      </details>
   </div>
</template>

<script setup lang="ts">
import { computed, watch } from 'vue';
import { CHAT_TOOLS } from './tools';
import Composer from '../Composer/Index.vue';
import { formatToolContent } from './utils';
import { useChatPanel } from './ChatPanel';

const props = withDefaults(
   defineProps<{
      context?: Record<string, any>;
      modelName?: string;
      placeholder?: string;
      showModelSelector?: boolean;
      systemPrompt?: string;
      collapsed?: boolean;
      forceOpen?: boolean;
   }>(),
   {
      placeholder: 'Ask a question...',
      showModelSelector: false,
      forceOpen: false,
   }
);

const emit = defineEmits<{ (e: 'update:collapsed', value: boolean): void }>();

const isSourceChat = computed(() => props.context?.section === 'source');

const {
   userInput,
   model,
   scrollContainer,
   isMenuOpen,
   showContextPayload,
   showDebugPanel,
   menuContainer,
   fileInputRef,
   selectedFile,
   fileError,
   isUploading,
   isCollapsed,
   triggerFilePicker,
   onFileSelected,
   clearSelectedFile,
   formatFileSize,
   getDisplayContent,
   renderMarkdown,
   getSystemPromptDisplay,
   messages,
   loading,
   error,
   sendMessage,
   clearChat,
   runTrackedElementsTool,
} = useChatPanel(props);

// Kept to preserve template ref binding for auto-scroll behavior.
void scrollContainer;

const toggleCollapsed = () => {
   if (props.forceOpen) {
      isCollapsed.value = false;
      emit('update:collapsed', false);
      return;
   }
   const next = !isCollapsed.value;
   isCollapsed.value = next;
   emit('update:collapsed', next);
};

watch(isCollapsed, (value) => {
   emit('update:collapsed', value);
});

const toolPrompt = JSON.stringify(CHAT_TOOLS, null, 2);

defineExpose({
   runTrackedElementsTool,
});
</script>
