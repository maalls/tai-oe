import { afterEach, describe, expect, it, vi } from 'vitest';

import { deleteAction } from '../../../../../src/api/action';

describe('deleteAction', () => {
   afterEach(() => {
      vi.restoreAllMocks();
   });

   it('deletes action with auth token', async () => {
      const fetchMock = vi.fn().mockResolvedValue({
         ok: true,
         json: vi.fn().mockResolvedValue({ status: 'ok' }),
      });
      vi.stubGlobal('fetch', fetchMock);

      await deleteAction('a1', 'token-1');

      expect(fetchMock).toHaveBeenCalledWith('/api/actions/a1', {
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

      await expect(deleteAction('a1', 'token-1')).rejects.toThrow('boom');
   });
});
