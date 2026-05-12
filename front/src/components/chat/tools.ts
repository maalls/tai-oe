/**
 * LLM tool definitions (db_query and qdrant_search)
 */

export const CHAT_TOOLS = [
   {
      type: 'function',
      function: {
         name: 'tracked_elements',
         description: 'List elements tracked on the page by CSS class (default: .ao).',
         parameters: {
            type: 'object',
            properties: {
               className: {
                  type: 'string',
                  description: 'CSS selector for tracked elements (default: .ao)',
               },
            },
            required: [],
         },
      },
   },
   {
      type: 'function',
      function: {
         name: 'product_search',
         description:
            'Search products by free-text query and/or column filters (marque, refciale, tarif). Uses combined semantic + filter search.',
         parameters: {
            type: 'object',
            properties: {
               query: {
                  type: 'string',
                  description: 'Free-text query for semantic/similarity search',
               },
               marque: {
                  type: 'string',
                  description: 'Manufacturer/brand filter (marque)',
               },
               refciale: {
                  type: 'string',
                  description: 'Part number filter (refciale)',
               },
               tarif: {
                  type: 'string',
                  description: 'Price filter (tarif) - exact match or text value',
               },
               limit: {
                  type: 'integer',
                  minimum: 1,
                  maximum: 100,
                  default: 50,
                  description: 'Maximum number of results',
               },
            },
            required: [],
         },
      },
   },
   {
      type: 'function',
      function: {
         name: 'update',
         description: 'Update a DOM element by id with a new value or text content.',
         parameters: {
            type: 'object',
            properties: {
               dom_id: {
                  type: 'string',
                  description: 'Target DOM element id to update',
               },
               value: {
                  type: 'string',
                  description: 'Value or text to set on the element',
               },
            },
            required: ['dom_id', 'value'],
         },
      },
   },
   {
      type: 'function',
      function: {
         name: 'read_dom_element',
         description: 'Read a DOM element by id and return its value or text content.',
         parameters: {
            type: 'object',
            properties: {
               dom_id: {
                  type: 'string',
                  description: 'Target DOM element id to read',
               },
            },
            required: ['dom_id'],
         },
      },
   },
   {
      type: 'function',
      function: {
         name: 'fs_create',
         description: 'Create a file or folder under the User directory.',
         parameters: {
            type: 'object',
            properties: {
               path: {
                  type: 'string',
                  description: 'Relative path to create under the User directory',
               },
               type: {
                  type: 'string',
                  enum: ['dir', 'file'],
                  description: 'Create a directory or a file',
                  default: 'dir',
               },
            },
            required: ['path'],
         },
      },
   },
   {
      type: 'function',
      function: {
         name: 'fs_read',
         description: 'Read a local file under the User directory.',
         parameters: {
            type: 'object',
            properties: {
               path: {
                  type: 'string',
                  description: 'Relative file path under the User directory',
               },
               max_chars: {
                  type: 'integer',
                  minimum: 100,
                  maximum: 50000,
                  default: 10000,
                  description: 'Maximum characters to return',
               },
            },
            required: ['path'],
         },
      },
   },
   {
      type: 'function',
      function: {
         name: 'curl',
         description: 'Run an HTTP request (curl-like) via backend and return response text.',
         parameters: {
            type: 'object',
            properties: {
               url: {
                  type: 'string',
                  description: 'Target URL (http/https)',
               },
               method: {
                  type: 'string',
                  enum: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE'],
                  description: 'HTTP method',
                  default: 'GET',
               },
               headers: {
                  type: 'object',
                  additionalProperties: { type: 'string' },
                  description: 'Request headers',
               },
               body: {
                  type: 'string',
                  description: 'Request body (string)',
               },
               max_chars: {
                  type: 'integer',
                  minimum: 100,
                  maximum: 50000,
                  default: 10000,
                  description: 'Maximum characters to return',
               },
               timeout_ms: {
                  type: 'integer',
                  minimum: 1000,
                  maximum: 20000,
                  default: 8000,
                  description: 'Timeout in milliseconds',
               },
            },
            required: ['url'],
         },
      },
   },
];
