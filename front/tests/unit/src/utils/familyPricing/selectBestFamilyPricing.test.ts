import { describe, expect, it } from 'vitest';

import { selectBestFamilyPricing } from '../../../../../src/utils/familyPricing';

describe('selectBestFamilyPricing', () => {
   it('returns direct net price family when available', () => {
      const result = selectBestFamilyPricing({
         directNetPriceFamily: { type: 'net_price', net_price: 42 },
         linkedFamilies: [{ type: 'discount', discount: 35 }],
      });

      expect(result).toEqual({ type: 'net_price', net_price: 42 });
   });

   it('returns linked net price family before discount families', () => {
      const result = selectBestFamilyPricing({
         linkedFamilies: [
            { type: 'discount', discount: 10 },
            { type: 'net_price', net_price: 18.5 },
            { type: 'discount', discount: 30 },
         ],
      });

      expect(result).toEqual({ type: 'net_price', net_price: 18.5 });
   });

   it('returns the highest discount family when no net price exists', () => {
      const result = selectBestFamilyPricing({
         linkedFamilies: [
            { type: 'discount', discount: 12 },
            { type: 'discount', discount: 45 },
            { type: 'discount', discount: 20 },
         ],
      });

      expect(result).toEqual({ type: 'discount', discount: 45 });
   });

   it('returns null when no effective family pricing exists', () => {
      const result = selectBestFamilyPricing({
         linkedFamilies: [{ type: 'discount', discount: 0 }, { type: 'other' }],
      });

      expect(result).toBeNull();
   });
});
