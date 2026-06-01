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

   // Ajout pour pagination et filtre
   const totalFamilies = ref(0);

   const loadData = async (params?: { brand_id?: string; limit?: number; offset?: number }) => {
      isLoading.value = true;
      errorMessage.value = '';

      try {
         const [vendorData, brandData, familyData] = await Promise.all([
            listVendors(),
            listCatalogBrands(),
            listCatalogFamilies(params),
         ]);

         const vendorMap = (vendorData || []).reduce((acc: Record<string, string>, v: any) => {
            acc[v.id] = v.name;
            return acc;
         }, {});

         brands.value = (brandData || []).map((b: any) => ({
            id: b.id,
            name: b.name || '',
            vendor_id: b.vendor_id ?? null,
            vendor_name: b.vendor_id ? vendorMap[b.vendor_id] : null,
            website: b.website ?? null,
            email: b.email ?? null,
            phone: b.phone ?? null,
            minimum_margin: b.minimum_margin ?? null,
            target_margin: b.target_margin ?? null,
            created_at: b.created_at ?? null,
         }));
         families.value = (familyData || []).map((f: any) => ({
            id: f.id,
            name: f.name || '',
            code: f.code ?? null,
            type: f.type || '',
            brand_id: f.brand_id,
            product_code: f.product_code ?? null,
            quantity: f.quantity ?? null,
            discount: f.discount ?? null,
            minimum_margin: f.minimum_margin ?? null,
            target_margin: f.target_margin ?? null,
            unit: f.unit ?? null,
            packing: f.packing ?? null,
            lead_time_week: f.lead_time_week ?? null,
            net_price: f.net_price ?? null,
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
