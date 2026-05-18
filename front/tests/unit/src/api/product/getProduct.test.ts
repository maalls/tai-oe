import { afterEach, describe, expect, it, vi } from 'vitest';

import { getProduct } from '../../../../../src/api/product';

describe('getProduct', () => {
   afterEach(() => {
      vi.restoreAllMocks();
   });

   it('returns product payload', async () => {
      const payload = { id: 'p-1', marque: 'ACME', refciale: 'SKU-1' };
      const fetchMock = vi.fn().mockResolvedValue({
         ok: true,
         json: vi.fn().mockResolvedValue(payload),
      });
      vi.stubGlobal('fetch', fetchMock);

      const result = await getProduct('p-1');

      expect(fetchMock).toHaveBeenCalledWith('/api/products/p-1');
      expect(result).toEqual(payload);
   });

   it('throws when request fails', async () => {
      vi.stubGlobal(
         'fetch',
         vi.fn().mockResolvedValue({
            ok: false,
            json: vi.fn(),
         })
      );

      await expect(getProduct('p-1')).rejects.toThrow('Erreur lors du chargement du produit');
   });
});
