import { afterEach, describe, expect, it, vi } from 'vitest';

import { deleteOpportunityDocument } from '../../../../../src/api/document';

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
