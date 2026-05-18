import { afterEach, describe, expect, it, vi } from 'vitest';

import { getQuoteProductsContext } from '../../../../../src/api/product';

describe('getQuoteProductsContext', () => {
   afterEach(() => {
      vi.restoreAllMocks();
   });

   it('returns products and net price families keyed by sku', async () => {
      const fetchMock = vi.fn().mockResolvedValue({
         ok: true,
         json: vi.fn().mockResolvedValue({
            products: [{ sku: 'SKU-1', price: 100 }],
            net_price_families: [{ product_code: 'SKU-1', net_price: 72 }],
         }),
      });
      vi.stubGlobal('fetch', fetchMock);

      const result = await getQuoteProductsContext(['SKU-1', 'SKU-1']);

      expect(fetchMock).toHaveBeenCalledWith('/api/products/quote-context?sku=SKU-1');
      expect(result).toEqual({
         productsBySku: {
            'SKU-1': { sku: 'SKU-1', price: 100 },
         },
         netPriceFamiliesBySku: {
            'SKU-1': { product_code: 'SKU-1', net_price: 72 },
         },
      });
   });

   it('returns empty maps without calling fetch when sku list is empty', async () => {
      const fetchMock = vi.fn();
      vi.stubGlobal('fetch', fetchMock);

      const result = await getQuoteProductsContext([]);

      expect(fetchMock).not.toHaveBeenCalled();
      expect(result).toEqual({ productsBySku: {}, netPriceFamiliesBySku: {} });
   });

   it('throws when request fails', async () => {
      vi.stubGlobal(
         'fetch',
         vi.fn().mockResolvedValue({
            ok: false,
            json: vi.fn(),
         })
      );

      await expect(getQuoteProductsContext(['SKU-1'])).rejects.toThrow(
         'Erreur lors du chargement du contexte produit'
      );
   });
});