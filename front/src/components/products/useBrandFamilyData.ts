import { ref } from 'vue';
import { listCatalogBrands, listCatalogFamilies } from '../../api/catalog';
import { listVendors } from '../../api/vendor';

export interface Brand {
   id: string;
   name: string;
   vendor_id?: string | null;
   vendor_name?: string | null;
   website?: string | null;
   email?: string | null;
   phone?: string | null;
   minimum_margin?: number | null;
   target_margin?: number | null;
   created_at?: string | null;
}

export interface Family {
   id: string;
   name: string;
   code: string | null;
   type: string;
   brand_id: string;
   product_code: string | null;
   quantity: number | null;
   discount: number | null;
   minimum_margin: number | null;
   target_margin: number | null;
   unit: string | null;
   packing: string | null;
   lead_time_week: number | null;
   net_price: number | null;
   product_family_count: number;
   product?: {
      id: string;
      sku: string;
      name: string | null;
      price: number | null;
      brand_id: string | null;
   } | null;
}

export const useBrandFamilyData = () => {
   const brands = ref<Brand[]>([]);
   const families = ref<Family[]>([]);
   const isLoading = ref(false);
   const errorMessage = ref('');

   const loadData = async () => {
      isLoading.value = true;
      errorMessage.value = '';

      try {
         const [vendorData, brandData, familyData] = await Promise.all([
            listVendors(),
            listCatalogBrands(),
            listCatalogFamilies(),
         ]);

         const vendorMap = (vendorData || []).reduce((acc: Record<string, string>, v: any) => {
            acc[v.id] = v.name;
            return acc;
         }, {});

         brands.value = (brandData || []).map((b: any) => ({
            ...b,
            vendor_name: b.vendor_id ? vendorMap[b.vendor_id] : null,
         }));
         families.value = (familyData || []).map((f: any) => ({
            ...f,
            product_family_count: f.product_family_count ?? 0,
            product: f.product ?? null,
         }));
      } catch (error) {
         errorMessage.value = error instanceof Error ? error.message : 'Failed to load brand data.';
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
