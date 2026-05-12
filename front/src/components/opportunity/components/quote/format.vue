<script lang="ts">
export const formatCurrency = (value: number, currency?: string) => {
   const amount = Number(value) || 0;
   const cur = currency || 'EUR';
   return new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: cur,
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
   }).format(amount);
};

export const formatNumber = (value: number, decimals: number = 2) => {
   const amount = Number(value) || 0;
   return new Intl.NumberFormat('fr-FR', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
   }).format(amount);
};

export const targetMargin = (item: any) => {
   if (item.best_family?.target_margin) {
      return item.best_family.target_margin;
   } else if (item.product?.brand?.target_margin) {
      return item.product?.brand?.target_margin;
   } else {
      return 0;
   }
};

export const purchasedPrice = (item: any) => {
   if ((item?.best_family?.type || '').toLowerCase() === 'net_price') {
      return Number(item?.best_family?.net_price || 0);
   }
   return (item.product ? item.product.price : 0) * (1 - (item.best_family?.discount || 0) / 100);
};

const hasEffectiveFamilyPricing = (item: any) => {
   const type = String(item?.best_family?.type || '').toLowerCase();
   if (type === 'net_price') {
      return item?.best_family?.net_price !== null && item?.best_family?.net_price !== undefined;
   }
   if (type === 'discount') {
      return Number(item?.best_family?.discount || 0) > 0;
   }
   return false;
};

const brandMinimumMargin = (item: any) => {
   return Number(item?.product?.brand?.minimum_margin || 0);
};

const brandTargetMargin = (item: any) => {
   return Number(item?.product?.brand?.target_margin || 0);
};

export const targetUnitPrice = (item: any) => {
   const marginRatio = Number(targetMargin(item) || 0) / 100;
   if (marginRatio >= 1) return 0;
   return purchasedPrice(item) / (1 - marginRatio);
};

export const maxDiscount = (item: any) => {
   const listPrice = item.product?.price || 0;
   if (listPrice === 0) return 0;
   const cost = purchasedPrice(item);
   if (cost <= 0) return 0;
   const minMargin = hasEffectiveFamilyPricing(item)
      ? Number(item.best_family?.minimum_margin || 0)
      : brandMinimumMargin(item);
   const minMarginRatio = minMargin / 100;
   if (minMarginRatio >= 1) return 0;
   const minSellPrice = cost / (1 - minMarginRatio);
   return (1 - minSellPrice / listPrice) * 100;
};

export const targetDiscount = (item: any) => {
   const listPrice = item.product?.price || 0;
   if (listPrice === 0) return 0;
   const purchased = purchasedPrice(item);
   const target_margin = targetMargin(item);
   const x = purchased / ((1 - target_margin / 100) * listPrice);

   return (1 - x) * 100;
};

export const unitPrice = (item: any) => {
   return (
      (item.product ? item.product.price : 0) *
      (1 - (item.discount || 0) / 100) *
      (1 + (item.line.margin || 0) / 100)
   );
};

export const priceWithoutTax = (item: any) => {
   const client_discount = 1 - (item.line.client_discount_rate || 0) / 100;
   return (item.product?.price || 0) * client_discount;
};

export const totalPriceWithoutTax = (item: any) => {
   const quantity = item.line.quantity || 0;
   if (quantity === 0) {
      return 0;
   }
   return priceWithoutTax(item) * quantity;
};

export const totalPriceWithTax = (item: any) => {
   return totalPriceWithoutTax(item) * (1 + (item.line.tax_rate || 0) / 100);
};

export const totalCost = (item: any) => {
   return item.line.quantity * purchasedPrice(item);
};

export const marginAmount = (item: any) => {
   return priceWithoutTax(item) - purchasedPrice(item);
};

export const totalMarginAmount = (item: any) => {
   return totalPriceWithoutTax(item) - totalCost(item);
};

export const marginPercent = (item: any) => {
   const cost = totalPriceWithoutTax(item);
   if (cost === 0) {
      return 0;
   }
   return (totalMarginAmount(item) / cost) * 100;
};

export const grandTotalCost = (lines: any) => {
   return lines.reduce((total: number, line: any) => {
      const cost = totalCost(line);
      return total + cost;
   }, 0);
};

export const grandTotalMargin = (lines: any) => {
   return lines.reduce((total: number, line: any) => {
      const margin = totalMarginAmount(line);
      return total + margin;
   }, 0);
};

export const minQuantity = (item: any) => {
   return item.best_family?.quantity || 1;
};

export const minMargin = (item: any) => {
   if (hasEffectiveFamilyPricing(item)) {
      return item.best_family?.minimum_margin || 0;
   }
   return item.product?.brand?.minimum_margin || 0;
};

export default {};
</script>
