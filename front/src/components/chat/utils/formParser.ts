/**
 * Lightweight page form parsing utilities for chat tools.
 */

export type FormFieldValue = string | boolean | null;
export type FormValuesMap = Record<string, Record<string, FormFieldValue>>;

export interface FormData {
   id: string;
   action?: string;
   method?: string;
   fields: Record<string, FormFieldValue>;
}

export interface PageFormsData {
   forms: FormData[];
}

let cachedForms: FormData[] = [];

function extractFormValues(form: HTMLFormElement): Record<string, FormFieldValue> {
   const fields: Record<string, FormFieldValue> = {};
   const elements = Array.from(form.elements) as Array<
      HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement | HTMLButtonElement
   >;

   for (const el of elements) {
      const name = (el as any).name as string;
      if (!name) continue;

      if (el instanceof HTMLInputElement) {
         if (el.type === 'checkbox') {
            fields[name] = el.checked;
         } else if (el.type === 'radio') {
            if (el.checked) fields[name] = el.value;
         } else {
            fields[name] = el.value ?? null;
         }
         continue;
      }

      if (el instanceof HTMLSelectElement || el instanceof HTMLTextAreaElement) {
         fields[name] = el.value ?? null;
      }
   }

   return fields;
}

export function parsePageForms(): PageFormsData {
   if (typeof document === 'undefined') {
      cachedForms = [];
      return { forms: [] };
   }

   const forms = Array.from(document.querySelectorAll('form')).map((form, idx) => {
      const id = form.id || `form_${idx}`;
      return {
         id,
         action: form.getAttribute('action') || undefined,
         method: form.getAttribute('method') || undefined,
         fields: extractFormValues(form),
      } as FormData;
   });

   cachedForms = forms;
   return { forms };
}

export function getFormValues(): FormValuesMap {
   if (cachedForms.length === 0) {
      parsePageForms();
   }

   return cachedForms.reduce<FormValuesMap>((acc, form) => {
      acc[form.id] = form.fields;
      return acc;
   }, {});
}

export function getFormData(id: string): FormData | undefined {
   if (cachedForms.length === 0) {
      parsePageForms();
   }
   return cachedForms.find((form) => form.id === id);
}
