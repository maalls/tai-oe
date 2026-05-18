import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useBrandFamilyData } from '../../../../../../src/components/products/useBrandFamilyData';
import * as catalogApi from '../../../../../../src/api/catalog';
import * as vendorApi from '../../../../../../src/api/vendor';

describe('useBrandFamilyData loadData', () => {
   beforeEach(() => {
      vi.restoreAllMocks();
   });

   it('loads brands and families from backend APIs', async () => {
      vi.spyOn(vendorApi, 'listVendors').mockResolvedValue([
         { id: 'v1', name: 'Vendor A', created_at: '2026-01-01', updated_at: '2026-01-01' },
      ]);
      vi.spyOn(catalogApi, 'listCatalogBrands').mockResolvedValue([
         { id: 'b1', name: 'Brand A', vendor_id: 'v1' },
      ]);
      vi.spyOn(catalogApi, 'listCatalogFamilies').mockResolvedValue([
         {
            id: 'f1',
            name: 'Family A',
            brand_id: 'b1',
            type: 'standard',
            product_family_count: 2,
            product: {
               id: 'p1',
               sku: 'SKU-1',
               name: 'Product A',
               price: 10,
               brand_id: 'b1',
            },
         },
      ] as any);

      const model = useBrandFamilyData();
      await model.loadData();

      expect(model.brands.value[0].vendor_name).toBe('Vendor A');
      expect(model.families.value[0].product_family_count).toBe(2);
      expect(model.families.value[0].product?.id).toBe('p1');
      expect(model.errorMessage.value).toBe('');
      expect(model.isLoading.value).toBe(false);
   });

   it('sets error message when an API call fails', async () => {
      vi.spyOn(vendorApi, 'listVendors').mockRejectedValue(new Error('vendors failed'));
      vi.spyOn(catalogApi, 'listCatalogBrands').mockResolvedValue([]);
      vi.spyOn(catalogApi, 'listCatalogFamilies').mockResolvedValue([]);

      const model = useBrandFamilyData();
      await model.loadData();

      expect(model.errorMessage.value).toBe('vendors failed');
      expect(model.isLoading.value).toBe(false);
   });
});
