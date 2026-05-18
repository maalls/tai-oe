import { afterEach, describe, expect, it, vi } from 'vitest';

import { searchProductBySku } from '../../../../../src/composables/useSuggestionSearch';

describe('searchProductBySku', () => {
   afterEach(() => {
      vi.restoreAllMocks();
   });

   it('fetches suggestions from the products endpoint', async () => {
      const products = [{ id: 'p1', sku: 'SKU-1' }];
      const fetchMock = vi.fn().mockResolvedValue({
         ok: true,
         json: vi.fn().mockResolvedValue({ products }),
      });
      vi.stubGlobal('fetch', fetchMock);
      const onResults = vi.fn();
      const onLoading = vi.fn();

      await searchProductBySku('sku', onResults, onLoading);

      expect(fetchMock).toHaveBeenCalledWith('/api/products?sku=sku&limit=5');
      expect(onLoading).toHaveBeenCalledWith(true);
      expect(onResults).toHaveBeenCalledWith(products);
   });

   it('returns an error when fetch fails', async () => {
      vi.stubGlobal(
         'fetch',
         vi.fn().mockResolvedValue({
            ok: false,
            json: vi.fn(),
         })
      );
      const onResults = vi.fn();
      const onLoading = vi.fn();

      await searchProductBySku('sku', onResults, onLoading);

      expect(onResults).toHaveBeenCalledWith([], 'Product search failed');
   });
});
