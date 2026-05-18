export interface OpportunitySourceContact {
   id: string;
   name?: string | null;
   email?: string | null;
}

export interface OpportunitySourceParticipant {
   role?: string | null;
   contact_id?: string | null;
   contact?: OpportunitySourceContact | null;
}

export interface OpportunitySourceAttachment {
   id: string;
   filename?: string | null;
   mime_type?: string | null;
   size?: number | null;
   storage_path?: string | null;
   title?: string | null;
   storage_key?: string | null;
   created_at?: string | null;
}

export interface OpportunitySourcePayload {
   source_type?: string | null;
   email?: Record<string, any> | null;
   document?: Record<string, any> | null;
   participants: OpportunitySourceParticipant[];
   attachments: OpportunitySourceAttachment[];
}

export async function getOpportunitySource(
   opportunityId: string
): Promise<OpportunitySourcePayload> {
   const res = await fetch(`/api/opportunity/${opportunityId}/source`);
   if (!res.ok) throw new Error('Erreur lors du chargement de la source opportunité');
   return await res.json();
}
