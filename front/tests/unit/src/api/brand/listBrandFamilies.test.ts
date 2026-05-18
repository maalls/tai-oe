import { afterEach, describe, expect, it, vi } from 'vitest';

import { listBrandFamilies } from '../../../../../src/api/brand';

describe('listBrandFamilies', () => {
   afterEach(() => {
      vi.restoreAllMocks();
   });

   it('returns families for a brand when API responds with ok', async () => {
      const payload = [{ id: 'f1', name: 'Family A', brand_id: 'b1', product_family_count: 3 }];
      const fetchMock = vi.fn().mockResolvedValue({
         ok: true,
         json: vi.fn().mockResolvedValue(payload),
      });
      vi.stubGlobal('fetch', fetchMock);

      const result = await listBrandFamilies('b1');

      expect(fetchMock).toHaveBeenCalledWith('/api/brand/b1/families');
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

      await expect(listBrandFamilies('b1')).rejects.toThrow(
         'Erreur lors du chargement des familles de la marque'
      );
   });
});
