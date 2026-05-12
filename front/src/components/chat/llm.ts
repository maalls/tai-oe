/**
 * LLM API integration
 */

import type { ChatMessage } from './types';
import { LLM_API_URL, DEFAULT_MODEL } from './types';

export async function callLLM(messages: ChatMessage[], model: string, tools: any[]): Promise<any> {
   const body = {
      model: model || DEFAULT_MODEL,
      messages,
      tools,
      tool_choice: 'auto',
   };

   const resp = await fetch(LLM_API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
   });

   if (!resp.ok) {
      const text = await resp.text();
      throw new Error(`LLM error ${resp.status}: ${text}`);
   }

   const data = await resp.json();
   return data?.choices?.[0];
}
