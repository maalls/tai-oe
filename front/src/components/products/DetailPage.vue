<template>
   <ProductsSubHeader class="mb-6" />
   <div class="p-6 max-w-4xl mx-auto">
      <!--div class="flex items-center justify-between mb-6">
         <div>
            <div class="text-sm text-gray-500">{{ t('products.detail.title') }}</div>
            <h1 class="text-2xl md:text-3xl font-semibold tracking-tight text-gray-900">
               {{ product?.refciale || t('products.detail.fallbackTitle') }}
            </h1>
         </div>
         <RouterLink
            to="/products"
            class="px-3 py-1.5 text-sm bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200"
         >
            {{ t('products.detail.back') }}
         </RouterLink>
      </div-->

      <div v-if="error" class="text-red-600 bg-red-50 p-4 rounded-lg mb-6">
         {{ error }}
      </div>

      <div v-if="loading" class="bg-white rounded-lg shadow p-6 text-gray-600">
         {{ t('products.detail.loading') }}
      </div>

      <div v-else-if="!product" class="bg-white rounded-lg shadow p-6 text-gray-600">
         {{ t('products.detail.notFound') }}
      </div>

      <div v-else class="bg-white rounded-2xl shadow-lg border border-gray-100 p-5 md:p-6">
         <div
            class="grid grid-cols-1 lg:grid-cols-[minmax(0,1.08fr)_minmax(0,0.92fr)] gap-6 lg:gap-8 items-start"
         >
            <div>
               <div v-if="mediaImages.length" class="space-y-3">
                  <div class="flex items-center justify-between">
                     <!--div class="text-sm font-medium text-gray-500">
                        {{ t('products.detail.images') }}
                     </div-->
                     <div v-if="mediaImages.length > 1" class="text-xs text-gray-400">
                        {{ activeMediaIndex + 1 }}/{{ mediaImages.length }}
                     </div>
                  </div>

                  <div
                     class="overflow-hidden rounded-2xl border border-gray-200 bg-linear-to-br from-gray-50 to-white shadow-sm"
                  >
                     <div class="relative">
                        <div class="flex aspect-4/3 max-h-105 items-center justify-center bg-white">
                           <img
                              v-if="activeMedia"
                              :src="activeMedia.url"
                              :alt="
                                 product.refciale ||
                                 product.libelle240 ||
                                 t('products.detail.fallbackTitle')
                              "
                              class="h-full w-full object-contain p-3 md:p-4"
                           />
                           <div v-else class="text-sm text-gray-400">
                              {{ t('products.detail.noImage') }}
                           </div>
                        </div>

                        <button
                           v-if="mediaImages.length > 1"
                           type="button"
                           class="absolute left-3 top-1/2 -translate-y-1/2 rounded-full bg-white/90 px-3 py-2 text-sm font-medium text-gray-700 shadow hover:bg-white disabled:opacity-40"
                           :disabled="mediaImages.length <= 1"
                           @click="previousMedia"
                        >
                           &lt;
                        </button>
                        <button
                           v-if="mediaImages.length > 1"
                           type="button"
                           class="absolute right-3 top-1/2 -translate-y-1/2 rounded-full bg-white/90 px-3 py-2 text-sm font-medium text-gray-700 shadow hover:bg-white disabled:opacity-40"
                           :disabled="mediaImages.length <= 1"
                           @click="nextMedia"
                        >
                           &gt;
                        </button>
                     </div>

                     <div
                        v-if="mediaImages.length > 1"
                        class="flex gap-3 overflow-x-auto border-t border-gray-100 bg-gray-50 p-3"
                     >
                        <button
                           v-for="(media, index) in mediaImages"
                           :key="media.id || `${media.url}-${index}`"
                           type="button"
                           class="shrink-0 rounded-xl border bg-white p-1 shadow-sm transition"
                           :class="
                              index === activeMediaIndex
                                 ? 'border-blue-500 ring-2 ring-blue-100'
                                 : 'border-gray-200 hover:border-gray-300'
                           "
                           @click="selectMedia(index)"
                        >
                           <img
                              :src="media.url"
                              :alt="`${product.refciale || 'product'} - ${index + 1}`"
                              class="h-14 w-14 rounded-lg object-cover md:h-16 md:w-16"
                           />
                        </button>
                     </div>
                  </div>
               </div>
            </div>

            <div class="space-y-5 lg:pt-1">
               <div>
                  <div class="text-xs font-medium uppercase tracking-[0.16em] text-gray-400">
                     {{ t('products.detail.description') }}
                  </div>
                  <div class="mt-1 text-sm md:text-base leading-6 text-gray-700">
                     {{ product.libelle240 || '-' }}
                  </div>
               </div>
               <div>
                  <div class="text-xs font-medium uppercase tracking-[0.16em] text-gray-400">
                     {{ t('products.detail.refciale') }}
                  </div>
                  <div class="mt-1 text-base md:text-lg font-mono text-gray-900">
                     {{ product.refciale }}
                  </div>
               </div>

               <div>
                  <div class="text-xs font-medium uppercase tracking-[0.16em] text-gray-400">
                     {{ t('products.detail.brand') }}
                  </div>
                  <div class="mt-1 text-lg md:text-xl font-medium text-gray-900">
                     {{ product.brand_name || product.marque || '-' }}
                  </div>
               </div>

               <div>
                  <div class="text-xs font-medium uppercase tracking-[0.16em] text-gray-400">
                     {{ t('products.table.columns.families') }}
                  </div>
                  <div v-if="familyTags.length" class="mt-2 flex flex-wrap gap-2">
                     <a
                        v-for="tag in familyTags"
                        :key="tag.label"
                        :href="tag.href"
                        class="rounded-full px-2.5 py-1 text-xs cursor-pointer hover:opacity-80"
                        :class="
                           tag.isNetPrice
                              ? 'bg-green-100 text-emerald-700'
                              : tag.hasDiscount
                                ? 'bg-amber-100 text-amber-800'
                                : 'bg-gray-100 text-gray-700'
                        "
                     >
                        {{ tag.label }}
                     </a>
                  </div>
                  <div v-else class="mt-2 text-gray-500">-</div>
               </div>

               <div
                  class="grid grid-cols-2 gap-4 rounded-2xl border border-gray-100 bg-gray-50/70 p-4"
               >
                  <div>
                     <div class="text-xs font-medium uppercase tracking-[0.16em] text-gray-400">
                        {{ t('products.detail.tarif') }}
                     </div>
                     <div v-if="discountedPrice" class="mt-1">
                        <div class="text-sm text-gray-500 line-through">
                           {{ formatPrice(discountedPrice.original) }}
                        </div>
                        <div class="text-xl font-semibold text-gray-900">
                           {{ formatPrice(discountedPrice.discounted) }}
                        </div>
                     </div>
                     <div v-else class="mt-1 text-xl font-semibold text-gray-900">
                        {{ formatPrice(product.tarif) }}
                     </div>
                  </div>

                  <div>
                     <div class="text-xs font-medium uppercase tracking-[0.16em] text-gray-400">
                        {{ t('products.detail.gamme') }}
                     </div>
                     <div class="mt-1 text-base text-gray-900">{{ product.gamme || '-' }}</div>
                  </div>

                  <div>
                     <div class="text-xs font-medium uppercase tracking-[0.16em] text-gray-400">
                        {{ t('products.detail.batch') }}
                     </div>
                     <div class="mt-1 text-base text-gray-900">{{ product.batch ?? '-' }}</div>
                  </div>
               </div>
            </div>
         </div>

         <div v-if="rawPayload" class="mt-6">
            <div class="text-sm text-gray-500 mb-2">{{ t('products.detail.rawPayload') }}</div>
            <pre class="bg-gray-50 border border-gray-200 rounded p-3 text-xs overflow-x-auto">{{
               rawPayload
            }}</pre>
         </div>
      </div>
   </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRoute } from 'vue-router';
