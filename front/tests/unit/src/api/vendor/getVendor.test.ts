import { afterEach, describe, expect, it, vi } from 'vitest';

import { getVendor } from '../../../../../src/api/vendor';

describe('getVendor', () => {
   afterEach(() => {
      vi.restoreAllMocks();
   });

   it('returns the vendor for a given id', async () => {
      const payload = {
         id: 'v1',
         name: 'ACME',
         created_at: '2026-01-01',
         updated_at: '2026-01-01',
      };
      const fetchMock = vi.fn().mockResolvedValue({
         ok: true,
         json: vi.fn().mockResolvedValue(payload),
      });
      vi.stubGlobal('fetch', fetchMock);

      const result = await getVendor('v1');

      expect(fetchMock).toHaveBeenCalledWith('/api/vendor/v1');
      expect(result).toEqual(payload);
   });

   it('throws when vendor is not found', async () => {
      vi.stubGlobal(
         'fetch',
         vi.fn().mockResolvedValue({
            ok: false,
            json: vi.fn(),
         })
      );

      await expect(getVendor('missing')).rejects.toThrow('Fournisseur introuvable');
   });
});
