/**
 * Chat storage utilities (localStorage persistence)
 */

import type { ChatMessage } from './types';
import { STORAGE_KEY } from './types';

export interface ChatHistory {
   messages: ChatMessage[];
   model: string;
}

export function saveHistory(messages: ChatMessage[], model: string): void {
   try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({ messages, model } as ChatHistory));
   } catch (e) {
      // Ignore storage errors
      console.warn('Failed to save chat history:', e);
   }
}

export function loadHistory(): ChatHistory | null {
   try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return null;

      const parsed = JSON.parse(raw);
      if (parsed?.messages && Array.isArray(parsed.messages)) {
         return {
            messages: parsed.messages,
            model: parsed.model || '',
         };
      }
   } catch (e) {
      console.warn('Failed to load chat history:', e);
   }
   return null;
}

export function clearHistory(): void {
   try {
      localStorage.removeItem(STORAGE_KEY);
   } catch (e) {
      console.warn('Failed to clear chat history:', e);
   }
}
