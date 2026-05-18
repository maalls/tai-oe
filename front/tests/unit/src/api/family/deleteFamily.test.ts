import { afterEach, describe, expect, it, vi } from 'vitest';

import { deleteFamily } from '../../../../../src/api/family';

describe('deleteFamily', () => {
   afterEach(() => {
      vi.restoreAllMocks();
   });

   it('deletes the family', async () => {
      const fetchMock = vi.fn().mockResolvedValue({
         ok: true,
         json: vi.fn(),
      });
      vi.stubGlobal('fetch', fetchMock);

      await deleteFamily('f1');

      expect(fetchMock).toHaveBeenCalledWith('/api/family/f1', {
         method: 'DELETE',
      });
   });

   it('throws when delete fails', async () => {
      vi.stubGlobal(
         'fetch',
         vi.fn().mockResolvedValue({
            ok: false,
            json: vi.fn(),
         })
      );

      await expect(deleteFamily('f1')).rejects.toThrow(
         'Erreur lors de la suppression de la famille'
      );
   });
});
