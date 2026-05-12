/**
 * Tool execution handlers
 */

import type { ChatMessage } from './types';
import { DB_API_URL } from './types';

export function safeParseArgs(argStr: string | undefined): any {
   if (!argStr) return {};
   try {
      return JSON.parse(argStr);
   } catch {
      return {};
   }
}

export async function dbProduct(args: any): Promise<any> {
   const table = 'test_commerce_vectors';

   // columns can be array or comma-separated string
   let columns = ['marque', 'refciale', 'gamme', 'libelle240', 'tarif', 'qt'];

   //if (typeof columns !== 'string' || !columns.trim()) columns = '*';

   console.log('DB Product Query Columns:', columns);
   const where = typeof args?.where === 'string' ? args.where : '';
   const limit = Number.isInteger(args?.limit) ? args.limit : 100;
   const offset = Number.isInteger(args?.offset) ? args.offset : 0;

   const vendorName = typeof args?.vendor_name === 'string' ? args.vendor_name.trim() : '';
   if (vendorName) {
      const vendorCondition = `marque ILIKE '%${vendorName.replace(/'/g, "''")}%'`;
      if (where) {
         args.where = `(${where}) AND (${vendorCondition})`;
      } else {
         args.where = vendorCondition;
      }
   }
   // Combine sortBy and sortOrder into single ORDER BY clause
   const sortByColumn = typeof args?.sortBy === 'string' ? args.sortBy.trim() : '';
   const sortOrder = typeof args?.sortOrder === 'string' ? args.sortOrder.trim().toUpperCase() : '';

   // Validate: sortOrder requires sortByColumn
   if (sortOrder && !sortByColumn) {
      throw new Error('sortOrder provided without sortBy column');
   }

   const sortByClause = sortByColumn && sortOrder ? `${sortByColumn} ${sortOrder}` : sortByColumn;

   const url = new URL(DB_API_URL);
   url.searchParams.set('table', table);
   const columnsParam = Array.isArray(columns) ? columns.join(',') : columns;
   if (columnsParam !== '*') url.searchParams.set('columns', columnsParam);
   if (where) url.searchParams.set('where', where);
   if (sortByClause) url.searchParams.set('sortBy', sortByClause);
   url.searchParams.set('limit', String(limit));
   url.searchParams.set('offset', String(offset));

   const resp = await fetch(url.toString());
   if (!resp.ok) {
      const text = await resp.text();
      throw new Error(`DB error ${resp.status}: ${text}`);
   }
   return await resp.json();
}

export async function dbQuery(args: any): Promise<any> {
   const table = String(args?.table || '').trim();
   if (!table) throw new Error('Missing table');

   // columns can be array or comma-separated string
   let columns = args?.columns;
   if (Array.isArray(columns)) columns = columns.join(',');
   if (typeof columns !== 'string' || !columns.trim()) columns = '*';

   const where = typeof args?.where === 'string' ? args.where : '';
   const limit = Number.isInteger(args?.limit) ? args.limit : 100;
   const offset = Number.isInteger(args?.offset) ? args.offset : 0;

   // Combine sortBy and sortOrder into single ORDER BY clause
   const sortByColumn = typeof args?.sortBy === 'string' ? args.sortBy.trim() : '';
   const sortOrder = typeof args?.sortOrder === 'string' ? args.sortOrder.trim().toUpperCase() : '';

   // Validate: sortOrder requires sortByColumn
   if (sortOrder && !sortByColumn) {
      throw new Error('sortOrder provided without sortBy column');
   }

   const sortByClause = sortByColumn && sortOrder ? `${sortByColumn} ${sortOrder}` : sortByColumn;

   const url = new URL(DB_API_URL);
   url.searchParams.set('table', table);
   if (columns !== '*') url.searchParams.set('columns', columns);
   if (where) url.searchParams.set('where', where);
   if (sortByClause) url.searchParams.set('sortBy', sortByClause);
   url.searchParams.set('limit', String(limit));
   url.searchParams.set('offset', String(offset));

   const resp = await fetch(url.toString());
   if (!resp.ok) {
      const text = await resp.text();
      throw new Error(`DB error ${resp.status}: ${text}`);
   }
   return await resp.json();
}


