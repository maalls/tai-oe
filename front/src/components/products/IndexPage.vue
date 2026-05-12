<template>
   <div>
      <ProductsSubHeader>
         <template #actions>
            <router-link
               to="/products/new"
               class="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg font-medium text-sm"
            >
               {{ t('products.list.new') }}
            </router-link>
         </template>
      </ProductsSubHeader>
      <div class="p-6 max-w-7xl mx-auto">
         <div v-if="error" class="text-red-600 bg-red-50 p-4 rounded-lg mb-6">
            {{ error }}
         </div>

         <!-- Combined Search Section -->
         <div class="mb-6">
            <!-- Search Query -->
            <div class="mb-4">
               <input
                  v-model="searchQuery"
                  type="text"
                  :placeholder="t('products.list.searchPlaceholder')"
                  class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  @keydown.enter="performSearch"
               />
            </div>

            <!-- Filters -->
            <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
               <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">
                     {{ t('products.list.fields.marque') }}
                  </label>
                  <input
                     v-model="filterMarque"
                     type="text"
                     placeholder="e.g., LEGRAND"
                     class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                     @keydown.enter="performSearch"
                  />
               </div>
               <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">
                     {{ t('products.list.fields.refciale') }}
                  </label>
                  <input
                     v-model="filterRefciale"
                     type="text"
                     placeholder="e.g., 050415"
                     class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                     @keydown.enter="performSearch"
                  />
               </div>
               <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">
                     {{ t('products.list.fields.tarif') }}
                  </label>
                  <input
                     v-model="filterTarif"
                     type="text"
                     placeholder="e.g., 100.50"
                     class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                     @keydown.enter="performSearch"
                  />
               </div>
               <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">
                     {{ t('products.list.fields.family') }}
                  </label>
                  <input
                     v-model="filterFamily"
                     type="text"
                     placeholder="e.g., 1A02"
                     class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                     @keydown.enter="performSearch"
                  />
               </div>
            </div>

            <div class="flex gap-3">
               <button
                  @click="performSearch"
                  :disabled="loading"
                  class="px-4 py-2 bg-blue-600 text-white rounded-md disabled:opacity-50 hover:bg-blue-700"
               >
                  {{ loading ? t('products.list.searching') : t('common.search') }}
               </button>
               <button
                  @click="clearSearch"
                  :disabled="loading"
                  class="px-4 py-2 bg-gray-400 text-white rounded-md disabled:opacity-50 hover:bg-gray-500"
               >
                  {{ t('common.clear') }}
               </button>
               <button
                  @click="loadProducts"
                  :disabled="loading"
                  class="px-4 py-2 bg-gray-600 text-white rounded-md disabled:opacity-50 hover:bg-gray-700"
               >
                  {{ t('products.list.showAll') }}
               </button>
            </div>

            <div v-if="searchError" class="text-red-600 mt-3">{{ searchError }}</div>
         </div>

         <Table
            :products="paginatedProducts"
            :loading="loading"
            :totalCount="tableTotalCount"
            :isUsingSearch="isUsingSearch"
            :currentPage="currentPage"
            :totalPages="totalPages"
            :pageSize="PAGE_SIZE"
            :getBrandDisplay="getBrandDisplay"
            :getFamilyTags="getFamilyTags"
            :getDiscountedPrice="getDiscountedPrice"
            :formatPrice="formatPrice"
            :goToPage="goToPage"
         />
      </div>
   </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import ProductsSubHeader from './ProductsSubHeader.vue';
import Table from './components/table/index.vue';
import { useBrandFamilyData } from './useBrandFamilyData';
import { supabase } from '../../lib/supabase';
import { useI18n } from '../../i18n/useI18n';

interface Product {
   id: string | number;
   marque: string;
   refciale: string;
   libelle240: string;
   tarif: string | number;
   brand_id?: string | null;
   brand_name?: string | null;
   family_codes?: string[] | null;
}

const PAGE_SIZE = 100;
const SEARCH_LIMIT = 500;
const FAMILY_LINK_BATCH_SIZE = 1000;

