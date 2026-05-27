import { authFetch } from './authFetch';
import { apiFetch } from './apiFetch';

export interface OpportunityDocument {
   id: string;
   opportunity_id?: string | null;
   type?: string | null;
   status?: string | null;
   title?: string | null;
   external_ref?: string | null;
   currency?: string | null;
   total_excl_tax?: number | null;
   total_tax?: number | null;
   total_incl_tax?: number | null;
   storage_key?: string | null;
   issued_at?: string | null;
   received_at?: string | null;
   created_at?: string | null;
}

export async function listOpportunityDocuments(
   opportunityId: string
): Promise<OpportunityDocument[]> {
   const res = await apiFetch(`/api/document?opportunity_id=${encodeURIComponent(opportunityId)}`);
   if (!res.ok) throw new Error('Erreur lors du chargement des documents');
   return await res.json();
}

export async function getOpportunityDocument(
   opportunityId: string,
   documentId: string
): Promise<OpportunityDocument> {
   const res = await apiFetch(
      `/api/document/${documentId}?opportunity_id=${encodeURIComponent(opportunityId)}`
   );
   if (!res.ok) throw new Error('Erreur lors du chargement du document');
   return await res.json();
}

export async function deleteOpportunityDocument(documentId: string, token: string): Promise<void> {
   const res = await authFetch(
      `/api/document/${documentId}`,
      {
         method: 'DELETE',
      },
      token
   );
   if (!res.ok) {
      const payload = await res.json().catch(() => ({}));
      throw new Error(payload?.message || 'Erreur lors de la suppression du document');
   }
}

export async function clearDocumentStorageKey(
   documentId: string,
   token: string
): Promise<OpportunityDocument> {
   const res = await authFetch(
      `/api/document/${documentId}/storage-key`,
      {
         method: 'PUT',
         headers: {
            'Content-Type': 'application/json',
         },
         body: JSON.stringify({ storage_key: null }),
      },
      token
   );
   if (!res.ok) {
      const payload = await res.json().catch(() => ({}));
      throw new Error(payload?.message || payload?.error || 'Erreur lors de la suppression du PDF');
   }
   return await res.json();
}

export async function updateDocumentStatus(
   documentId: string,
   status: string,
   token: string
): Promise<OpportunityDocument> {
   const res = await authFetch(
      `/api/document/${documentId}/status`,
      {
         method: 'PUT',
         headers: {
            'Content-Type': 'application/json',
         },
         body: JSON.stringify({ status }),
      },
      token
   );
   if (!res.ok) {
      const payload = await res.json().catch(() => ({}));
      throw new Error(
         payload?.message || payload?.error || 'Erreur lors de la mise à jour du statut du document'
      );
   }
   return await res.json();
}
