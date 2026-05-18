import { afterEach, describe, expect, it, vi } from 'vitest';

import {
   clearDocumentStorageKey,
   deleteOpportunityDocument,
} from '../../../../../src/api/document';

describe('deleteOpportunityDocument', () => {
   afterEach(() => {
      vi.restoreAllMocks();
   });

   it('deletes a document with auth token', async () => {
      const fetchMock = vi.fn().mockResolvedValue({
         ok: true,
         json: vi.fn().mockResolvedValue({ status: 'ok' }),
      });
      vi.stubGlobal('fetch', fetchMock);

      await deleteOpportunityDocument('doc-1', 'token-1');

      expect(fetchMock).toHaveBeenCalledWith('/api/document/doc-1', {
         method: 'DELETE',
         headers: {
            Authorization: 'Bearer token-1',
         },
      });
   });

   it('throws when deletion fails', async () => {
      vi.stubGlobal(
         'fetch',
         vi.fn().mockResolvedValue({
            ok: false,
            json: vi.fn().mockResolvedValue({ message: 'boom' }),
         })
      );

      await expect(deleteOpportunityDocument('doc-1', 'token-1')).rejects.toThrow('boom');
   });
});

describe('clearDocumentStorageKey', () => {
   afterEach(() => {
      vi.restoreAllMocks();
   });

   it('clears storage key with auth token', async () => {
      const payload = { id: 'doc-1', storage_key: null };
      const fetchMock = vi.fn().mockResolvedValue({
         ok: true,
         json: vi.fn().mockResolvedValue(payload),
      });
      vi.stubGlobal('fetch', fetchMock);

      const result = await clearDocumentStorageKey('doc-1', 'token-1');

      expect(fetchMock).toHaveBeenCalledWith('/api/document/doc-1/storage-key', {
         method: 'PUT',
         headers: {
            'Content-Type': 'application/json',
            Authorization: 'Bearer token-1',
         },
         body: JSON.stringify({ storage_key: null }),
      });
      expect(result).toEqual(payload);
   });

   it('throws when request fails', async () => {
      vi.stubGlobal(
         'fetch',
         vi.fn().mockResolvedValue({
            ok: false,
            json: vi.fn().mockResolvedValue({ error: 'boom' }),
         })
      );

      await expect(clearDocumentStorageKey('doc-1', 'token-1')).rejects.toThrow('boom');
   });
});
