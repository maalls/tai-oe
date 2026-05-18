export interface EmailAttachment {
   id: string;
   filename?: string | null;
   mime_type?: string | null;
   size?: number | null;
   storage_path?: string | null;
}

export async function listEmailAttachments(
   emailId: string,
   token: string
): Promise<EmailAttachment[]> {
   const res = await fetch(`/api/email/${encodeURIComponent(emailId)}/attachments`, {
      headers: {
         Authorization: `Bearer ${token}`,
      },
   });

   if (!res.ok) {
      const payload = await res.json().catch(() => ({}));
      throw new Error(
         payload?.message || payload?.error || 'Erreur lors du chargement des pieces jointes'
      );
   }

   const payload = await res.json();
   return payload.attachments || [];
}