const products = ref<Product[]>([]);
const searchResults = ref<Product[]>([]);
const loading = ref(false);
const error = ref('');
const searchError = ref('');
const searchQuery = ref('');
const filterMarque = ref('');
const filterRefciale = ref('');
const filterTarif = ref('');
const filterFamily = ref('');
const exactMatch = ref(false);
const totalCount = ref(0);
const isUsingSearch = ref(false);
const currentPage = ref(1);

const route = useRoute();
const router = useRouter();
const { t } = useI18n();

const { brands, families, loadData: loadBrandData } = useBrandFamilyData();

const brandNameById = computed(() => {
   return brands.value.reduce(
      (acc, brand) => {
         acc[brand.id] = brand.name;
         return acc;
      },
      {} as Record<string, string>
   );
});

const brandNameByNormalized = computed(() => {
   return brands.value.reduce(
      (acc, brand) => {
         acc[brand.name.toLowerCase()] = brand.name;
         return acc;
      },
      {} as Record<string, string>
   );
});

const familyMetaByCode = computed(() => {
   return families.value.reduce(
      (acc, family) => {
         if (family.code) {
            const code = family.code.toLowerCase();
            acc[code] = {
               name: family.name,
               discount: family.discount ?? null,
               hasDiscount: typeof family.discount === 'number' && family.discount > 0,
            };
         }
         return acc;
      },
      {} as Record<string, { name: string; discount: number | null; hasDiscount: boolean }>
   );
});

const displayedProducts = computed(() =>
   isUsingSearch.value ? searchResults.value : products.value
);

const tableTotalCount = computed(() =>
   isUsingSearch.value ? displayedProducts.value.length : totalCount.value
);

const totalPages = computed(() => {
   const total = tableTotalCount.value;
   if (total === 0) return 0;
   return Math.ceil(total / PAGE_SIZE);
});

const paginatedProducts = computed(() => {
   if (!isUsingSearch.value) {
      return products.value;
   }
   const start = (currentPage.value - 1) * PAGE_SIZE;
   const end = start + PAGE_SIZE;
   return searchResults.value.slice(start, end);
});

function matchesFamilyFilter(product: Product, familyFilter: string): boolean {
   const normalizedFilter = familyFilter.trim().toLowerCase();
   if (!normalizedFilter) return true;

   const codes = Array.isArray(product.family_codes) ? product.family_codes : [];
   return codes.some((code) => String(code).trim().toLowerCase() === normalizedFilter);
}

function mapSupabaseProduct(row: any): Product {
   const brandFromJoin = row.brand || null;
   const familyCodes = Array.isArray(row.product_family)
      ? row.product_family
           .map((pf: any) => pf?.family?.code)
           .filter((code: unknown) => typeof code === 'string' && code.trim() !== '')
      : Array.isArray(row.family_codes)
        ? row.family_codes
        : [];

   return {
      id: row.id,
      marque: row.marque || brandFromJoin?.marque || brandFromJoin?.name || '',
      refciale: row.refciale || row.sku || '',
      libelle240: row.libelle240 || row.name || '',
      tarif: row.tarif ?? row.price ?? '',
      brand_id: row.brand_id || null,
      brand_name: row.brand_name || brandFromJoin?.name || null,
      family_codes: familyCodes,
   };
}

function applyClientFilters(list: Product[]): Product[] {
   const normalizedSearch = searchQuery.value.trim().toLowerCase();
   const normalizedMarque = filterMarque.value.trim().toLowerCase();
   const normalizedRef = filterRefciale.value.trim().toLowerCase();
   const normalizedTarif = filterTarif.value.trim().toLowerCase();

   return list.filter((product) => {
      if (normalizedSearch) {
         const haystack =
            `${product.libelle240 || ''} ${product.refciale || ''} ${product.marque || ''}`
               .toLowerCase()
               .trim();
         if (!haystack.includes(normalizedSearch)) {
            return false;
         }
      }

      if (normalizedMarque) {
         const brandLabel = `${product.marque || ''} ${product.brand_name || ''}`.toLowerCase();
         if (!brandLabel.includes(normalizedMarque)) {
            return false;
         }
      }

      if (
         normalizedRef &&
         (exactMatch.value
            ? String(product.refciale || '').toLowerCase() !== normalizedRef
            : !String(product.refciale || '')
                 .toLowerCase()
                 .includes(normalizedRef))
      ) {
         return false;
      }

      if (
         normalizedTarif &&
         !String(product.tarif ?? '')
            .toLowerCase()
            .includes(normalizedTarif)
      ) {
         return false;
      }

      if (!matchesFamilyFilter(product, filterFamily.value)) {
         return false;
      }

      return true;
   });
}

