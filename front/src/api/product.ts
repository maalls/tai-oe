import { apiFetch } from './apiFetch';

export interface ProductDetail {
   id: string | number;
   marque?: string;
   refciale?: string;
   libelle240?: string;
   tarif?: string | number;
   batch?: string | number | null;
   brand_id?: string | null;
   brand_name?: string | null;
   family_codes?: string[];
   media?: ProductMedia[];
   vector_text?: string;
}

export interface ProductMedia {
   id?: string;
   url: string;
   type?: string | null;
   source?: string | null;
   position?: number | null;
   created_at?: string | null;
}

export interface SearchProductsParams {
   query?: string;
   marque?: string;
   refciale?: string;
   tarif?: string;
   family?: string;
   exactMatch?: boolean;
   limit?: number;
   offset?: number;
}

export interface SearchProductsResponse {
   products: ProductDetail[];
   totalCount: number;
}

export interface QuoteContextProductFamily {
   family: {
      id?: string;
      name?: string | null;
      code?: string | null;
      type?: string | null;
      discount?: number | null;
      minimum_margin?: number | null;
      target_margin?: number | null;
      quantity?: number | null;
      net_price?: number | null;
      product_code?: string | null;
   };
}

export interface QuoteContextProduct {
   id: string | number;
   sku: string;
   name?: string | null;
   price?: number | null;
   brand_id?: string | null;
   brand?: {
      id?: string | null;
      name?: string | null;
      marque?: string | null;
      minimum_margin?: number | null;
      target_margin?: number | null;
   } | null;
   product_family?: QuoteContextProductFamily[];
}

export interface QuoteContextFamily {
   id?: string;
   name?: string | null;
   code?: string | null;
   type?: string | null;
   product_code?: string | null;
   quantity?: number | null;
   discount?: number | null;
   minimum_margin?: number | null;
   target_margin?: number | null;
   net_price?: number | null;
}

export interface QuoteProductsContext {
   productsBySku: Record<string, QuoteContextProduct>;
   netPriceFamiliesBySku: Record<string, QuoteContextFamily>;
}

export async function getProduct(productId: string): Promise<ProductDetail> {
   const res = await apiFetch(`/api/products/${encodeURIComponent(productId)}`);
   if (!res.ok) throw new Error('Erreur lors du chargement du produit');
   return await res.json();
}

export async function searchProducts(
   params: SearchProductsParams = {}
): Promise<SearchProductsResponse> {
   const query = new URLSearchParams();

   if (params.query) query.set('query', params.query);
   if (params.marque) query.set('marque', params.marque);
   if (params.refciale) query.set('refciale', params.refciale);
   if (params.tarif) query.set('tarif', params.tarif);
   if (params.family) query.set('family', params.family);
   if (params.exactMatch) query.set('exact_match', 'true');
   if (typeof params.limit === 'number') query.set('limit', String(params.limit));
   if (typeof params.offset === 'number') query.set('offset', String(params.offset));

   const suffix = query.toString();
   const res = await apiFetch(`/api/products/search${suffix ? `?${suffix}` : ''}`);
   if (!res.ok) throw new Error('Erreur lors du chargement des produits');

   const payload = await res.json();
   return {
      products: payload.products || [],
      totalCount: payload.total_count || 0,
   };
}

export async function getQuoteProductsContext(skus: string[]): Promise<QuoteProductsContext> {
   const normalizedSkus = Array.from(new Set(skus.map((sku) => sku.trim()).filter(Boolean)));
   if (normalizedSkus.length === 0) {
      return { productsBySku: {}, netPriceFamiliesBySku: {} };
   }

   const query = new URLSearchParams();
   normalizedSkus.forEach((sku) => query.append('sku', sku));

   const res = await apiFetch(`/api/products/quote-context?${query.toString()}`);
   if (!res.ok) throw new Error('Erreur lors du chargement du contexte produit');

   const payload = await res.json();
   const productsBySku = (payload.products || []).reduce(
      (acc: Record<string, QuoteContextProduct>, product: QuoteContextProduct) => {
         if (product?.sku) {
            acc[product.sku] = product;
         }
         return acc;
      },
      {}
   );
   const netPriceFamiliesBySku = (payload.net_price_families || []).reduce(
      (acc: Record<string, QuoteContextFamily>, family: QuoteContextFamily) => {
         const sku = String(family?.product_code || '').trim();
         if (sku) {
            acc[sku] = family;
         }
         return acc;
      },
      {}
   );

   return { productsBySku, netPriceFamiliesBySku };
}
