import { authFetch } from './authFetch';

export interface OpportunitySummary {
   id: string;
   account_id?: string | null;
   name?: string | null;
   source?: string | null;
   source_reference_id?: string | null;
   stage?: string | null;
   status?: string | null;
   updated_at?: string | null;
}

export interface SentEmailRecord {
   id: string;
   document_id?: string | null;
   subject?: string | null;
   body?: string | null;
   from_email?: string | null;
   to_emails?: string[] | null;
   cc_emails?: string[] | null;
   sent_at?: string | null;
}

export interface OpportunityAdvanceResult {
   status: string;
   opportunity?: OpportunitySummary;
   message?: string;
}

export interface OpportunityStageTransition {
   opportunity_id: string;
   from_stage?: string | null;
   to_stage?: string | null;
   changed_by?: string | null;
   changed_at?: string | null;
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
   const res = await authFetch(
      '/api/opportunities/create-manual',
      {
      method: 'POST',
      headers: {
         'Content-Type': 'application/json',
      },
      body: JSON.stringify({ name }),
      },
      token
   );
   if (!res.ok) throw new Error('Erreur lors de la création de l’opportunité');
   const payload = await res.json();
   if (payload?.status !== 'ok' || !payload?.opportunity) {
      throw new Error(payload?.message || 'Erreur lors de la création de l’opportunité');
   }
   return payload.opportunity as OpportunitySummary;
}

export async function createDraftOpportunity(
   accountId: string,
   token: string,
   options?: { name?: string; source?: string }
): Promise<OpportunitySummary> {
   const res = await authFetch(
      '/api/opportunities/create-draft',
      {
      method: 'POST',
      headers: {
         'Content-Type': 'application/json',
      },
      body: JSON.stringify({
         account_id: accountId,
         name: options?.name ?? '',
         source: options?.source ?? 'user_form',
      }),
      },
      token
   );
   if (!res.ok) throw new Error('Erreur lors de la création de l’opportunité brouillon');
   const payload = await res.json();
   if (payload?.status !== 'ok' || !payload?.opportunity) {
      throw new Error(payload?.message || 'Erreur lors de la création de l’opportunité brouillon');
   }
   return payload.opportunity as OpportunitySummary;
}

export async function updateOpportunityName(
   opportunityId: string,
   name: string,
   token: string
): Promise<OpportunitySummary> {
   const res = await authFetch(
      `/api/opportunity/${opportunityId}/name`,
      {
      method: 'PUT',
      headers: {
         'Content-Type': 'application/json',
      },
      body: JSON.stringify({ name }),
      },
      token
   );
   if (!res.ok) throw new Error('Erreur lors de la mise à jour de l’opportunité');
   return await res.json();
}

export async function updateOpportunityAccount(
   opportunityId: string,
   accountId: string,
   token: string
): Promise<OpportunitySummary> {
   const res = await authFetch(
      `/api/opportunity/${opportunityId}/account`,
      {
      method: 'PUT',
      headers: {
         'Content-Type': 'application/json',
      },
      body: JSON.stringify({ account_id: accountId }),
      },
      token
   );
   if (!res.ok) throw new Error('Erreur lors de la mise à jour du compte de l’opportunité');
   return await res.json();
}

export async function extractOpportunityAuthorContact(
   opportunityId: string,
   fromEmail: string,
   fromName: string | null,
   token: string
): Promise<{ status: string; contact_id: string; linked: boolean }> {
   const res = await authFetch(
      `/api/opportunity/${opportunityId}/extract-author-contact`,
      {
      method: 'POST',
      headers: {
         'Content-Type': 'application/json',
      },
      body: JSON.stringify({ from_email: fromEmail, from_name: fromName }),
      },
      token
   );
   if (!res.ok) throw new Error('Erreur lors de l’extraction du contact auteur');
   return await res.json();
}

export async function getOpportunitySentEmail(
   opportunityId: string,
   documentId?: string
): Promise<SentEmailRecord | null> {
   const query = documentId ? `?document_id=${encodeURIComponent(documentId)}` : '';
   const res = await fetch(`/api/opportunity/${opportunityId}/sent-email${query}`);
   if (!res.ok) throw new Error('Erreur lors du chargement de l’email envoyé');
   const payload = await res.json();
   return (payload?.sent_email as SentEmailRecord | null) || null;
}

export async function searchOpportunities(
   token: string,
   params?: { name?: string; sourceReferenceId?: string }
): Promise<OpportunitySummary[]> {
   const query = new URLSearchParams();
   if (params?.name) {
      query.set('name', params.name);
   }
   if (params?.sourceReferenceId) {
      query.set('source_reference_id', params.sourceReferenceId);
   }
   const suffix = query.size > 0 ? `?${query.toString()}` : '';
   const res = await authFetch(`/api/opportunities/search${suffix}`, {}, token);
   if (!res.ok) throw new Error('Erreur lors du chargement des opportunités');
   const payload = await res.json();
   return (payload?.opportunities as OpportunitySummary[]) || [];
}

export async function advanceOpportunityStage(
   opportunityId: string,
   stage: string
): Promise<OpportunityAdvanceResult> {
   const res = await fetch('/api/opportunity/advance', {
      method: 'POST',
      headers: {
         'Content-Type': 'application/json',
      },
      body: JSON.stringify({ opportunity_id: opportunityId, stage }),
   });
   const payload = await res.json();
   if (!res.ok || payload?.status === 'error') {
      throw new Error(payload?.message || 'Erreur lors de la mise à jour du stage');
   }
   return payload as OpportunityAdvanceResult;
}

export async function getOpportunityStageHistory(
   opportunityId: string,
   limit = 10
): Promise<OpportunityStageTransition[]> {
   const res = await fetch(
      `/api/opportunity/${opportunityId}/stage-history?limit=${encodeURIComponent(String(limit))}`
   );
   if (!res.ok) throw new Error('Erreur lors du chargement de l’historique des stages');
   return await res.json();
}

export async function updateOpportunityStageState(
   opportunityId: string,
   stage: string,
   status: string,
   token: string
): Promise<{ id: string; stage: string; status: string }> {
   const res = await authFetch(
      `/api/opportunity/${opportunityId}/stage-state`,
      {
      method: 'PUT',
      headers: {
         'Content-Type': 'application/json',
      },
      body: JSON.stringify({ stage, status }),
      },
      token
   );
   const payload = await res.json();
   if (!res.ok) {
      throw new Error(
         payload?.message || payload?.error || 'Erreur lors de la mise à jour du stage'
      );
   }
   return payload;
}
