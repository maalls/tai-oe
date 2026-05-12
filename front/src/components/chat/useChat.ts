/**
 * Chat composable - main chat logic
 */

import { ref, type Ref } from 'vue';
import type { ChatMessage } from './types';
import { SYSTEM_MESSAGE } from './types';
import { CHAT_TOOLS } from './tools';
import { saveHistory, loadHistory } from './storage';
import { callLLM } from './llm';
import { executeToolCalls } from './toolExecutor';

export interface UseChatReturn {
   messages: Ref<ChatMessage[]>;
   loading: Ref<boolean>;
   error: Ref<string>;
   sendMessage: (text: string) => Promise<void>;
   clearChat: () => void;
   loadStoredHistory: () => void;
}

export function useChat(model: Ref<string>, systemPrompt?: Ref<string | undefined>): UseChatReturn {
   const messages = ref<ChatMessage[]>([]);
   const loading = ref(false);
   const error = ref('');

   function buildPayloadMessages(): ChatMessage[] {
      const resolvedSystem: ChatMessage = systemPrompt?.value?.trim()
         ? ({ role: 'system', content: systemPrompt.value.trim() } as ChatMessage)
         : SYSTEM_MESSAGE;
      return [resolvedSystem, ...messages.value];
   }

   async function runCompletionLoop() {
      loading.value = true;
      error.value = '';

      try {
         // First assistant turn
         const first = await callLLM(buildPayloadMessages(), model.value, CHAT_TOOLS);
         if (first?.message) {
            const msg = first.message as ChatMessage;
            messages.value.push({ role: 'assistant', content: msg.content ?? '' });

            // Preserve tool_calls for follow-up
            if (msg.tool_calls && msg.tool_calls.length > 0) {
               // Also append the assistant message with tool_calls for API context
               messages.value.push({
                  role: 'assistant',
                  content: msg.content,
                  tool_calls: msg.tool_calls,
               });

               const toolMessages = await executeToolCalls(msg.tool_calls);
               messages.value.push(...toolMessages);

               // Follow-up turn with tool results
               const follow = await callLLM(buildPayloadMessages(), model.value, CHAT_TOOLS);
               if (follow?.message) {
                  const followMsg = follow.message as ChatMessage;
                  messages.value.push({ role: 'assistant', content: followMsg.content ?? '' });
               }
            }
         }
      } catch (e: any) {
         error.value = String(e?.message || e);
      } finally {
         loading.value = false;
         saveHistory(messages.value, model.value);
      }
   }

   async function sendMessage(text: string) {
      const trimmed = text.trim();
      if (!trimmed || loading.value) return;

      error.value = '';
      messages.value.push({ role: 'user', content: trimmed });
      saveHistory(messages.value, model.value);

      await runCompletionLoop();
   }

   function clearChat() {
      messages.value = [];
      error.value = '';
      saveHistory([], model.value);
   }

   function loadStoredHistory() {
      const history = loadHistory();
      if (history) {
         messages.value = history.messages;
         if (history.model) {
            model.value = history.model;
         }
      }
   }

   return {
      messages,
      loading,
      error,
      sendMessage,
      clearChat,
      loadStoredHistory,
   };
}
