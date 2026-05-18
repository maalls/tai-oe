import { afterEach, describe, expect, it, vi } from 'vitest';

import { listCatalogBrands } from '../../../../../src/api/catalog';

describe('listCatalogBrands', () => {
   afterEach(() => {
      vi.restoreAllMocks();
   });

   it('returns brands when API responds with ok', async () => {
      const payload = [{ id: 'b1', name: 'Brand A' }];
      const fetchMock = vi.fn().mockResolvedValue({
         ok: true,
         json: vi.fn().mockResolvedValue(payload),
      });
      vi.stubGlobal('fetch', fetchMock);

      const result = await listCatalogBrands();

      expect(fetchMock).toHaveBeenCalledWith('/api/catalog/brands');
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

      await expect(listCatalogBrands()).rejects.toThrow('Erreur lors du chargement des marques');
   });
});