import { getProduct } from '../../api/product';
import { useI18n } from '../../i18n/useI18n';
import ProductsSubHeader from './ProductsSubHeader.vue';
import { useBrandFamilyData } from './useBrandFamilyData';
import {
   applyFamilyPricingToListPrice,
   selectBestFamilyPricing,
   type FamilyPricing,
} from '../../utils/familyPricing';

interface Product {
   id: string | number;
   marque?: string;
   brand_name?: string | null;
   brand_id?: string | null;
   refciale?: string;
   libelle240?: string;
   tarif?: string | number;
   batch?: string | number | null;
   family_codes?: string[] | null;
   media?: ProductMedia[];
   gamme?: string;
}

interface ProductMedia {
   id?: string;
   url: string;
   type?: string | null;
   source?: string | null;
   position?: number | null;
   created_at?: string | null;
}

const route = useRoute();
const { t } = useI18n();
const { families, loadData: loadBrandData } = useBrandFamilyData();
const product = ref<Product | null>(null);
const loading = ref(false);
const error = ref('');
const rawPayload = ref('');
const activeMediaIndex = ref(0);

const mediaImages = computed(() => {
   const media = Array.isArray(product.value?.media) ? product.value?.media : [];
   return [...media]
      .filter((item) => {
         const mediaType = String(item?.type || '')
            .trim()
            .toLowerCase();
         return !mediaType || mediaType === 'photo' || mediaType === 'image';
      })
      .sort((left, right) => {
         const leftPosition = Number.isFinite(Number(left?.position))
            ? Number(left?.position)
            : Number.MAX_SAFE_INTEGER;
         const rightPosition = Number.isFinite(Number(right?.position))
            ? Number(right?.position)
            : Number.MAX_SAFE_INTEGER;

         if (leftPosition !== rightPosition) {
            return leftPosition - rightPosition;
         }

         return String(left?.created_at || '').localeCompare(String(right?.created_at || ''));
      });
});

