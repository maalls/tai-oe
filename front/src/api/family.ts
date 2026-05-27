import { apiFetch } from './apiFetch';

export interface Family {
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
   created_at?: string | null;
   updated_at?: string | null;
}

export interface FamilyCreate {
   name?: string | null;
   code?: string | null;
   type: string;
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
}

export type FamilyUpdate = Partial<FamilyCreate>;

export interface FamilyDiscountLine {
   id: string;
   position: number;
   quantity: number;
   unit: string;
   unit_price_excl_tax: number;
   discount_rate: number;
   sku: string | null;
   line_total_excl_tax: number;
   isNew?: boolean;
}

export interface FamilyDiscountLinesResponse {
   document_id: string | null;
   lines: FamilyDiscountLine[];
}

export async function getFamily(id: string): Promise<Family> {
   const res = await apiFetch(`/api/family/${id}`);
   if (!res.ok) throw new Error('Famille introuvable');
   return await res.json();
}

export async function createFamily(data: FamilyCreate): Promise<Family> {
   const res = await apiFetch('/api/family', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
   });
   if (!res.ok) throw new Error('Erreur lors de la création de la famille');
   return await res.json();
}

export async function updateFamily(id: string, data: FamilyUpdate): Promise<Family> {
   const res = await apiFetch(`/api/family/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
   });
   if (!res.ok) throw new Error('Erreur lors de la mise à jour de la famille');
   return await res.json();
}

export async function deleteFamily(id: string): Promise<void> {
   const res = await apiFetch(`/api/family/${id}`, {
      method: 'DELETE',
   });
   if (!res.ok) throw new Error('Erreur lors de la suppression de la famille');
}

export async function getFamilyDiscountLines(id: string): Promise<FamilyDiscountLinesResponse> {
   const res = await apiFetch(`/api/family/${id}/discount-lines`);
   if (!res.ok) throw new Error('Erreur lors du chargement des lignes de remise');
   return await res.json();
}

export async function saveFamilyDiscountLines(
   id: string,
   lines: FamilyDiscountLine[]
): Promise<FamilyDiscountLinesResponse> {
   const res = await apiFetch(`/api/family/${id}/discount-lines`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ lines }),
   });
   if (!res.ok) throw new Error('Erreur lors de la sauvegarde des lignes de remise');
   return await res.json();
}
