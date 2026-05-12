export interface MailMessage {
   id: string;
   provider?: string;
   provider_message_id?: string;
   from_raw?: any;
   from_name?: string;
   from_email?: string;
   from?: string;
   to?: string;
   cc_email?: string;
   subject?: string;
   email_date?: string;
   snippet?: string;
   labels?: string[];
   hasAttachments?: boolean;
   attachmentCount?: number;
   category?: string;
   category_suggestion?: string;
   classification_reason?: string;
   classified_at?: string;
   is_classified?: boolean;
   contact_id?: string;
   account_id?: string;
   auth_score?: number;
   is_verified?: boolean;
   spf_status?: string;
   dkim_status?: string;
   dmarc_status?: string;
   opportunities?: Array<{
      id: string;
      stage?: string;
      name?: string;
      [key: string]: any;
   }>;
}
