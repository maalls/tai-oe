import { ref } from 'vue';
import { supabase } from '../../../lib/supabase';

export interface Brand {
   id: string;
   name: string;
   website?: string | null;
   email?: string | null;
   phone?: string | null;
   created_at?: string | null;
}

export interface Family {
   id: string;
   name: string;
   type: string;
   brand_id: string;
}

export const useCmsData = () => {
   const brands = ref<Brand[]>([]);
   const families = ref<Family[]>([]);
   const isLoading = ref(false);
   const errorMessage = ref('');

   const loadData = async () => {
      isLoading.value = true;
      errorMessage.value = '';

      try {
         const { data: brandData, error: brandError } = await supabase
            .from('brand')
            .select('id,name,website,email,phone,created_at')
            .order('name', { ascending: true });

         if (brandError) throw brandError;

         const { data: familyData, error: familyError } = await supabase
            .from('family')
            .select('id,name,type,brand_id')
            .order('name', { ascending: true });

         if (familyError) throw familyError;

         brands.value = brandData || [];
         families.value = familyData || [];
      } catch (error) {
         errorMessage.value = error instanceof Error ? error.message : 'Failed to load CMS data.';
      } finally {
         isLoading.value = false;
      }
   };

   return {
      brands,
      families,
      isLoading,
      errorMessage,
      loadData,
   };
};
