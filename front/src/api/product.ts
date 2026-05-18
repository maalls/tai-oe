export interface ProductDetail {
   id: string | number;
   marque?: string;
   refciale?: string;
   libelle240?: string;
   tarif?: string | number;
   brand_id?: string | null;
   brand_name?: string | null;
   family_codes?: string[];
   vector_text?: string;
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

export async function getProduct(productId: string): Promise<ProductDetail> {
   const res = await fetch(`/api/products/${encodeURIComponent(productId)}`);
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
   const res = await fetch(`/api/products/search${suffix ? `?${suffix}` : ''}`);
   if (!res.ok) throw new Error('Erreur lors du chargement des produits');

   const payload = await res.json();
   return {
      products: payload.products || [],
      totalCount: payload.total_count || 0,
   };
}
