export type FamilyPricing = {
   type?: string | null;
   discount?: number | null;
   net_price?: number | null;
};

const normalizeFamilyType = (family: FamilyPricing | null | undefined) =>
   String(family?.type || '')
      .trim()
      .toLowerCase();

const isNetPriceFamily = (family: FamilyPricing | null | undefined) =>
   normalizeFamilyType(family) === 'net_price' && Number.isFinite(Number(family?.net_price));

const isDiscountFamily = (family: FamilyPricing | null | undefined) => {
   if (normalizeFamilyType(family) !== 'discount') return false;
   return Number(family?.discount || 0) > 0;
};

export const selectBestFamilyPricing = ({
   directNetPriceFamily,
   linkedFamilies,
}: {
   directNetPriceFamily?: FamilyPricing | null;
   linkedFamilies?: Array<FamilyPricing | null | undefined>;
}): FamilyPricing | null => {
   if (isNetPriceFamily(directNetPriceFamily)) {
      return directNetPriceFamily || null;
   }

   const families = Array.isArray(linkedFamilies) ? linkedFamilies : [];
   let bestDiscountFamily: FamilyPricing | null = null;

   for (const family of families) {
      if (!family) continue;

      if (isNetPriceFamily(family)) {
         return family;
      }

      if (!isDiscountFamily(family)) {
         continue;
      }

      const currentDiscount = Number(family.discount || 0);
      const bestDiscount = Number(bestDiscountFamily?.discount || -Infinity);
      if (currentDiscount > bestDiscount) {
         bestDiscountFamily = family;
      }
   }

   return bestDiscountFamily;
};

export const applyFamilyPricingToListPrice = ({
   listPrice,
   bestFamily,
}: {
   listPrice: number;
   bestFamily: FamilyPricing | null;
}): number => {
   const basePrice = Number(listPrice);
   if (!Number.isFinite(basePrice)) {
      return NaN;
   }

   if (isNetPriceFamily(bestFamily)) {
      return Number(bestFamily?.net_price);
   }

   if (isDiscountFamily(bestFamily)) {
      return basePrice * (1 - Number(bestFamily?.discount || 0) / 100);
   }

   return basePrice;
};
