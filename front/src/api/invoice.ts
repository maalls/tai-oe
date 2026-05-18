import type { Contact } from './contact';
import type { OpportunityDocument } from './document';
import type { SentEmailRecord } from './opportunity';

export interface OpportunityInvoiceView {
   invoice: OpportunityDocument;
   sent_email: SentEmailRecord | null;
   default_contact: Contact | null;
}

export async function listOpportunityInvoices(
   opportunityId: string
): Promise<OpportunityDocument[]> {
   const res = await fetch(`/api/invoice?opportunity_id=${encodeURIComponent(opportunityId)}`);
   if (!res.ok) throw new Error('Erreur lors du chargement des factures');
   return await res.json();
}

export async function getOpportunityInvoiceView(
   opportunityId: string,
   invoiceId: string
): Promise<OpportunityInvoiceView> {
   const res = await fetch(
      `/api/invoice/${invoiceId}/view?opportunity_id=${encodeURIComponent(opportunityId)}`
   );
   if (!res.ok) throw new Error('Erreur lors du chargement de la facture');
   return await res.json();
}