export function trackedElements(args: any): any {
   const className =
      typeof args?.className === 'string' && args.className.trim() ? args.className.trim() : '.ao';

   if (typeof document === 'undefined') {
      return { error: 'document is not available', count: 0, elements: [] };
   }

   const nodes = document.querySelectorAll(className);
   const elements = Array.from(nodes).map((el) => {
      const html = el as HTMLElement;
      const elementName =
         el instanceof HTMLInputElement ||
         el instanceof HTMLTextAreaElement ||
         el instanceof HTMLSelectElement ||
         el instanceof HTMLButtonElement
            ? (el as any).name
            : html.getAttribute('name') || undefined;

      const base: Record<string, any> = {
         tag: el.tagName.toLowerCase(),
         id: html.id || undefined,
         name: elementName || undefined,
         value:
            el instanceof HTMLInputElement ||
            el instanceof HTMLTextAreaElement ||
            el instanceof HTMLSelectElement ||
            el instanceof HTMLButtonElement
               ? (el as any).value
               : undefined,
      };

      // Remove undefined values
      Object.keys(base).forEach((key) => base[key] === undefined && delete base[key]);

      // Collect non-standard attributes (exclude common ones)
      const excludeAttrs = new Set([
         'id',
         'name',
         'value',
         'class',
         'type',
         'placeholder',
         'disabled',
         'readonly',
         'required',
         'checked',
         'multiple',
         'rows',
         'cols',
         'pattern',
         'min',
         'max',
         'step',
      ]);
      const attributes: Record<string, any> = {};
      if (html.attributes && html.attributes.length > 0) {
         for (let i = 0; i < html.attributes.length; i++) {
            const attr = html.attributes.item(i);
            if (!attr) continue;
            if (!excludeAttrs.has(attr.name)) {
               attributes[attr.name] = attr.value;
            }
         }
      }
      if (Object.keys(attributes).length > 0) {
         base.attributes = attributes;
      }

      // Type-specific properties
      if (el instanceof HTMLInputElement) {
         base.type = el.type;
         base.placeholder = el.placeholder || undefined;
         base.disabled = el.disabled ? true : undefined;
         base.readonly = el.readOnly ? true : undefined;
         base.required = el.required ? true : undefined;
         if (el.checked) base.checked = true;
         if (el.pattern) base.pattern = el.pattern;
         if (el.min) base.min = el.min;
         if (el.max) base.max = el.max;
         if (el.step) base.step = el.step;
      } else if (el instanceof HTMLTextAreaElement) {
         base.placeholder = el.placeholder || undefined;
         base.disabled = el.disabled ? true : undefined;
         base.readonly = el.readOnly ? true : undefined;
         base.required = el.required ? true : undefined;
         if (el.rows) base.rows = el.rows;
         if (el.cols) base.cols = el.cols;
      } else if (el instanceof HTMLSelectElement) {
         base.disabled = el.disabled ? true : undefined;
         base.multiple = el.multiple ? true : undefined;
         base.required = el.required ? true : undefined;
         base.options = Array.from(el.options).map((opt) => ({
            text: opt.text,
            value: opt.value,
            selected: opt.selected,
         }));
      } else if (el instanceof HTMLButtonElement) {
         base.type = el.type;
         if (el.disabled) base.disabled = true;
         const text = el.textContent?.trim();
         if (text) base.textContent = text;
      } else {
         const text = html.textContent?.trim()?.substring(0, 100);
         if (text) base.textContent = text;
      }

      // Remove undefined values again
      Object.keys(base).forEach((key) => base[key] === undefined && delete base[key]);

      return base;
   });

   return { count: elements.length, elements, selector: className };
}

export function updateDom(args: any): any {
   const domId = typeof args?.dom_id === 'string' ? args.dom_id.trim() : '';
   if (!domId) {
      return { error: 'Missing dom_id' };
   }

   if (typeof document === 'undefined') {
      return { error: 'document is not available' };
   }

   const el = document.getElementById(domId);
   if (!el) {
      return { error: `Element not found: ${domId}` };
   }

   const value = args?.value ?? '';

   if (el instanceof HTMLInputElement || el instanceof HTMLTextAreaElement) {
      el.value = String(value);
      el.dispatchEvent(new Event('input', { bubbles: true }));
      el.dispatchEvent(new Event('change', { bubbles: true }));
   } else if (el instanceof HTMLSelectElement) {
      el.value = String(value);
      el.dispatchEvent(new Event('change', { bubbles: true }));
   } else {
      el.textContent = String(value);
   }

   return { status: 'ok', dom_id: domId, value };
}

