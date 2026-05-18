import { afterEach, describe, expect, it, vi } from 'vitest';

import { updateDocumentStatus } from '../../../../../src/api/document';

describe('updateDocumentStatus', () => {
   afterEach(() => {
      vi.restoreAllMocks();
   });

   it('updates document status with auth token', async () => {
      const payload = { id: 'doc-1', status: 'PAID' };
      const fetchMock = vi.fn().mockResolvedValue({
         ok: true,
         json: vi.fn().mockResolvedValue(payload),
      });
      vi.stubGlobal('fetch', fetchMock);

      const result = await updateDocumentStatus('doc-1', 'PAID', 'token-1');

      expect(fetchMock).toHaveBeenCalledWith('/api/document/doc-1/status', {
         method: 'PUT',
         headers: {
            'Content-Type': 'application/json',
            Authorization: 'Bearer token-1',
         },
         body: JSON.stringify({ status: 'PAID' }),
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

      await expect(updateDocumentStatus('doc-1', 'PAID', 'token-1')).rejects.toThrow('boom');
   });
});