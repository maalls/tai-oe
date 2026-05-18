export interface OpportunitySummary {
   id: string;
   account_id?: string | null;
   name?: string | null;
   source?: string | null;
   source_reference_id?: string | null;
}

export async function getOpportunitySummary(opportunityId: string): Promise<OpportunitySummary> {
   const res = await fetch(`/api/opportunity?opportunity_id=${encodeURIComponent(opportunityId)}`);
   if (!res.ok) throw new Error('Erreur lors du chargement de l’opportunité');
   const payload = await res.json();
   if (payload?.status !== 'ok' || !payload?.opportunity) {
      throw new Error(payload?.message || 'Erreur lors du chargement de l’opportunité');
   }
   return payload.opportunity as OpportunitySummary;
}

export async function createManualOpportunity(
   name: string,
   token: string
): Promise<OpportunitySummary> {
   const res = await fetch('/api/opportunities/create-manual', {
      method: 'POST',
      headers: {
         'Content-Type': 'application/json',
         Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ name }),
   });
   if (!res.ok) throw new Error('Erreur lors de la création de l’opportunité');
   const payload = await res.json();
   if (payload?.status !== 'ok' || !payload?.opportunity) {
      throw new Error(payload?.message || 'Erreur lors de la création de l’opportunité');
   }
   return payload.opportunity as OpportunitySummary;
}

export async function updateOpportunityName(
   opportunityId: string,
   name: string,
   token: string
): Promise<OpportunitySummary> {
   const res = await fetch(`/api/opportunity/${opportunityId}/name`, {
      method: 'PUT',
      headers: {
         'Content-Type': 'application/json',
         Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ name }),
   });
   if (!res.ok) throw new Error('Erreur lors de la mise à jour de l’opportunité');
   return await res.json();
}

export async function extractOpportunityAuthorContact(
   opportunityId: string,
   fromEmail: string,
   fromName: string | null,
   token: string
): Promise<{ status: string; contact_id: string; linked: boolean }> {
   const res = await fetch(`/api/opportunity/${opportunityId}/extract-author-contact`, {
      method: 'POST',
      headers: {
         'Content-Type': 'application/json',
         Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ from_email: fromEmail, from_name: fromName }),
   });
   if (!res.ok) throw new Error('Erreur lors de l’extraction du contact auteur');
   return await res.json();
}
