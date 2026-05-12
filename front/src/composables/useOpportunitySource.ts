import { ref, computed } from 'vue';
import { supabase } from '../lib/supabase';

type MaybeRef<T> = T | { value: T };

export const useOpportunitySource = (opportunityId: MaybeRef<string>) => {
   const resolveOpportunityId = () =>
      typeof opportunityId === 'string' ? opportunityId : opportunityId.value;

   const sourceEmail = ref<any>(null);
   const sourceDocument = ref<any>(null);
   const sourceType = ref<string | null>(null);
   const participants = ref<any[]>([]);
   const attachments = ref<any[]>([]);

   const formatEmailDate = (dateString: string) => {
      if (!dateString) return '';
      const date = new Date(dateString);
      return date.toLocaleString();
   };

   const formatRole = (role: string) => {
      if (!role) return 'Recipient';
      if (role.includes('_')) {
         return role
            .split('_')
            .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
      }
      const roles: Record<string, string> = {
         from: 'From',
         to: 'To',
         cc: 'Cc',
         bcc: 'Bcc',
      };
      return roles[role.toLowerCase()] || role;
   };

   const formatBodySize = (body: string | number): string => {
      if (body === null || body === undefined || body === '') return '0 KB';
      const bytes = typeof body === 'string' ? new Blob([body]).size : body;
      const kb = bytes / 1024;
      if (kb < 1024) {
         return `${kb.toFixed(2)} KB`;
      }
      const mb = kb / 1024;
      return `${mb.toFixed(2)} MB`;
   };

   const formatFileSize = (bytes: number): string => {
      if (!bytes) return '0 B';
      const k = 1024;
      const sizes = ['B', 'KB', 'MB', 'GB'];
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
   };

   const isHtmlContent = (content: string): boolean => {
      if (!content) return false;
      return /<[^>]*>/.test(content);
   };

   const sanitizeHtml = (html: string): string => {
      let cleaned = html.replace(/cid:[^\s"'>\]<]*/g, '');
      cleaned = cleaned.replace(/\s(src|href|data)=["']?cid:[^\s"'>]*/g, '');

      const temp = document.createElement('div');
      temp.innerHTML = cleaned;

      const dangerousTags = ['script', 'iframe', 'object', 'embed', 'form'];
      dangerousTags.forEach((tag) => {
         const elements = temp.querySelectorAll(tag);
         elements.forEach((el) => el.remove());
      });

      const styleTags = temp.querySelectorAll('style');
      styleTags.forEach((tag) => tag.remove());

      const imgTags = temp.querySelectorAll('img');
      imgTags.forEach((img) => {
         const src = img.getAttribute('src') || '';
         if (!src || src.trim() === '') {
            img.remove();
         }
      });

      temp.querySelectorAll('*').forEach((el) => {
         Array.from(el.attributes).forEach((attr) => {
            if (attr.name.startsWith('on')) {
               el.removeAttribute(attr.name);
            }
            if (
               ['src', 'href', 'data'].includes(attr.name) &&
               (!attr.value || attr.value.trim() === '')
            ) {
               el.removeAttribute(attr.name);
            }
         });

         if (el instanceof HTMLElement && el.hasAttribute('style')) {
            el.removeAttribute('style');
         }
      });

      return temp.innerHTML;
   };

   const getAttachmentUrl = (attachment: any): string => {
      if (attachment?.id && sourceEmail.value?.id) {
         return `/api/email-attachment/${attachment.id}/download`;
      }
      const key = attachment?.storage_key || attachment?.storage_path || '';
      return `/api/storage/${key}`;
   };

   const isPdfAttachment = (attachment: any): boolean => {
      const name =
         attachment?.filename || attachment?.storage_key || attachment?.storage_path || '';
      const mime = (attachment?.mime_type || '').toLowerCase();
      return mime === 'application/pdf' || name.toLowerCase().endsWith('.pdf');
   };

   const pdfAttachments = computed(() => attachments.value.filter(isPdfAttachment));

   const source = computed(() => ({
      sourceType: sourceType.value ?? undefined,
      email: sourceEmail.value,
      document: sourceDocument.value,
      attachments: attachments.value,
      pdfAttachments: pdfAttachments.value,
      participants: participants.value,
      formatEmailDate,
      formatBodySize,
      formatFileSize,
      formatRole,
      isHtmlContent,
      sanitizeHtml,
      getAttachmentUrl,
   }));

   const loadParticipants = async () => {
      try {
         const { data, error } = await supabase
            .from('opportunity_participant')
            .select('role, contact_id, contact:contact_id(id, name, email)')
            .eq('opportunity_id', resolveOpportunityId());

         if (error) {
            console.error('[OpportunitySource] Error loading participants:', error);
            return;
         }

         participants.value = data || [];
      } catch (error) {
         console.error('[OpportunitySource] Unexpected error loading participants:', error);
      }
   };

   const loadAttachments = async () => {
      if (sourceEmail.value?.id) {
         try {
            const { data, error } = await supabase
               .from('email_attachment')
               .select('id, filename, mime_type, size, storage_path')
               .eq('email_id', sourceEmail.value.id);

            if (error) {
               console.error('[OpportunitySource] Error loading email attachments:', error);
               return;
            }

            attachments.value = data || [];
         } catch (error) {
            console.error('[OpportunitySource] Unexpected error loading email attachments:', error);
         }
         return;
      }

      if (sourceDocument.value) {
         try {
            const { data, error } = await supabase
               .from('document')
               .select('id, title, storage_key, created_at')
               .eq('opportunity_id', resolveOpportunityId())
               .eq('type', 'ATTACHMENT');

            if (error) {
               console.error('[OpportunitySource] Error loading document attachments:', error);
               return;
            }

            const rows = (data as any[]) || [];

            // Fetch file sizes from storage API for each attachment
            const attachmentsWithSize = await Promise.all(
               rows.map(async (doc) => {
                  let size = 0;
                  if (doc.storage_key) {
                     try {
                        const url = `/api/storage/${doc.storage_key}`;
                        const response = await fetch(url, { method: 'HEAD' });
                        const contentLength = response.headers.get('Content-Length');
                        if (contentLength) {
                           size = parseInt(contentLength, 10);
                        }
                     } catch (err) {
                        console.warn(`Failed to fetch size for ${doc.storage_key}:`, err);
                     }
                  }

                  return {
                     id: doc.id,
                     filename: doc.title?.replace('Attachment: ', '') || doc.storage_key,
                     storage_key: doc.storage_key,
                     created_at: doc.created_at,
                     mime_type: doc.mime_type,
                     size,
                  };
               })
            );

            attachments.value = attachmentsWithSize;
         } catch (error) {
            console.error(
               '[OpportunitySource] Unexpected error loading document attachments:',
               error
            );
         }
      }
   };

   const loadSourceEmail = async (emailId: string) => {
      try {
         const { data, error } = await supabase
            .from('email')
            .select('*')
            .eq('id', emailId)
            .single();

         if (error) {
            console.error('[OpportunitySource] Error loading source email:', error);
            return;
         }

         sourceEmail.value = data;
         sourceDocument.value = null;
         await loadAttachments();
      } catch (error) {
         console.error('[OpportunitySource] Unexpected error loading source email:', error);
      }
   };

   const loadSourceDocument = async (documentId: string) => {
      try {
         const { data, error } = await supabase
            .from('document')
            .select('*')
            .eq('id', documentId)
            .single();

         if (error) {
            console.error('[OpportunitySource] Error loading source document:', error);
            return;
         }

         const doc = data as any;
         sourceDocument.value = doc;
         sourceEmail.value = null;

         if (doc?.storage_key) {
            try {
               const url = `/api/storage/${doc.storage_key}`;
               const response = await fetch(url, {
                  signal: AbortSignal.timeout(10000),
               });

               if (response.ok) {
                  const content = await response.text();
                  sourceDocument.value.content = content;
               } else {
                  console.error(
                     '[OpportunitySource] Failed to load document content:',
                     response.status
                  );
               }
            } catch (err) {
               console.error('[OpportunitySource] Error loading document content:', err);
               sourceDocument.value.content = '[Error loading document content]';
            }
         }

         await loadAttachments();
      } catch (error) {
         console.error('[OpportunitySource] Unexpected error loading source document:', error);
      }
   };

   const loadSourceFromOpportunity = async () => {
      try {
         const { data, error } = await supabase
            .from('opportunity')
            .select('source, source_reference_id')
            .eq('id', resolveOpportunityId())
            .single();

         if (error) {
            console.error('[OpportunitySource] Error loading opportunity source:', error);
            return;
         }

         const opp = data as any;
         sourceType.value = opp?.source || null;
         if (opp?.source === 'email' && opp?.source_reference_id) {
            await loadSourceEmail(opp.source_reference_id);
         } else if (
            (opp?.source === 'rfp_upload' || opp?.source === 'user_form') &&
            opp?.source_reference_id
         ) {
            await loadSourceDocument(opp.source_reference_id);
         }

         await loadParticipants();
      } catch (error) {
         console.error('[OpportunitySource] Unexpected error loading opportunity source:', error);
      }
   };

   const resetSourceState = () => {
      sourceEmail.value = null;
      sourceDocument.value = null;
      sourceType.value = null;
      participants.value = [];
      attachments.value = [];
   };

   return {
      source,
      sourceEmail,
      sourceDocument,
      participants,
      attachments,
      pdfAttachments,
      formatEmailDate,
      formatBodySize,
      formatFileSize,
      formatRole,
      isHtmlContent,
      sanitizeHtml,
      getAttachmentUrl,
      loadParticipants,
      loadAttachments,
      loadSourceEmail,
      loadSourceDocument,
      loadSourceFromOpportunity,
      resetSourceState,
   };
};
