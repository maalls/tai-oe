import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useCmsData } from '../../../../../../../src/components/products/cms/useCmsData';
import * as catalogApi from '../../../../../../../src/api/catalog';

describe('products/useCmsData loadData', () => {
   beforeEach(() => {
      vi.restoreAllMocks();
   });

   it('loads brands and families from API', async () => {
      vi.spyOn(catalogApi, 'listCatalogBrands').mockResolvedValue([{ id: 'b1', name: 'Brand A' }]);
      vi.spyOn(catalogApi, 'listCatalogFamilies').mockResolvedValue([
         { id: 'f1', name: 'Family A', brand_id: 'b1', type: 'standard' },
      ]);

      const model = useCmsData();
      await model.loadData();

      expect(model.brands.value).toHaveLength(1);
      expect(model.families.value).toHaveLength(1);
      expect(model.errorMessage.value).toBe('');
      expect(model.isLoading.value).toBe(false);
   });

   it('sets error message when API fails', async () => {
      vi.spyOn(catalogApi, 'listCatalogBrands').mockRejectedValue(new Error('boom'));
      vi.spyOn(catalogApi, 'listCatalogFamilies').mockResolvedValue([]);

      const model = useCmsData();
      await model.loadData();

      expect(model.errorMessage.value).toBe('boom');
      expect(model.isLoading.value).toBe(false);
   });
});