async function loadProducts(page = 1) {
   loading.value = true;
   error.value = '';
   searchError.value = '';
   isUsingSearch.value = false;
   searchResults.value = [];
   currentPage.value = Math.max(1, page);

   await syncQueryToUrl();

   try {
      const from = (currentPage.value - 1) * PAGE_SIZE;
      const to = from + PAGE_SIZE - 1;
      const {
         data,
         count,
         error: queryError,
      } = await supabase
         .from('product')
         .select('*, brand:brand_id(id,name,marque), product_family(family:family_id(code))', {
            count: 'exact',
         })
         .order('sku', { ascending: true })
         .range(from, to);

      if (queryError) throw queryError;

      const mapped = (data || []).map(mapSupabaseProduct);
      products.value = mapped;
      totalCount.value = count || 0;
   } catch (e: any) {
      error.value = String(e?.message || e);
   } finally {
      loading.value = false;
   }
}

async function performSearch(options?: { preservePage?: boolean }) {
   const hasQuery = searchQuery.value.trim().length > 0;
   const hasFilters =
      filterMarque.value.trim() ||
      filterRefciale.value.trim() ||
      filterTarif.value.trim() ||
      filterFamily.value.trim();

   console.log('performSearch called with', {
      searchQuery: searchQuery.value,
      filterMarque: filterMarque.value,
      filterRefciale: filterRefciale.value,
      filterTarif: filterTarif.value,
      filterFamily: filterFamily.value,
      exactMatch: exactMatch.value,
   });
   if (!hasQuery && !hasFilters) {
      await loadProducts();
      return;
   }

   if (!options?.preservePage) {
      currentPage.value = 1;
   }

   await syncQueryToUrl();
   loading.value = true;
   searchError.value = '';
   searchResults.value = [];

   try {
      let familyFilteredProducts: Product[] | null = null;

      if (filterFamily.value.trim()) {
         const { data: matchingFamilies, error: familyError } = await supabase
            .from('family')
            .select('id')
            .ilike('code', filterFamily.value.trim());

         if (familyError) throw familyError;

         const familyIds = (matchingFamilies || []).map((family: any) => family.id).filter(Boolean);
         if (!familyIds.length) {
            searchResults.value = [];
            isUsingSearch.value = true;
            return;
         }

         const deduped = new Map<string, Product>();
         let from = 0;

         while (true) {
            const to = from + FAMILY_LINK_BATCH_SIZE - 1;
            const { data: linkedRows, error: linkedRowsError } = await supabase
               .from('product_family')
               .select(
                  'product:product_id(*, brand:brand_id(id,name,marque), product_family(family:family_id(code)))'
               )
               .in('family_id', familyIds)
               .range(from, to);

            if (linkedRowsError) throw linkedRowsError;

            const batch = linkedRows || [];
            for (const row of batch) {
               const product = (row as any).product;
               if (!product?.id) continue;
               deduped.set(String(product.id), mapSupabaseProduct(product));
            }

            if (batch.length < FAMILY_LINK_BATCH_SIZE) {
               break;
            }

            from += FAMILY_LINK_BATCH_SIZE;
         }

         familyFilteredProducts = Array.from(deduped.values());

         if (!familyFilteredProducts.length) {
            searchResults.value = [];
            isUsingSearch.value = true;
            return;
         }
      }

      if (familyFilteredProducts) {
         searchResults.value = applyClientFilters(familyFilteredProducts);
         isUsingSearch.value = true;
         if (options?.preservePage) {
            currentPage.value = Math.min(Math.max(1, currentPage.value), totalPages.value || 1);
         }
         return;
      }

      let query = supabase
         .from('product')
         .select('*, brand:brand_id(id,name,marque), product_family(family:family_id(code))')
         .order('sku', { ascending: true })
         .range(0, SEARCH_LIMIT - 1);

      if (filterRefciale.value.trim()) {
         const refFilter = filterRefciale.value.trim();
         query = exactMatch.value
            ? query.ilike('sku', refFilter)
            : query.ilike('sku', `%${refFilter}%`);
      }

      if (searchQuery.value.trim()) {
         const q = searchQuery.value.trim().replace(/,/g, ' ');
         query = query.or(`name.ilike.%${q}%,sku.ilike.%${q}%`);
      }

      const { data, error: queryError } = await query;
      if (queryError) throw queryError;

      const mappedResults = (data || []).map(mapSupabaseProduct);
      searchResults.value = applyClientFilters(mappedResults);
      isUsingSearch.value = true;
      if (options?.preservePage) {
         currentPage.value = Math.min(Math.max(1, currentPage.value), totalPages.value || 1);
      }
   } catch (e: any) {
      searchError.value = String(e?.message || e);
   } finally {
      loading.value = false;
   }
}

