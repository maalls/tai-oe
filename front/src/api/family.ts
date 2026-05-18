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

export async function getFamily(id: string): Promise<Family> {
   const res = await fetch(`/api/family/${id}`);
   if (!res.ok) throw new Error('Famille introuvable');
   return await res.json();
}

export async function createFamily(data: FamilyCreate): Promise<Family> {
   const res = await fetch('/api/family', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
   });
   if (!res.ok) throw new Error('Erreur lors de la création de la famille');
   return await res.json();
}

export async function updateFamily(id: string, data: FamilyUpdate): Promise<Family> {
   const res = await fetch(`/api/family/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
   });
   if (!res.ok) throw new Error('Erreur lors de la mise à jour de la famille');
   return await res.json();
}

export async function deleteFamily(id: string): Promise<void> {
   const res = await fetch(`/api/family/${id}`, {
      method: 'DELETE',
   });
   if (!res.ok) throw new Error('Erreur lors de la suppression de la famille');
}
