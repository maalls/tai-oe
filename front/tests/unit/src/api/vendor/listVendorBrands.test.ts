import { afterEach, describe, expect, it, vi } from 'vitest';

import { listVendorBrands } from '../../../../../src/api/vendor';

describe('listVendorBrands', () => {
   afterEach(() => {
      vi.restoreAllMocks();
   });

   it('returns related brands for a vendor when API responds with ok', async () => {
      const payload = [
         {
            id: 'b1',
            name: 'Brand A',
            marque: 'Brand A',
            product_count: 3,
         },
      ];
      const fetchMock = vi.fn().mockResolvedValue({
         ok: true,
         json: vi.fn().mockResolvedValue(payload),
      });
      vi.stubGlobal('fetch', fetchMock);

      const result = await listVendorBrands('v1');

      expect(fetchMock).toHaveBeenCalledWith('/api/vendor/v1/brands');
      expect(result).toEqual(payload);
   });

   it('throws when API responds with non-ok status', async () => {
      vi.stubGlobal(
         'fetch',
         vi.fn().mockResolvedValue({
            ok: false,
            json: vi.fn(),
         })
      );

      await expect(listVendorBrands('v1')).rejects.toThrow(
         'Erreur lors du chargement des marques du fournisseur'
      );
   });
});