function clearSearch() {
   filterMarque.value = '';
   filterRefciale.value = '';
   filterTarif.value = '';
   filterFamily.value = '';
   exactMatch.value = false;
   searchQuery.value = '';
   searchResults.value = [];
   searchError.value = '';
   isUsingSearch.value = false;
   currentPage.value = 1;
   syncQueryToUrl();
}

async function goToPage(page: number) {
   const target = Math.max(1, page);
   if (target === currentPage.value) return;

   if (isUsingSearch.value) {
      currentPage.value = Math.min(target, totalPages.value || 1);
      await syncQueryToUrl();
      return;
   }

   const maxPage = Math.max(1, Math.ceil(totalCount.value / PAGE_SIZE));
   await loadProducts(Math.min(target, maxPage));
}

function formatPrice(price: string | number): string {
   const num = typeof price === 'string' ? parseFloat(price) : price;
   if (isNaN(num)) return '-';
   return (
      '€ ' + num.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
   );
}

function getBrandDisplay(product: Product): string {
   if (product.brand_name) return product.brand_name;
   if (product.brand_id && brandNameById.value[product.brand_id]) {
      return brandNameById.value[product.brand_id] || 'none';
   }

   const normalizedMarque = product.marque?.trim().toLowerCase();
   if (normalizedMarque && brandNameByNormalized.value[normalizedMarque]) {
      return brandNameByNormalized.value[normalizedMarque];
   }

   return 'none';
}

