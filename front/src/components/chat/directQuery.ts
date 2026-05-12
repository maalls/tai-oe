/**
 * Direct database query utilities for product lookup
 */

import { DB_API_URL } from './types';

export interface ColumnInfo {
   name: string;
   type: string;
   nullable: boolean;
   default: string | null;
   max_length: number | null;
   precision: number | null;
   scale: number | null;
}

export interface TableInfo {
   name: string;
   columns: ColumnInfo[];
}

export interface QueryParams {
   table: string;
   columns?: string;
   where?: string;
   sortBy?: string;
   sortOrder?: string;
   limit?: number;
}

export async function fetchTables(): Promise<TableInfo[]> {
   const url = new URL(DB_API_URL);
   url.searchParams.set('tables', 'true');

   const resp = await fetch(url.toString());
   if (!resp.ok) {
      throw new Error(`Failed to fetch tables: ${resp.status}`);
   }
   const data = await resp.json();
   return data.tables;
}

export async function executeDirectQuery(params: QueryParams): Promise<any> {
   const { table, columns = '*', where = '', sortBy = '', sortOrder = '', limit = 100 } = params;

   if (!table) throw new Error('Missing table');

   const url = new URL(DB_API_URL);
   url.searchParams.set('table', table);
   if (columns !== '*') url.searchParams.set('columns', columns);
   if (where) url.searchParams.set('where', where);

   // Combine sortBy and sortOrder
   if (sortBy && sortOrder) {
      url.searchParams.set('sortBy', `${sortBy} ${sortOrder}`);
   } else if (sortBy) {
      url.searchParams.set('sortBy', sortBy);
   }

   url.searchParams.set('limit', String(limit));

   const resp = await fetch(url.toString());
   if (!resp.ok) {
      const text = await resp.text();
      throw new Error(`DB error ${resp.status}: ${text}`);
   }
   return await resp.json();
}

export function formatResultsAsTable(data: any): string {
   if (!data || !data.rows || data.rows.length === 0) {
      return 'No results found';
   }

   const rows = data.rows;
   const columns = data.columns || (rows.length > 0 ? Object.keys(rows[0]) : []);

   let html = '<table style="width:100%; border-collapse: collapse; margin: 8px 0;">';

   // Header
   html += '<thead><tr style="background-color: #f3f4f6;">';
   for (const col of columns) {
      html += `<th style="border: 1px solid #e5e7eb; padding: 8px; text-align: left; font-weight: 600;">${col}</th>`;
   }
   html += '</tr></thead>';

   // Body
   html += '<tbody>';
   for (const row of rows) {
      html += '<tr style="border-bottom: 1px solid #e5e7eb;">';
      for (const col of columns) {
         let value = row[col];
         if (value === null || value === undefined) value = '—';

         if (typeof value === 'object') {
            value = JSON.stringify(value);
         }
         html += `<td style="border: 1px solid #e5e7eb; padding: 8px; text-align: left;">${String(value)}</td>`;
      }
      html += '</tr>';
   }
   html += '</tbody>';
   html += '</table>';

   return html;
}
