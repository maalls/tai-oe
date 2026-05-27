import { apiFetch } from '../api/apiFetch';

/**
 * Searches the product table by SKU with debouncing.
 * Used in both Quote and Family tables for product code/SKU suggestions.
 */
export const searchProductBySku = async (
   query: string,
   onResults: (products: any[], error?: string) => void,
   onLoading: (loading: boolean) => void
) => {
   onLoading(true);

   try {
      const response = await apiFetch(`/api/products?sku=${encodeURIComponent(query)}&limit=5`);
      if (!response.ok) {
         throw new Error('Product search failed');
      }

      const payload = await response.json();
      onResults(payload.products || []);
   } catch (err) {
      console.error('[searchProductBySku] Search failed:', err);
      const errorMsg = err instanceof Error ? err.message : 'Search failed';
      onResults([], errorMsg);
   }
};