function getFamilyTags(
   product: Product
): { label: string; hasDiscount: boolean; isNetPrice: boolean; href: string }[] {
   const skuLower = String(product.refciale || '')
      .trim()
      .toLowerCase();
   const directNetPriceFamily = skuLower
      ? (families.value.find(
           (f) =>
              String(f.product_code || '')
                 .trim()
                 .toLowerCase() === skuLower && (f.type || '').toLowerCase() === 'net_price'
        ) ?? null)
      : null;

   const codes = product.family_codes || [];
   const discountsByCode = codes
      .map((code) => {
         const normalizedCode = String(code).trim().toLowerCase();
         const discount = familyMetaByCode.value[normalizedCode]?.discount;
         return typeof discount === 'number' && discount > 0 ? discount : null;
      })
      .filter((discount): discount is number => typeof discount === 'number');

   const bestDiscount = discountsByCode.length ? Math.max(...discountsByCode) : null;

   const tags: { label: string; hasDiscount: boolean; isNetPrice: boolean; href: string }[] = [];

   if (directNetPriceFamily) {
      const sku = String(product.refciale || '').trim();
      const href = sku
         ? `/vendors/family?tab=all&sku=${encodeURIComponent(sku)}&exactMatch=true`
         : '/vendors/family?tab=all';
      tags.push({ label: 'NET', hasDiscount: false, isNetPrice: true, href });
   }

   tags.push(
      ...codes
         .map((code) => String(code).trim())
         .filter(Boolean)
         .map((code) => {
            const meta = familyMetaByCode.value[code.toLowerCase()];
            const hasDiscount =
               !directNetPriceFamily &&
               typeof meta?.discount === 'number' &&
               bestDiscount !== null &&
               meta.discount === bestDiscount;
            const nameLabel = meta?.name ? `${code} ${meta.name}` : code;
            const discountLabel =
               typeof meta?.discount === 'number' && meta.discount > 0
                  ? ` (${meta.discount}%)`
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
}

function getDiscountedPrice(product: Product): { original: number; discounted: number } | null {
   const price = typeof product.tarif === 'string' ? parseFloat(product.tarif) : product.tarif;
   if (!Number.isFinite(price)) return null;

   const skuLower = String(product.refciale || '')
      .trim()
      .toLowerCase();
   const directNetPriceFamily = skuLower
      ? (families.value.find(
           (f) =>
              String(f.product_code || '')
                 .trim()
                 .toLowerCase() === skuLower && (f.type || '').toLowerCase() === 'net_price'
        ) ?? null)
      : null;

   if (directNetPriceFamily && typeof directNetPriceFamily.net_price === 'number') {
      return { original: price, discounted: directNetPriceFamily.net_price };
   }

   const discounts = (product.family_codes || [])
      .map((code) => familyMetaByCode.value[String(code).toLowerCase()]?.discount)
      .filter((value): value is number => typeof value === 'number' && value > 0);

   if (!discounts.length) return null;

   const maxDiscount = Math.max(...discounts);
   const discounted = price * (1 - maxDiscount / 100);
   return { original: price, discounted };
}

function applyQueryFromUrl() {
   const query = route.query;
   const getValue = (value: unknown) => (Array.isArray(value) ? value[0] : value) ?? '';

   searchQuery.value = String(getValue(query.q) || '').trim();
   filterMarque.value = String(getValue(query.marque) || '').trim();
   filterRefciale.value = String(getValue(query.refciale) || '').trim();
   filterTarif.value = String(getValue(query.tarif) || '').trim();
   filterFamily.value = String(getValue(query.family) || '').trim();
   exactMatch.value = String(getValue(query.exactMatch) || '').toLowerCase() === 'true';
   const parsedPage = Number.parseInt(String(getValue(query.page) || '1'), 10);
   currentPage.value = Number.isFinite(parsedPage) && parsedPage > 0 ? parsedPage : 1;
}

async function syncQueryToUrl() {
   const nextQuery: Record<string, string> = {};
   if (searchQuery.value.trim()) nextQuery.q = searchQuery.value.trim();
   if (filterMarque.value.trim()) nextQuery.marque = filterMarque.value.trim();
   if (filterRefciale.value.trim()) nextQuery.refciale = filterRefciale.value.trim();
   if (filterTarif.value.trim()) nextQuery.tarif = filterTarif.value.trim();
   if (filterFamily.value.trim()) nextQuery.family = filterFamily.value.trim();
   if (exactMatch.value) nextQuery.exactMatch = 'true';
   if (currentPage.value > 1) nextQuery.page = String(currentPage.value);

   const scrollY = typeof window !== 'undefined' ? window.scrollY : 0;
   await router.replace({ query: nextQuery });

   if (typeof window !== 'undefined') {
      await nextTick();
      window.scrollTo({ top: scrollY, left: 0, behavior: 'auto' });
   }
}

onMounted(() => {
   applyQueryFromUrl();
   loadBrandData();
   if (
      searchQuery.value ||
      filterMarque.value ||
      filterRefciale.value ||
      filterTarif.value ||
      filterFamily.value
   ) {
      performSearch({ preservePage: true });
   } else {
      loadProducts(currentPage.value);
   }
});
</script>