const activeMedia = computed(
   () => mediaImages.value[activeMediaIndex.value] || mediaImages.value[0] || null
);

const familiesByBrandAndCode = computed(() => {
   return families.value.reduce(
      (acc, family) => {
         const code = String(family.code || '')
            .trim()
            .toLowerCase();
         const brandId = String(family.brand_id || '')
            .trim()
            .toLowerCase();
         if (!code || !brandId) {
            return acc;
         }

         const key = `${brandId}::${code}`;
         const current = acc[key];
         if (!current || Number(family.discount || 0) > Number(current.discount || 0)) {
            acc[key] = family;
         }

         return acc;
      },
      {} as Record<string, any>
   );
});

const netPriceFamilyByBrandAndSku = computed(() => {
   return families.value.reduce(
      (acc, family) => {
         const familyType = String(family.type || '')
            .trim()
            .toLowerCase();
         if (familyType !== 'net_price') {
            return acc;
         }

         const brandId = String(family.brand_id || '')
            .trim()
            .toLowerCase();
         const sku = String(family.product_code || '')
            .trim()
            .toLowerCase();
         if (!brandId || !sku) {
            return acc;
         }

         acc[`${brandId}::${sku}`] = family;
         return acc;
      },
      {} as Record<string, any>
   );
});

const bestFamilyForProduct = computed(() => {
   if (!product.value) return null;

   const skuLower = String(product.value.refciale || '')
      .trim()
      .toLowerCase();
   const brandIdLower = String(product.value.brand_id || '')
      .trim()
      .toLowerCase();
   const codes = (product.value.family_codes || [])
      .map((code) => String(code).trim())
      .filter(Boolean);

   const linkedFamilies = codes
      .map((code) => familiesByBrandAndCode.value[`${brandIdLower}::${code.toLowerCase()}`])
      .filter(Boolean) as FamilyPricing[];
   const directNetPriceFamily = skuLower
      ? netPriceFamilyByBrandAndSku.value[`${brandIdLower}::${skuLower}`] || null
      : null;

   return selectBestFamilyPricing({
      directNetPriceFamily,
      linkedFamilies,
   });
});

