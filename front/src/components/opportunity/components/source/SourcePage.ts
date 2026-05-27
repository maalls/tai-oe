import { ref, onMounted, watch, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useAuth } from '../../../../stores/auth';
import { authFetch } from '../../../../api/authFetch';
import OpportunityHeader from '../../OpportunityHeader.vue';
import { useI18n } from '../../../../i18n/useI18n';
import { useOpportunitySource } from '../../../../composables/useOpportunitySource';
import {
   createManualOpportunity,
   extractOpportunityAuthorContact,
   getOpportunitySummary,
   updateOpportunityName,
} from '../../../../api/opportunity';

export function useSourcePage() {
   const { t } = useI18n();
   const route = useRoute();
   const router = useRouter();

   const opportunityId = computed(() => route.params.id as string);
   const { getValidToken } = useAuth();

   const isLoading = ref(true);
   const isExtracting = ref(false);
   const isScanning = ref(false);
   const opportunity = ref<any>(null);
   const scannedRFPData = ref<any>(null);
   const headerRef = ref<InstanceType<typeof OpportunityHeader> | null>(null);
   const opportunityName = ref('');
   const isSavingName = ref(false);
   const nameError = ref('');

   const {
      source,
      sourceEmail,
      sourceDocument,
      loadParticipants,
      loadSourceFromOpportunity,
      resetSourceState,
   } = useOpportunitySource(opportunityId);

   // RFQ Form state
   const rfqForm = ref<{ message: string; file: File | null }>({
      message: '',
      file: null,
   });
   const isCreatingRFQ = ref(false);
   const rfqErrorMessage = ref('');
   const rfqSuccessMessage = ref('');
   const systemPrompt = ref('');

   const loadSystemPrompt = async () => {
      try {
         const response = await fetch('/api/prompt/opportunity/source');
         if (!response.ok) {
            console.error('[SourcePage] Failed to load system prompt:', response.status);
            return;
         }
         systemPrompt.value = await response.text();
      } catch (error) {
         console.error('[SourcePage] Error loading system prompt:', error);
      }
   };

   const formatEmailDate = (dateString: string) => {
      if (!dateString) return '';
      const date = new Date(dateString);
      return date.toLocaleString();
   };

   const extractAuthorAsContact = async () => {
      if (!sourceEmail.value || !opportunity.value) return;

      isExtracting.value = true;
      try {
         const { from_name, from_email } = sourceEmail.value;
         const token = await getValidToken();
         if (!token) {
            alert('Unauthorized');
            return;
         }

         await extractOpportunityAuthorContact(
            opportunityId.value,
            String(from_email || ''),
            from_name || null,
            token
         );

         // Reload participants to show the newly added contact
         await loadParticipants();

         alert('Author extracted and linked as contact');
      } catch (error) {
         console.error('[SourcePage] Unexpected error extracting author:', error);
         alert('Error extracting author information');
      } finally {
         isExtracting.value = false;
      }
   };

   const scanAttachmentForRFQ = async (attachmentId: string) => {
      isScanning.value = true;
      try {
         console.log('[SourcePage] Scanning attachment:', attachmentId);

         const response = await authFetch('/api/document/extract-rfp', {
            method: 'POST',
            headers: {
               'Content-Type': 'application/json',
            },
            body: JSON.stringify({
               document_id: attachmentId,
            }),
         });

         console.log('[SourcePage] Response status:', response.status);

         if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || `HTTP ${response.status}`);
         }

         const result = await response.json();

         if (result.status === 'ok') {
            scannedRFPData.value = result.data;
            console.log('[SourcePage] Extracted RFQ data:', result.data);
            alert(
               `✅ RFQ Scanned!\n\nProducts found: ${result.data.products?.length || 0}\nCompany: ${result.data.contact?.company_name || 'Unknown'}`
            );
         } else {
            throw new Error(result.message || 'Failed to scan RFQ-4');
         }
      } catch (error) {
         console.error('[SourcePage] Error scanning RFQ:', error);
         alert(`Error scanning RFQ: ${error instanceof Error ? error.message : 'Unknown error'}`);
      } finally {
         isScanning.value = false;
      }
   };

   const loadOpportunity = async () => {
      isLoading.value = true;

      if (opportunityId.value === 'new') {
         try {
            const token = await getValidToken();
            if (!token) {
               console.error('[SourcePage] No authenticated token');
               opportunity.value = null;
               resetSourceState();
               isLoading.value = false;
               return;
            }

            const created = await createManualOpportunity('New Opportunity', token);

            if (!created?.id) {
               console.error('[SourcePage] Error creating opportunity: no id returned');
               opportunity.value = null;
               resetSourceState();
               isLoading.value = false;
               return;
            }

            await router.replace(`/opportunities/${created.id}/source`);
            return;
         } catch (error) {
            console.error('[SourcePage] Error creating new opportunity:', error);
            opportunity.value = null;
            resetSourceState();
            isLoading.value = false;
            return;
         }
      }

      try {
         const opportunityData = await getOpportunitySummary(opportunityId.value);
         if (opportunityData) {
            opportunity.value = opportunityData;
            opportunityName.value = opportunityData.name || '';
         }

         await loadSourceFromOpportunity();
      } catch (error) {
         console.error('[SourcePage] Unexpected error:', error);
      } finally {
         isLoading.value = false;
      }
   };

   const onFileSelected = (event: Event) => {
      const target = event.target as HTMLInputElement;
      rfqForm.value.file = target.files?.[0] || null;
   };

   const saveOpportunityName = async () => {
      if (!opportunity.value || !opportunityId.value || opportunityId.value === 'new') return;
      const trimmed = opportunityName.value.trim();
      if (trimmed === (opportunity.value?.name || '').trim()) return;

      isSavingName.value = true;
      nameError.value = '';

      try {
         const token = await getValidToken();
         if (!token) {
            nameError.value = 'Unauthorized';
            return;
         }

         await updateOpportunityName(opportunityId.value, trimmed, token);

         opportunity.value.name = trimmed;
         headerRef.value?.refreshOpportunity?.();
      } catch (err) {
         nameError.value = err instanceof Error ? err.message : 'Failed to update name.';
      } finally {
         isSavingName.value = false;
      }
   };

   const saveDocumentContent = async (documentId: string, content: string) => {
      try {
         const response = await authFetch('/api/document/update-content', {
            method: 'POST',
            headers: {
               'Content-Type': 'application/json',
            },
            body: JSON.stringify({
               document_id: documentId,
               content: content,
            }),
         });

         if (!response.ok) {
            const error = await response.json();
            console.error('[SourcePage] Error updating document content:', error);
            alert('Failed to save content: ' + (error.message || 'Unknown error'));
            throw new Error(error.message || `HTTP ${response.status}`);
         }

         const result = await response.json();

         if (result.status !== 'ok') {
            throw new Error(result.message || 'Failed to update content');
         }

         // Reload source to show updated content
         await loadSourceFromOpportunity();
      } catch (error) {
         console.error('[SourcePage] Unexpected error saving content:', error);
         throw error;
      }
   };

   const submitRFQ = async () => {
      const hasMessage = !!rfqForm.value.message.trim();
      const hasFile = !!rfqForm.value.file;
      if (!hasMessage && !hasFile) {
         rfqErrorMessage.value = 'Message or PDF attachment is required';
         return;
      }

      isCreatingRFQ.value = true;
      rfqErrorMessage.value = '';
      rfqSuccessMessage.value = '';

      try {
         const formData = new FormData();
         formData.append('message', rfqForm.value.message);

         // Send opportunity name only if provided
         const nameToSend = opportunityName.value?.trim();
         if (nameToSend) {
            formData.append('opportunity_name', nameToSend);
         }

         if (rfqForm.value.file) {
            formData.append('file', rfqForm.value.file);
         }

         // Use the opportunity-specific RFQ endpoint
         const response = await authFetch(
            `/api/opportunity/${opportunityId.value}/rfq/create-from-text`,
            {
               method: 'POST',
               body: formData,
            }
         );

         const result = await response.json().catch(() => ({}));

         if (response.ok && result.status === 'ok') {
            rfqSuccessMessage.value = 'RFQ source created successfully!';
            rfqForm.value.message = '';
            rfqForm.value.file = null;

            console.log('[SourcePage] RFQ created successfully:', result);

            const isRfpUploadFromResult =
               result?.opportunity?.source === 'rfp_upload' ||
               result?.opportunity?.source_type === 'rfp_upload';

            // If a new opportunity was created, redirect to it immediately
            if (
               result.opportunity &&
               result.opportunity.id &&
               result.opportunity.id !== opportunityId.value
            ) {
               console.log('[SourcePage] Redirecting to new opportunity:', result.opportunity.id);
               if (isRfpUploadFromResult) {
                  router.push(`/opportunities/${result.opportunity.id}/quote`);
               } else {
                  router.push(`/opportunities/${result.opportunity.id}/source`);
               }
               return;
            }

            // Reload opportunity data to show new source
            await loadOpportunity();

            // If this opportunity originated from an RFP upload, go straight to quote
            if (
               source.value.sourceType === 'rfp_upload' ||
               opportunity.value?.source === 'rfp_upload'
            ) {
               router.push(`/opportunities/${opportunityId.value}/quote`);
               return;
            }
         } else {
            rfqErrorMessage.value =
               result.message || `Failed to create RFQ (HTTP ${response.status})`;
         }
      } catch (error) {
         rfqErrorMessage.value = `Error: ${error instanceof Error ? error.message : 'Unknown error'}`;
      } finally {
         isCreatingRFQ.value = false;
      }
   };

   onMounted(() => {
      // Reset all state when component mounts
      isLoading.value = true;
      opportunity.value = null;
      resetSourceState();

      loadSystemPrompt();

      loadOpportunity();
   });

   // Watch for route parameter changes and reload
   watch(
      () => route.params.id,
      (newId, oldId) => {
         if (newId && newId !== oldId) {
            // Reset all state when opportunity ID changes
            isLoading.value = true;
            opportunity.value = null;
            resetSourceState();
            rfqForm.value = { message: '', file: null };
            rfqErrorMessage.value = '';
            rfqSuccessMessage.value = '';

            loadOpportunity();
         }
      }
   );

   return {
      t,
      opportunityId,
      isLoading,
      isExtracting,
      isScanning,
      opportunity,
      scannedRFPData,
      headerRef,
      opportunityName,
      isSavingName,
      nameError,
      source,
      sourceEmail,
      sourceDocument,
      rfqForm,
      isCreatingRFQ,
      rfqErrorMessage,
      rfqSuccessMessage,
      systemPrompt,
      formatEmailDate,
      extractAuthorAsContact,
      scanAttachmentForRFQ,
      saveOpportunityName,
      saveDocumentContent,
      submitRFQ,
      onFileSelected,
   };
}
