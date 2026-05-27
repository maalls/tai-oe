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

export async function listCatalogBrands(): Promise<CatalogBrand[]> {
   const res = await apiFetch('/api/catalog/brands');
   if (!res.ok) throw new Error('Erreur lors du chargement des marques');
   return await res.json();
}

export async function listCatalogFamilies(): Promise<CatalogFamily[]> {
   const res = await apiFetch('/api/catalog/families');
   if (!res.ok) throw new Error('Erreur lors du chargement des familles');
   return await res.json();
}
