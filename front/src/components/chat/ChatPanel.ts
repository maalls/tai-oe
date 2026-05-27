import { ref, onMounted, nextTick, watch, onUnmounted, toRef } from 'vue';
import { marked } from 'marked';
import DOMPurify from 'dompurify';
import { DEFAULT_MODEL, SYSTEM_MESSAGE } from './types';
import { useChat } from './useChat';
import { executeToolCalls } from './toolExecutor';
import type { ChatMessage } from './types';
import { authFetch } from '../../api/authFetch';

export function useChatPanel(props: {
   context?: Record<string, any>;
   modelName?: string;
   placeholder?: string;
   showModelSelector?: boolean;
   systemPrompt?: string;
   collapsed?: boolean;
   forceOpen?: boolean;
}) {
   const MENU_PREFS_KEY = 'chat.menu.preferences';
   const COLLAPSED_PREFS_KEY = 'chat.collapsed';
   const userInput = ref('');
   const model = ref(props.modelName || DEFAULT_MODEL);
   const scrollContainer = ref<HTMLElement | null>(null);
   const isMenuOpen = ref(false);
   const showContextPayload = ref(false);
   const showDebugPanel = ref(true);
   const menuContainer = ref<HTMLElement | null>(null);
   const fileInputRef = ref<HTMLInputElement | null>(null);
   const selectedFile = ref<File | null>(null);
   const fileError = ref('');
   const isUploading = ref(false);
   const isCollapsed = ref(false);
   let domObserver: MutationObserver | null = null;
   let onDocumentClick: ((event: MouseEvent) => void) | null = null;
   let onCollapsedSync: ((event: Event) => void) | null = null;

   const elements = ref<Array<Record<string, any>>>([]);
   console.log('[ChatPanel] useChatPanel initialized with context:', props.context);

   function loadMenuPreferences() {
      try {
         const raw = localStorage.getItem(MENU_PREFS_KEY);
         if (!raw) return;
         const parsed = JSON.parse(raw) as {
            isMenuOpen?: boolean;
            showContextPayload?: boolean;
            showDebugPanel?: boolean;
         };
         if (typeof parsed.isMenuOpen === 'boolean') {
            isMenuOpen.value = parsed.isMenuOpen;
         }
         if (typeof parsed.showContextPayload === 'boolean') {
            showContextPayload.value = parsed.showContextPayload;
         }
         if (typeof parsed.showDebugPanel === 'boolean') {
            showDebugPanel.value = parsed.showDebugPanel;
         }
      } catch (error) {
         console.warn('[ChatPanel] Failed to load menu preferences:', error);
      }
   }

   function loadCollapsedPreference() {
      try {
         if (props.forceOpen) {
            isCollapsed.value = false;
            return;
         }
         const raw = localStorage.getItem(COLLAPSED_PREFS_KEY);
         if (raw === null) {
            isCollapsed.value = !!props.collapsed;
            return;
         }
         isCollapsed.value = raw === 'true';
      } catch (error) {
         console.warn('[ChatPanel] Failed to load collapsed preference:', error);
         isCollapsed.value = !!props.collapsed;
      }
   }

   function saveCollapsedPreference(value: boolean) {
      try {
         localStorage.setItem(COLLAPSED_PREFS_KEY, String(value));
      } catch (error) {
         console.warn('[ChatPanel] Failed to save collapsed preference:', error);
      }
   }

   function saveMenuPreferences() {
      try {
         localStorage.setItem(
            MENU_PREFS_KEY,
            JSON.stringify({
               isMenuOpen: isMenuOpen.value,
               showContextPayload: showContextPayload.value,
               showDebugPanel: showDebugPanel.value,
            })
         );
      } catch (error) {
         console.warn('[ChatPanel] Failed to save menu preferences:', error);
      }
   }
   function collectPageForms() {
      const doms = document.querySelectorAll('.ao');
      console.log('[ChatPanel] Searching for elements with class .ao');
      console.log('[ChatPanel] Found elements:', elements.value.length);
      console.log('[ChatPanel] Element list:', elements);

      elements.value = [];

      doms.forEach((el, idx) => {
         let element: Record<string, any> = {
            tag: el.tagName.toLowerCase(),
         };
         if (el instanceof HTMLInputElement) {
            element['type'] = el.type;
            element['name'] = el.name;
            element['value'] = el.value;
         } else if (el instanceof HTMLTextAreaElement) {
            element['name'] = el.name;
            element['value'] = el.value;
         } else if (el instanceof HTMLSpanElement) {
            element['value'] = el.textContent;
            element['name'] = el.getAttribute('name') || `span_${idx}`;
            element['description'] = el.getAttribute('description') || '';
         }

         element['id'] = el.getAttribute('id') || '';

         elements.value.push(element);
      });

      console.log(`[ChatPanel] chat context:`, props.context);
      console.log('[ChatPanel] Collected context elements:', elements.value);
   }

   function renderMarkdown(content: string | null): string {
      if (!content) return '';
      const parsed = marked.parse(content, { breaks: true });
      return DOMPurify.sanitize(typeof parsed === 'string' ? parsed : String(parsed));
   }

   function getDisplayContent(content: string | null): string {
      if (!content) return '';
      if (showContextPayload.value) return content;
      const lines = content.split('\n');
      const firstLine = lines[0];
      if (firstLine?.startsWith('[Context:')) {
         return lines.slice(1).join('\n').trimStart();
      }
      return content;
   }

   const systemPromptRef = toRef(props, 'systemPrompt');

   function getSystemPromptDisplay(): string {
      const override = systemPromptRef.value?.trim();
      return override && override.length > 0 ? override : (SYSTEM_MESSAGE.content ?? '');
   }

   const {
      messages,
      loading,
      error,
      sendMessage: sendChatMessage,
      clearChat: clearChatMessages,
      loadStoredHistory,
   } = useChat(model, systemPromptRef);

   async function maybeScrollToBottom() {
      await nextTick();
      const el = scrollContainer.value;
      if (el) el.scrollTop = el.scrollHeight;
   }

   function formatFileSize(bytes: number): string {
      if (!Number.isFinite(bytes)) return '0 B';
      const units = ['B', 'KB', 'MB', 'GB'];
      let size = bytes;
      let unitIndex = 0;
      while (size >= 1024 && unitIndex < units.length - 1) {
         size /= 1024;
         unitIndex++;
      }
      return `${size.toFixed(size >= 10 || unitIndex === 0 ? 0 : 1)} ${units[unitIndex]}`;
   }

   function triggerFilePicker() {
      fileInputRef.value?.click();
   }

   function clearSelectedFile() {
      selectedFile.value = null;
      fileError.value = '';
      if (fileInputRef.value) fileInputRef.value.value = '';
   }

   function onFileSelected(event: Event) {
      const target = event.target as HTMLInputElement;
      const file = target.files?.[0] || null;
      fileError.value = '';
      selectedFile.value = file;
   }

   async function uploadAttachment(
      file: File
   ): Promise<{ document_id: string; filename: string } | null> {
      const opportunityId = props.context?.opportunity_id;
      if (!opportunityId) {
         fileError.value = 'Missing opportunity context for upload.';
         return null;
      }

      const formData = new FormData();
      formData.append('file', file);

      isUploading.value = true;
      try {
         const response = await authFetch(
            `/api/chat/attachments?opportunity_id=${encodeURIComponent(opportunityId)}`,
            {
               method: 'POST',
               body: formData,
            }
         );

         const result = await response.json();
         if (!response.ok || result.status !== 'ok') {
            fileError.value = result?.message || `Upload failed (${response.status})`;
            return null;
         }

         return {
            document_id: result.document_id,
            filename: result.filename || file.name,
         };
      } catch (error) {
         fileError.value = error instanceof Error ? error.message : 'Upload failed.';
         return null;
      } finally {
         isUploading.value = false;
      }
   }

   async function sendMessage() {
      const text = userInput.value.trim();
      if (!text && !selectedFile.value) return;

      // Re-collect forms before sending in case DOM changed
      collectPageForms();

      // Build message with context
      let messageContent = text;
      if (props.context) {
         //messageContent = `[Context: ${JSON.stringify(contextPayload)}]\n${JSON.stringify(elements.value)}${text}`;
         messageContent = text;
      }

      if (selectedFile.value) {
         const uploadResult = await uploadAttachment(selectedFile.value);
         if (!uploadResult) return;
         const attachmentRef = `[Event] Document Uploaded: {document_id: ${uploadResult.document_id}, filename: ${uploadResult.filename}}]`;
         messageContent = [messageContent, attachmentRef].filter(Boolean).join('\n\n');
      }

      console.log('Sending message:', messageContent);
      userInput.value = '';
      clearSelectedFile();
      await sendChatMessage(messageContent);
      await maybeScrollToBottom();
   }

   async function runTrackedElementsTool(className = '.ao') {
      const toolCalls: ChatMessage['tool_calls'] = [
         {
            id: `manual_${Date.now()}`,
            type: 'function',
            function: {
               name: 'tracked_elements',
               arguments: JSON.stringify({ className }),
            },
         },
      ];

      const toolMessages = await executeToolCalls(toolCalls);
      if (toolMessages.length > 0) {
         messages.value.push(...toolMessages);
      }
   }

   function clearChat() {
      userInput.value = '';
      clearChatMessages();
   }

   onMounted(async () => {
      await nextTick();
      loadMenuPreferences();
      loadCollapsedPreference();
      collectPageForms();
      if (!domObserver) {
         domObserver = new MutationObserver(() => {
            collectPageForms();
         });
         if (document.body) {
            domObserver.observe(document.body, { childList: true, subtree: true });
         }
      }
      if (!onDocumentClick) {
         onDocumentClick = (event: MouseEvent) => {
            if (!isMenuOpen.value) return;
            const target = event.target as Node | null;
            if (menuContainer.value && target && !menuContainer.value.contains(target)) {
               isMenuOpen.value = false;
            }
         };
         document.addEventListener('click', onDocumentClick);
      }
      if (!onCollapsedSync) {
         onCollapsedSync = (event: Event) => {
            const detail = (event as CustomEvent<{ collapsed: boolean }>).detail;
            if (detail && typeof detail.collapsed === 'boolean') {
               if (props.forceOpen && detail.collapsed) {
                  return;
               }
               isCollapsed.value = detail.collapsed;
            }
         };
         window.addEventListener('chat-collapsed-toggle', onCollapsedSync as EventListener);
      }
      loadStoredHistory();
      await maybeScrollToBottom();
   });

   watch(
      () => props.collapsed,
      (value) => {
         if (typeof value === 'boolean') {
            if (props.forceOpen && value) {
               isCollapsed.value = false;
               return;
            }
            isCollapsed.value = value;
         }
      }
   );

   watch(
      () => props.forceOpen,
      (value) => {
         if (value) {
            isCollapsed.value = false;
         }
      },
      { immediate: true }
   );

   onUnmounted(() => {
      if (domObserver) {
         domObserver.disconnect();
         domObserver = null;
      }
      if (onDocumentClick) {
         document.removeEventListener('click', onDocumentClick);
         onDocumentClick = null;
      }
      if (onCollapsedSync) {
         window.removeEventListener('chat-collapsed-toggle', onCollapsedSync as EventListener);
         onCollapsedSync = null;
      }
   });

   watch(messages, maybeScrollToBottom, { deep: true });
   watch([isMenuOpen, showContextPayload, showDebugPanel], saveMenuPreferences);
   watch(isCollapsed, (value) => {
      if (props.forceOpen && value) {
         isCollapsed.value = false;
         return;
      }
      saveCollapsedPreference(value);
      window.dispatchEvent(
         new CustomEvent('chat-collapsed-toggle', {
            detail: { collapsed: value },
         })
      );
   });
   watch(showDebugPanel, (enabled) => {
      window.dispatchEvent(
         new CustomEvent('chat-debug-toggle', {
            detail: { enabled },
         })
      );
   });

   return {
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
      collectPageForms,
      renderMarkdown,
      getDisplayContent,
      getSystemPromptDisplay,
      messages,
      loading,
      error,
      sendMessage,
      clearChat,
      runTrackedElementsTool,
   };
}
