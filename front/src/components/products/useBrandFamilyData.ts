import { ref } from 'vue';
import { supabase } from '../../lib/supabase';

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
         // Fetch all vendors
         const { data: vendorData, error: vendorError } = await supabase
            .from('vendor')
            .select('id,name');
         if (vendorError) throw new Error(`Vendors: ${vendorError.message}`);
         const vendorMap = (vendorData || []).reduce((acc: Record<string, string>, v: any) => {
            acc[v.id] = v.name;
            return acc;
         }, {});

         // Fetch brands with vendor_id
         const { data: brandData, error: brandError } = await supabase
            .from('brand')
            .select('*')
            .order('name', { ascending: true });
         if (brandError) throw new Error(`Brands: ${brandError.message}`);

         brands.value = (brandData || []).map((b: any) => ({
            ...b,
            vendor_name: b.vendor_id ? vendorMap[b.vendor_id] : null,
         }));

         // Fetch families from the family table
         const { data: familyData, error: familyError } = await supabase
            .from('family')
            .select('*, product_family(count)')
            .order('name', { ascending: true });
         if (familyError) throw new Error(`Families: ${familyError.message}`);

         // Left-join semantics by SKU: product.sku = family.product_code
         const productCodes = Array.from(
            new Set(
               (familyData || [])
                  .map((f: any) =>
                     typeof f.product_code === 'string' ? f.product_code.trim() : ''
                  )
                  .filter((code: string) => code.length > 0)
            )
         );

         let productBySku: Record<
            string,
            {
               id: string;
               sku: string;
               name: string | null;
               price: number | null;
               brand_id: string | null;
            }
         > = {};
         if (productCodes.length > 0) {
            const { data: productData, error: productError } = await supabase
               .from('product')
               .select('id,sku,price,name,brand_id')
               .in('sku', productCodes);
            if (productError) throw new Error(`Products: ${productError.message}`);

            productBySku = (productData || []).reduce(
               (
                  acc: Record<
                     string,
                     {
                        id: string;
                        sku: string;
                        name: string | null;
                        price: number | null;
                        brand_id: string | null;
                     }
                  >,
                  p: any
               ) => {
                  acc[p.sku] = {
                     id: p.id,
                     sku: p.sku,
                     price: p.price ?? null,
                     name: p.name ?? null,
                     brand_id: p.brand_id ?? null,
                  };
                  return acc;
               },
               {}
            );
         }

         families.value = (familyData || []).map((f: any) => {
            const sku = typeof f.product_code === 'string' ? f.product_code.trim() : '';
            const matchedProduct = sku ? productBySku[sku] : undefined;
            return {
               ...f,
               product_family_count: f.product_family?.[0]?.count ?? 0,
               product: matchedProduct ?? null,
            };
         });
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
