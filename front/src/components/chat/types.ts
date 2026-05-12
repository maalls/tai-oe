/**
 * Chat types and constants
 */

import { apiUrl } from '../../utils/api';

export type ChatMessage = {
   role: 'system' | 'user' | 'assistant' | 'tool';
   content: string | null;
   name?: string;
   tool_call_id?: string;
   tool_arguments?: string; // JSON string of tool arguments for display
   // Carry through assistant tool_calls for subsequent requests
   tool_calls?: Array<{
      id: string;
      type: 'function';
      function: { name: string; arguments: string };
   }>;
};

export const LLM_API_URL = 'http://localhost:1234/v1/chat/completions';
export const DB_API_URL = apiUrl('csv/query');
export const DEFAULT_MODEL = 'Qwen3-VL-2B';
export const STORAGE_KEY = 'rk_chat_history_v1';

export const SYSTEM_MESSAGE: ChatMessage = {
   role: 'system',
   //'You are a helpful assistant that help use finding  electric parts.\n. When returning product informations, show product information like product name price etc. and also a link to the product page if available. Prefer concise answers and include table summaries when helpful.',
   content: 'You are A helpful assistant',
};
