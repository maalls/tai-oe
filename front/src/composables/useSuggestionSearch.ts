import { supabase } from '../lib/supabase';

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
      const response = await supabase
         .from('product')
         .select('*, brand(*), product_family(family(*))')
         .ilike('sku', `%${query}%`)
         .limit(5);

      if (response.error) {
         throw new Error(response.error.message || 'Product search failed');
      }

      onResults(response.data || []);
   } catch (err) {
      console.error('[searchProductBySku] Search failed:', err);
      const errorMsg = err instanceof Error ? err.message : 'Search failed';
      onResults([], errorMsg);
   }
};
