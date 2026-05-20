import { describe, expect, it } from 'vitest';

import { applyFamilyPricingToListPrice } from '../../../../../src/utils/familyPricing';

describe('applyFamilyPricingToListPrice', () => {
   it('applies net price when family type is net_price', () => {
      const result = applyFamilyPricingToListPrice({
         listPrice: 100,
         bestFamily: { type: 'net_price', net_price: 57.3 },
      });

      expect(result).toBe(57.3);
   });

   it('applies percentage discount when family type is discount', () => {
      const result = applyFamilyPricingToListPrice({
         listPrice: 100,
         bestFamily: { type: 'discount', discount: 25 },
      });

      expect(result).toBe(75);
   });

   it('returns list price when family has no effective pricing', () => {
      const result = applyFamilyPricingToListPrice({
         listPrice: 100,
         bestFamily: { type: 'discount', discount: 0 },
      });

      expect(result).toBe(100);
   });
});
