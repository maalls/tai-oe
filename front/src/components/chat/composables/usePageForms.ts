/**
 * Composable for accessing parsed page forms data
 */

import { ref, onMounted, type Ref } from 'vue';
import {
   parsePageForms,
   getFormValues,
   getFormData,
   type PageFormsData,
   type FormData,
} from '../utils/formParser';

export interface UsePageFormsReturn {
   formsData: Ref<PageFormsData | null>;
   formValues: Ref<Record<string, Record<string, string | boolean | null>>>;
   collectForms: () => void;
   getFormById: (id: string) => FormData | undefined;
   getFormValues: () => Record<string, Record<string, string | boolean | null>>;
}

export function usePageForms(): UsePageFormsReturn {
   const formsData = ref<PageFormsData | null>(null);
   const formValues = ref<Record<string, Record<string, string | boolean | null>>>({});

   function collectForms() {
      formsData.value = parsePageForms();
      formValues.value = getFormValues();
      console.log('[usePageForms] Forms collected:', formsData.value);
      console.log('[usePageForms] Form values:', formValues.value);
   }

   function getFormById(id: string): FormData | undefined {
      return getFormData(id);
   }

   function updateFormValues() {
      formValues.value = getFormValues();
      return formValues.value;
   }

   onMounted(() => {
      collectForms();
      // Re-collect forms periodically for dynamic changes
      const interval = setInterval(updateFormValues, 5000);
      return () => clearInterval(interval);
   });

   return {
      formsData,
      formValues,
      collectForms,
      getFormById,
      getFormValues: () => updateFormValues(),
   };
}
