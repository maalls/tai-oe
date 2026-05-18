import { afterEach, describe, expect, it, vi } from 'vitest';

import { listCatalogFamilies } from '../../../../../src/api/catalog';

describe('listCatalogFamilies', () => {
   afterEach(() => {
      vi.restoreAllMocks();
   });

   it('returns families when API responds with ok', async () => {
      const payload = [{ id: 'f1', name: 'Family A', brand_id: 'b1' }];
      const fetchMock = vi.fn().mockResolvedValue({
         ok: true,
         json: vi.fn().mockResolvedValue(payload),
      });
      vi.stubGlobal('fetch', fetchMock);

      const result = await listCatalogFamilies();

      expect(fetchMock).toHaveBeenCalledWith('/api/catalog/families');
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

      await expect(listCatalogFamilies()).rejects.toThrow('Erreur lors du chargement des familles');
   });
});
