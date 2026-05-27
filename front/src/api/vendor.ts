import { apiFetch } from './apiFetch';

export interface Vendor {
   id: string;
   name: string;
   email?: string | null;
   phone?: string | null;
   website?: string | null;
   created_at: string;
   updated_at: string;
   brand_count?: number | null;
   family_count?: number | null;
   product_count?: number | null;
}

export interface VendorBrand {
   id: string;
   name?: string | null;
   marque?: string | null;
   website?: string | null;
   target_margin?: number | null;
   minimum_margin?: number | null;
   product_count: number;
}

export type VendorCreate = {
   name: string;
   email?: string | null;
   phone?: string | null;
   website?: string | null;
};

export type VendorUpdate = Partial<VendorCreate>;

export async function listVendors(): Promise<Vendor[]> {
   const res = await apiFetch('/api/vendor');
   if (!res.ok) throw new Error('Erreur lors du chargement des fournisseurs');
   return await res.json();
}

export async function getVendor(id: string): Promise<Vendor> {
   const res = await apiFetch(`/api/vendor/${id}`);
   if (!res.ok) throw new Error('Fournisseur introuvable');
   return await res.json();
}

export async function createVendor(data: VendorCreate): Promise<Vendor> {
   const res = await apiFetch('/api/vendor', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
   });
   if (!res.ok) throw new Error('Erreur lors de la création du fournisseur');
   return await res.json();
}

export async function updateVendor(id: string, data: VendorUpdate): Promise<Vendor> {
   const res = await apiFetch(`/api/vendor/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
   });
   if (!res.ok) throw new Error('Erreur lors de la mise à jour du fournisseur');
   return await res.json();
}

export async function deleteVendor(id: string): Promise<{ id: string }> {
   const res = await apiFetch(`/api/vendor/${id}`, { method: 'DELETE' });
   if (!res.ok) throw new Error('Erreur lors de la suppression du fournisseur');
   return await res.json();
}

export async function listVendorBrands(id: string): Promise<VendorBrand[]> {
   const res = await apiFetch(`/api/vendor/${id}/brands`);
   if (!res.ok) throw new Error('Erreur lors du chargement des marques du fournisseur');
   return await res.json();
}
