import { afterEach, describe, expect, it, vi } from 'vitest';

import { deleteVendor } from '../../../../../src/api/vendor';

describe('deleteVendor', () => {
   afterEach(() => {
      vi.restoreAllMocks();
   });

   it('deletes vendor and returns deleted id', async () => {
      const payload = { id: 'v1' };
      const fetchMock = vi.fn().mockResolvedValue({
         ok: true,
         json: vi.fn().mockResolvedValue(payload),
      });
      vi.stubGlobal('fetch', fetchMock);

      const result = await deleteVendor('v1');

      expect(fetchMock).toHaveBeenCalledWith('/api/vendor/v1', { method: 'DELETE' });
      expect(result).toEqual(payload);
   });

   it('throws when deletion fails', async () => {
      vi.stubGlobal(
         'fetch',
         vi.fn().mockResolvedValue({
            ok: false,
            json: vi.fn(),
         })
      );

      await expect(deleteVendor('v1')).rejects.toThrow(
         'Erreur lors de la suppression du fournisseur'
      );
   });
});
