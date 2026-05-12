<template>
   <div v-if="messages.length === 0" class="text-center py-12 text-gray-500">
      {{ t('mail.noMessagesFound') }}
   </div>

   <div v-else class="space-y-2">
      <div
         v-for="message in messages"
         :key="message.id"
         class="bg-white border border-gray-200 rounded-lg overflow-hidden hover:shadow-md transition-all"
         :class="{ 'bg-gray-50': message.labels?.includes('UNREAD') }"
      >
         <MailItem
            :message="message as any"
            :isClassifying="classifyingEmails[message.id] || false"
            :isCreatingOpportunity="creatingOpportunity?.[message.id] || false"
            @expand="$emit('expand', $event)"
            @classify="$emit('classify', $event)"
            @create-opportunity="$emit('create-opportunity', $event)"
            @resync="
               (messageId, providerMessageId) => $emit('resync', messageId, providerMessageId)
            "
            @delete="$emit('delete', $event)"
         />
         <MailItemExpanded
            v-if="expandedMessageIds.has(message.id)"
            :message="message as any"
            :messageBody="messageBody[message.id] || null"
            :isLoadingBody="loadingMessageBody[message.id] || false"
            :attachments="messageAttachments[message.id] || []"
            :isLoadingAttachments="loadingAttachments[message.id] || false"
         />
      </div>
   </div>
</template>

<script setup lang="ts">
import MailItem from './MailItem.vue';
import MailItemExpanded from './MailItemExpanded.vue';
import { useI18n } from '../../i18n/useI18n';

const { t } = useI18n();

interface Message {
   id: string;
   from?: string;
   to?: string;
   provider?: string;
   provider_message_id?: string;
   subject?: string;
   date?: string;
   snippet?: string;
   labels?: string[];
   hasAttachments?: boolean;
   attachmentCount?: number;
   category?: string;
   category_suggestion?: string;
   classification_reason?: string;
   classified_at?: string;
   is_classified?: boolean;
   auth_score?: number;
   is_verified?: boolean;
   spf_status?: string;
   dkim_status?: string;
   dmarc_status?: string;
}

defineProps<{
   messages: Message[];
   expandedMessageIds: Set<string>;
   messageBody: Record<string, any>;
   loadingMessageBody: Record<string, boolean>;
   messageAttachments: Record<string, any[]>;
   loadingAttachments: Record<string, boolean>;
   classifyingEmails: Record<string, boolean>;
   creatingOpportunity?: Record<string, boolean>;
}>();

defineEmits<{
   expand: [messageId: string];
   classify: [messageId: string];
   'create-opportunity': [messageId: string];
   resync: [messageId: string, providerMessageId: string];
   delete: [messageId: string];
}>();
</script>