export function readDom(args: any): any {
   const domId = typeof args?.dom_id === 'string' ? args.dom_id.trim() : '';
   if (!domId) {
      return { error: 'Missing dom_id' };
   }

   if (typeof document === 'undefined') {
      return { error: 'document is not available' };
   }

   const el = document.getElementById(domId);
   if (!el) {
      return { error: `Element not found: ${domId}` };
   }

   let value: string | null = null;
   if (el instanceof HTMLInputElement || el instanceof HTMLTextAreaElement) {
      value = el.value;
   } else if (el instanceof HTMLSelectElement) {
      value = el.value;
   } else {
      value = el.textContent;
   }

   return {
      status: 'ok',
      dom_id: domId,
      value,
   };
}

export async function fetchUrl(args: any): Promise<any> {
   const url = typeof args?.url === 'string' ? args.url.trim() : '';
   if (!url) return { error: 'Missing url' };

   const maxChars = Number.isInteger(args?.max_chars) ? args.max_chars : 10000;
   const timeoutMs = Number.isInteger(args?.timeout_ms) ? args.timeout_ms : 8000;

   try {
      const apiUrl = new URL('/api/fetch', window.location.origin);
      apiUrl.searchParams.set('url', url);
      apiUrl.searchParams.set('max_chars', String(maxChars));
      apiUrl.searchParams.set('timeout_ms', String(timeoutMs));

      const response = await fetch(apiUrl.toString(), { method: 'GET' });
      const data = await response.json();

      if (!response.ok) {
         return { error: data?.error || `Fetch failed (${response.status})`, url };
      }

      return data;
   } catch (error: any) {
      return { error: String(error?.message || error), url };
   }
}

export async function fsCreate(args: any): Promise<any> {
   const path = typeof args?.path === 'string' ? args.path.trim() : '';
   if (!path) return { error: 'Missing path' };

   const type = args?.type === 'file' ? 'file' : 'dir';

   try {
      const response = await fetch('/api/fs/create', {
         method: 'POST',
         headers: { 'Content-Type': 'application/json' },
         body: JSON.stringify({ path, type }),
      });

      const data = await response.json();
      if (!response.ok) {
         return { error: data?.error || `Create failed (${response.status})`, path };
      }
      return data;
   } catch (error: any) {
      return { error: String(error?.message || error), path };
   }
}

export async function fsRead(args: any): Promise<any> {
   const path = typeof args?.path === 'string' ? args.path.trim() : '';
   if (!path) return { error: 'Missing path' };

   const maxChars = Number.isInteger(args?.max_chars) ? args.max_chars : 10000;

   try {
      const response = await fetch('/api/fs/read', {
         method: 'POST',
         headers: { 'Content-Type': 'application/json' },
         body: JSON.stringify({ path, max_chars: maxChars }),
      });

      const data = await response.json();
      if (!response.ok) {
         return { error: data?.error || `Read failed (${response.status})`, path };
      }
      return data;
   } catch (error: any) {
      return { error: String(error?.message || error), path };
   }
}

export async function curlRequest(args: any): Promise<any> {
   const url = typeof args?.url === 'string' ? args.url.trim() : '';
   if (!url) return { error: 'Missing url' };

   const payload = {
      url,
      method: typeof args?.method === 'string' ? args.method : 'GET',
      headers: typeof args?.headers === 'object' && args.headers ? args.headers : {},
      body: typeof args?.body === 'string' ? args.body : undefined,
      max_chars: Number.isInteger(args?.max_chars) ? args.max_chars : undefined,
      timeout_ms: Number.isInteger(args?.timeout_ms) ? args.timeout_ms : undefined,
   };

   try {
      const response = await fetch('/api/curl', {
         method: 'POST',
         headers: { 'Content-Type': 'application/json' },
         body: JSON.stringify(payload),
      });

      const data = await response.json();
      if (!response.ok) {
         return { error: data?.error || `Curl failed (${response.status})`, url };
      }
      return data;
   } catch (error: any) {
      return { error: String(error?.message || error), url };
   }
}

