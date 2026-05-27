import { apiFetch } from './apiFetch';

export interface Brand {
   id: string;
   name: string;
   vendor_id: string;
   website?: string | null;
   email?: string | null;
   phone?: string | null;
   minimum_margin?: number | null;
   target_margin?: number | null;
   created_at: string;
   updated_at: string;
}

export interface BrandCreate {
   name: string;
   website?: string | null;
   email?: string | null;
   phone?: string | null;
   minimum_margin?: number | null;
   target_margin?: number | null;
}

export type BrandUpdate = Partial<BrandCreate>;

export interface BrandFamilyProduct {
   id: string;
   sku: string;
   name?: string | null;
   price?: number | null;
   brand_id?: string | null;
}

export interface BrandFamily {
   id: string;
   name?: string | null;
   code?: string | null;
   type?: string | null;
   brand_id: string;
   product_code?: string | null;
   quantity?: number | null;
   discount?: number | null;
   minimum_margin?: number | null;
   target_margin?: number | null;
   unit?: string | null;
   packing?: string | null;
   lead_time_week?: number | null;
   net_price?: number | null;
   product_family_count: number;
   product?: BrandFamilyProduct | null;
}

export async function getBrand(id: string): Promise<Brand> {
   const res = await apiFetch(`/api/brand/${id}`);
   if (!res.ok) throw new Error('Marque introuvable');
   return await res.json();
}

export async function createBrand(data: BrandCreate): Promise<Brand> {
   const res = await apiFetch('/api/brand', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
   });
   if (!res.ok) throw new Error('Erreur lors de la création de la marque');
   return await res.json();
}

export async function updateBrand(id: string, data: BrandUpdate): Promise<Brand> {
   const res = await apiFetch(`/api/brand/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
   });
   if (!res.ok) throw new Error('Erreur lors de la mise à jour de la marque');
   return await res.json();
}

export async function listBrandFamilies(id: string): Promise<BrandFamily[]> {
   const res = await apiFetch(`/api/brand/${id}/families`);
   if (!res.ok) throw new Error('Erreur lors du chargement des familles de la marque');
   return await res.json();
}
