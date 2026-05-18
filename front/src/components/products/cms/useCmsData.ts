import { ref } from 'vue';
import { listCatalogBrands, listCatalogFamilies } from '../../../api/catalog';

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
         const [brandData, familyData] = await Promise.all([
            listCatalogBrands(),
            listCatalogFamilies(),
         ]);

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