const familyTags = computed(() => {
   if (!product.value) return [];

   const sku = String(product.value.refciale || '').trim();
   const brandIdLower = String(product.value.brand_id || '')
      .trim()
      .toLowerCase();
   const bestFamily = bestFamilyForProduct.value;
   const bestDiscount =
      String(bestFamily?.type || '').toLowerCase() === 'discount'
         ? Number(bestFamily?.discount || 0)
         : 0;

   const tags: { label: string; hasDiscount: boolean; isNetPrice: boolean; href: string }[] = [];

   if (String(bestFamily?.type || '').toLowerCase() === 'net_price') {
      const href = sku
         ? `/vendors/family?tab=all&sku=${encodeURIComponent(sku)}&exactMatch=true`
         : '/vendors/family?tab=all';
      const netPrice = Number(bestFamily?.net_price);
      const netLabel = Number.isFinite(netPrice) ? `NET (${formatPrice(netPrice)})` : 'NET';
      tags.push({ label: netLabel, hasDiscount: false, isNetPrice: true, href });
   }

   const codes = (product.value.family_codes || [])
      .map((code) => String(code).trim())
      .filter(Boolean);

   tags.push(
      ...codes.map((code) => {
         const family = familiesByBrandAndCode.value[`${brandIdLower}::${code.toLowerCase()}`];
         const hasDiscount =
            String(bestFamily?.type || '').toLowerCase() === 'discount' &&
            bestDiscount > 0 &&
            Number(family?.discount || 0) === bestDiscount;
         const nameLabel = family?.name ? `${code} ${family.name}` : code;
         const discountLabel =
            String(family?.type || '').toLowerCase() === 'discount' &&
            Number(family?.discount || 0) > 0
               ? ` (${Number(family?.discount)}%)`
               : '';
         return {
            label: `${nameLabel}${discountLabel}`,
            hasDiscount,
            isNetPrice: false,
            href: `/vendors/family?tab=all&code=${encodeURIComponent(code)}`,
         };
      })
   );

   return tags;
});

const discountedPrice = computed(() => {
   if (!product.value) return null;
   const price =
      typeof product.value.tarif === 'string'
         ? parseFloat(product.value.tarif)
         : product.value.tarif;
   if (!Number.isFinite(price)) return null;

   const bestFamily = bestFamilyForProduct.value;
   if (!bestFamily) return null;

   const discounted = applyFamilyPricingToListPrice({
      listPrice: price,
      bestFamily,
   });
   if (!Number.isFinite(discounted) || discounted === price) {
      return null;
   }

   return { original: price, discounted };
});

function selectMedia(index: number) {
   activeMediaIndex.value = index;
}

function previousMedia() {
   if (!mediaImages.value.length) return;
   activeMediaIndex.value =
      (activeMediaIndex.value - 1 + mediaImages.value.length) % mediaImages.value.length;
}

function nextMedia() {
   if (!mediaImages.value.length) return;
   activeMediaIndex.value = (activeMediaIndex.value + 1) % mediaImages.value.length;
}

async function loadProduct() {
   const routeId = route.params.id;
   const id = Array.isArray(routeId) ? routeId[0] : routeId;
   if (!id) {
      error.value = t('products.detail.missingId');
      return;
   }

   loading.value = true;
   error.value = '';

   try {
      const data = await getProduct(String(id));

      if (!data) {
         product.value = null;
         return;
      }

      product.value = {
         id: data.id,
         marque: data.marque || '',
         brand_name: data.brand_name || null,
         brand_id: data.brand_id || null,
         refciale: data.refciale || '',
         libelle240: data.libelle240 || '',
         tarif: data.tarif ?? '',
         batch: data.batch ?? null,
         family_codes: Array.isArray(data.family_codes) ? data.family_codes : [],
         media: Array.isArray(data.media) ? data.media : [],
         gamme: '',
      };

      activeMediaIndex.value = 0;

      rawPayload.value = JSON.stringify(data, null, 2);
   } catch (e: any) {
      error.value = String(e?.message || e);
   } finally {
      loading.value = false;
   }
}

function formatPrice(price: string | number | undefined): string {
   if (price === undefined || price === null || price === '') return '-';
   const num = typeof price === 'string' ? parseFloat(price) : price;
   if (isNaN(num)) return '-';
   return (
      '€ ' + num.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
   );
}

onMounted(() => {
   loadBrandData();
   loadProduct();
});
</script>
