import { afterEach, describe, expect, it, vi } from 'vitest';

import { searchProducts } from '../../../../../src/api/product';

describe('searchProducts', () => {
   afterEach(() => {
      vi.restoreAllMocks();
   });

   it('returns paginated product payload', async () => {
      const fetchMock = vi.fn().mockResolvedValue({
         ok: true,
         json: vi.fn().mockResolvedValue({
            products: [{ id: 'p-1', refciale: 'SKU-1' }],
            total_count: 12,
         }),
      });
      vi.stubGlobal('fetch', fetchMock);

      const result = await searchProducts({
         query: 'abc',
         marque: 'acme',
         refciale: 'sku',
         tarif: '42',
         family: 'fam',
         exactMatch: true,
         limit: 100,
         offset: 200,
      });

      expect(fetchMock).toHaveBeenCalledWith(
         '/api/products/search?query=abc&marque=acme&refciale=sku&tarif=42&family=fam&exact_match=true&limit=100&offset=200'
      );
      expect(result).toEqual({
         products: [{ id: 'p-1', refciale: 'SKU-1' }],
         totalCount: 12,
      });
   });

   it('throws when request fails', async () => {
      vi.stubGlobal(
         'fetch',
         vi.fn().mockResolvedValue({
            ok: false,
            json: vi.fn(),
         })
      );

      await expect(searchProducts()).rejects.toThrow('Erreur lors du chargement des produits');
   });
});