export async function executeToolCalls(
   toolCalls: ChatMessage['tool_calls']
): Promise<ChatMessage[]> {
   if (!toolCalls || toolCalls.length === 0) return [];

   const toolMessages: ChatMessage[] = [];

   for (const tc of toolCalls) {
      if (tc.type !== 'function') continue;

      const { name, arguments: argStr } = tc.function || {};

      if (name === 'db_products_query') {
         try {
            const args = safeParseArgs(argStr);
            const result = await dbProduct(args);
            toolMessages.push({
               role: 'tool',
               name: 'db_products_query',
               tool_call_id: tc.id,
               tool_arguments: argStr,
               content: JSON.stringify(result),
            });
         } catch (e: any) {
            toolMessages.push({
               role: 'tool',
               name: 'db_products_query',
               tool_call_id: tc.id,
               tool_arguments: argStr,
               content: JSON.stringify({ error: String(e?.message || e) }),
            });
         }
      } else if (name === 'tracked_elements') {
         try {
            const args = safeParseArgs(argStr);
            const result = trackedElements(args);
            toolMessages.push({
               role: 'tool',
               name: 'tracked_elements',
               tool_call_id: tc.id,
               tool_arguments: argStr,
               content: JSON.stringify(result),
            });
         } catch (e: any) {
            toolMessages.push({
               role: 'tool',
               name: 'tracked_elements',
               tool_call_id: tc.id,
               tool_arguments: argStr,
               content: JSON.stringify({ error: String(e?.message || e) }),
            });
         }
      } else if (name === 'update') {
         try {
            const args = safeParseArgs(argStr);
            const result = updateDom(args);
            toolMessages.push({
               role: 'tool',
               name: 'update',
               tool_call_id: tc.id,
               tool_arguments: argStr,
               content: JSON.stringify(result),
            });
         } catch (e: any) {
            toolMessages.push({
               role: 'tool',
               name: 'update',
               tool_call_id: tc.id,
               tool_arguments: argStr,
               content: JSON.stringify({ error: String(e?.message || e) }),
            });
         }
      } else if (name === 'read' || name === 'read_dom_element') {
         try {
            const args = safeParseArgs(argStr);
            const result = readDom(args);
            toolMessages.push({
               role: 'tool',
               name: 'read',
               tool_call_id: tc.id,
               tool_arguments: argStr,
               content: JSON.stringify(result),
            });
         } catch (e: any) {
            toolMessages.push({
               role: 'tool',
               name: 'read',
               tool_call_id: tc.id,
               tool_arguments: argStr,
               content: JSON.stringify({ error: String(e?.message || e) }),
            });
         }
      } else if (name === 'fetch_url') {
         try {
            const args = safeParseArgs(argStr);
            const result = await fetchUrl(args);
            toolMessages.push({
               role: 'tool',
               name: 'fetch_url',
               tool_call_id: tc.id,
               tool_arguments: argStr,
               content: JSON.stringify(result),
            });
         } catch (e: any) {
            toolMessages.push({
               role: 'tool',
               name: 'fetch_url',
               tool_call_id: tc.id,
               tool_arguments: argStr,
               content: JSON.stringify({ error: String(e?.message || e) }),
            });
         }
      } else if (name === 'fs_create') {
         try {
            const args = safeParseArgs(argStr);
            const result = await fsCreate(args);
            toolMessages.push({
               role: 'tool',
               name: 'fs_create',
               tool_call_id: tc.id,
               tool_arguments: argStr,
               content: JSON.stringify(result),
            });
         } catch (e: any) {
            toolMessages.push({
               role: 'tool',
               name: 'fs_create',
               tool_call_id: tc.id,
               tool_arguments: argStr,
               content: JSON.stringify({ error: String(e?.message || e) }),
            });
         }
      } else if (name === 'fs_read') {
         try {
            const args = safeParseArgs(argStr);
            const result = await fsRead(args);
            toolMessages.push({
               role: 'tool',
               name: 'fs_read',
               tool_call_id: tc.id,
               tool_arguments: argStr,
               content: JSON.stringify(result),
            });
         } catch (e: any) {
            toolMessages.push({
               role: 'tool',
               name: 'fs_read',
               tool_call_id: tc.id,
               tool_arguments: argStr,
               content: JSON.stringify({ error: String(e?.message || e) }),
            });
         }
      } else if (name === 'curl') {
         try {
            const args = safeParseArgs(argStr);
            const result = await curlRequest(args);
            toolMessages.push({
               role: 'tool',
               name: 'curl',
               tool_call_id: tc.id,
               tool_arguments: argStr,
               content: JSON.stringify(result),
            });
         } catch (e: any) {
            toolMessages.push({
               role: 'tool',
               name: 'curl',
               tool_call_id: tc.id,
               tool_arguments: argStr,
               content: JSON.stringify({ error: String(e?.message || e) }),
            });
         }
      }
   }

   return toolMessages;
}
