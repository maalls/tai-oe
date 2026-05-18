import { ref } from 'vue';
import { listCatalogBrands, listCatalogFamilies } from '../../../../api/catalog';

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

         brands.value = (brandData || []).map((brand) => ({
            id: brand.id,
            name: brand.name || '',
            website: brand.website ?? null,
            email: brand.email ?? null,
            phone: brand.phone ?? null,
            created_at: brand.created_at ?? null,
         }));
         families.value = (familyData || []).map((family) => ({
            id: family.id,
            name: family.name || '',
            type: family.type || '',
            brand_id: family.brand_id,
         }));
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
