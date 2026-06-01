import { apiFetch } from './apiFetch';

export interface CatalogBrand {
   id: string;
   name?: string | null;
   website?: string | null;
   email?: string | null;
   phone?: string | null;
   created_at?: string | null;
}

export interface CatalogFamily {
   id: string;
   name?: string | null;
   type?: string | null;
   brand_id: string;
}

export interface CatalogFamiliesResponse {
   items: CatalogFamily[];
   total: number;
}

export async function listCatalogBrands(): Promise<CatalogBrand[]> {
   const res = await apiFetch('/api/catalog/brands');
   if (!res.ok) throw new Error('Erreur lors du chargement des marques');
   return await res.json();
}

export async function listCatalogFamilies(params?: {
   brand_id?: string;
   limit?: number;
   offset?: number;
   with_total?: boolean;
}): Promise<CatalogFamily[] | CatalogFamiliesResponse> {
   const search = new URLSearchParams();
   if (params?.brand_id) search.set('brand_id', params.brand_id);
   if (params?.limit !== undefined) search.set('limit', params.limit.toString());
   if (params?.offset !== undefined) search.set('offset', params.offset.toString());
   if (params?.with_total) search.set('with_total', 'true');
   const query = search.toString();
   const url = query ? `/api/catalog/families?${query}` : '/api/catalog/families';
   const res = await apiFetch(url);
   if (!res.ok) throw new Error('Erreur lors du chargement des familles');
   return await res.json();
}
