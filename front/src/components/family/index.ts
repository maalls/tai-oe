// JS/TS logic extracted from index.vue
import { computed, onMounted, ref, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useBrandFamilyData } from '../products/useBrandFamilyData';
import { searchProductBySku } from '../../composables/useSuggestionSearch';
import { useI18n } from '../../i18n/useI18n';
import { createFamily, deleteFamily as deleteFamilyApi, updateFamily } from '../../api/family';
import { useAuthWithProfile } from '../../composables/useAuthWithProfile';

export function useFamilyPageLogic() {
   const { userRole } = useAuthWithProfile();
   const router = useRouter();
   const route = useRoute();
   const { t } = useI18n();
   const PAGE_SIZE = 100;
   const { brands, families, isLoading, errorMessage, loadData } = useBrandFamilyData();
   const codeQuery = ref('');
   const typeQuery = ref('');
   const skuQuery = ref('');
   const familyTypeTab = ref<'all' | 'discount' | 'net_price'>('discount');
   const exactMatch = ref(true);
   const showDiscountOnly = ref(true);
   const brandIdFilter = ref<string | null>(null);
   const isSavingById = ref<Record<string, boolean>>({});
   const isDeletingById = ref<Record<string, boolean>>({});
   const savedFlashById = ref<Record<string, boolean>>({});
   const isCreatingFamily = ref(false);
   const currentPage = ref(1);

   // Product code search state
   const productCodeSuggestions = ref<Record<string, any[]>>({});
   const productCodeSearchLoading = ref<Record<string, boolean>>({});
   const productCodeSearchError = ref<Record<string, string>>({});
   const productCodeSearchTimeout = ref<Record<string, ReturnType<typeof setTimeout>>>({});
   const activeProductCodeFamilyId = ref<string | null>(null);
   const lastSyncedNetPriceSkuByFamilyId = ref<Record<string, string | null>>({});

   const brandLookup = computed<Record<string, string>>(() => {
      return brands.value.reduce(
         (acc, brand) => {
            acc[brand.id] = brand.name;
            return acc;
         },
         {} as Record<string, string>
      );
   });

   const hasActiveFilters = computed(() => {
      return (
         familyTypeTab.value !== 'discount' ||
         codeQuery.value.trim().length > 0 ||
         typeQuery.value.trim().length > 0 ||
         skuQuery.value.trim().length > 0 ||
         brandIdFilter.value !== null ||
         exactMatch.value !== true ||
         showDiscountOnly.value !== true
      );
   });

   const filteredFamilies = computed(() => {
      return families.value
         .filter((family) => {
            if (familyTypeTab.value !== 'all') {
               const normalizedFamilyType = (family.type || '').toLowerCase();
               const selectedType = familyTypeTab.value === 'net_price' ? 'net_price' : 'discount';
               if (normalizedFamilyType !== selectedType) {
                  return false;
               }
            }
            if (brandIdFilter.value && family.brand_id !== brandIdFilter.value) {
               return false;
            }
            const code = family.code ? family.code.toLowerCase() : '';
            const type = family.type ? family.type.toLowerCase() : '';
            const sku = family.product_code ? family.product_code.toLowerCase() : '';
            const normalizedCodeQuery = codeQuery.value.toLowerCase();
            const normalizedTypeQuery = typeQuery.value.toLowerCase();
            const normalizedSkuQuery = skuQuery.value.toLowerCase();
            if (normalizedCodeQuery) {
               if (exactMatch.value) {
                  if (code !== normalizedCodeQuery) {
                     return false;
                  }
               } else if (!code.includes(normalizedCodeQuery)) {
                  return false;
               }
            }
            if (normalizedTypeQuery) {
               if (exactMatch.value) {
                  if (type !== normalizedTypeQuery) {
                     return false;
                  }
               } else if (!type.includes(normalizedTypeQuery)) {
                  return false;
               }
            }
            if (normalizedSkuQuery) {
               if (exactMatch.value) {
                  if (sku !== normalizedSkuQuery) {
                     return false;
                  }
               } else if (!sku.includes(normalizedSkuQuery)) {
                  return false;
               }
            }
            if (familyTypeTab.value === 'discount' && showDiscountOnly.value) {
               const discount = family.discount;
               if (typeof discount !== 'number' || discount <= 0) {
                  return false;
               }
            }
            return true;
         })
         .sort((a, b) => {
            const codeA = (a.code || '').toLowerCase();
            const codeB = (b.code || '').toLowerCase();
            return codeA.localeCompare(codeB, undefined, { numeric: true, sensitivity: 'base' });
         });
   });

   const totalPages = computed(() => {
      const total = filteredFamilies.value.length;
      if (total === 0) return 0;
      return Math.ceil(total / PAGE_SIZE);
   });

   const paginatedFamilies = computed(() => {
      const start = (currentPage.value - 1) * PAGE_SIZE;
      const end = start + PAGE_SIZE;
      return filteredFamilies.value.slice(start, end);
   });

   const shownResultsText = computed(() => {
      const shown = paginatedFamilies.value.length;
      const total = filteredFamilies.value.length;
      return t('products.table.showing', { count: shown, total });
   });

   const goToPage = (page: number) => {
      if (page < 1 || page > totalPages.value) return;
      currentPage.value = page;
   };

   const syncUrlWithFilters = async () => {
      const query: Record<string, string> = {};
      if (familyTypeTab.value !== 'discount') {
         query.tab = familyTypeTab.value;
      }
      if (codeQuery.value.trim()) {
         query.code = codeQuery.value.trim();
      }
      if (typeQuery.value.trim()) {
         query.type = typeQuery.value.trim();
      }
      if (skuQuery.value.trim()) {
         query.sku = skuQuery.value.trim();
      }
      if (!exactMatch.value) {
         query.exactMatch = 'false';
      }
      if (showDiscountOnly.value) {
         query.discount_only = 'true';
      }
      if (brandIdFilter.value) {
         query.brand_id = brandIdFilter.value;
      }
      await router.replace({ query });
   };

   const applyUrlFilters = () => {
      const queryTab = route.query.tab;
      if (queryTab === 'all') {
         familyTypeTab.value = 'all';
      } else if (queryTab === 'net_price') {
         familyTypeTab.value = 'net_price';
      } else {
         familyTypeTab.value = 'discount';
      }
      const queryCode = route.query.code;
      codeQuery.value = typeof queryCode === 'string' ? queryCode : '';
      const queryType = route.query.type;
      typeQuery.value = typeof queryType === 'string' ? queryType : '';
      const querySku = route.query.sku;
      skuQuery.value = typeof querySku === 'string' ? querySku : '';
      const queryExactMatch = route.query.exactMatch;
      exactMatch.value = queryExactMatch === 'false' ? false : true;
      const queryDiscountOnly = route.query.discount_only;
      showDiscountOnly.value = queryDiscountOnly === 'true' ? true : false;
      const queryBrandId = route.query.brand_id;
      brandIdFilter.value = typeof queryBrandId === 'string' ? queryBrandId : null;
   };

   onMounted(() => {
      loadData();
      applyUrlFilters();
   });

   watch(
      [familyTypeTab, codeQuery, typeQuery, skuQuery, exactMatch, showDiscountOnly, brandIdFilter],
      () => {
         currentPage.value = 1;
         syncUrlWithFilters();
      }
   );

   watch(filteredFamilies, () => {
      if (totalPages.value === 0) {
         currentPage.value = 1;
         return;
      }
      if (currentPage.value > totalPages.value) {
         currentPage.value = totalPages.value;
      }
   });

   const clearFilters = () => {
      familyTypeTab.value = 'discount';
      codeQuery.value = '';
      typeQuery.value = '';
      skuQuery.value = '';
      brandIdFilter.value = null;
      exactMatch.value = true;
      showDiscountOnly.value = true;
      currentPage.value = 1;
   };

   const addFamily = async () => {
      const selectedBrandId = brandIdFilter.value || brands.value[0]?.id || null;
      if (!selectedBrandId) {
         errorMessage.value = 'Please select a brand before adding a family.';
         return;
      }
      isCreatingFamily.value = true;
      try {
         const type = familyTypeTab.value === 'all' ? 'discount' : familyTypeTab.value;
         const payload: Record<string, any> = {
            brand_id: selectedBrandId,
            type,
            name: '',
            code: null,
            product_code: null,
            quantity: 0,
            discount: 0,
            minimum_margin: 0,
            target_margin: 0,
            net_price: type === 'net_price' ? 0 : null,
         };
         await createFamily(payload);
         await loadData();
         if (type === 'discount' && showDiscountOnly.value) {
            showDiscountOnly.value = false;
         }
      } catch (error) {
         errorMessage.value = error instanceof Error ? error.message : 'Failed to add family.';
      } finally {
         isCreatingFamily.value = false;
      }
   };

   const formatListPrice = (value: number) => {
      return new Intl.NumberFormat('fr-FR', {
         minimumFractionDigits: 2,
         maximumFractionDigits: 2,
      }).format(Number(value) || 0);
   };

   const truncateDescription = (value: string | null | undefined) => {
      const text = String(value || '');
      if (text.length <= 50) return text;
      return `${text.slice(0, 50)}...`;
   };

   const triggerSavedFlash = (familyId: string) => {
      savedFlashById.value = { ...savedFlashById.value, [familyId]: true };
      setTimeout(() => {
         savedFlashById.value = { ...savedFlashById.value, [familyId]: false };
      }, 800);
   };

   const performProductCodeSearch = (familyId: string, query: string) => {
      if (productCodeSearchTimeout.value[familyId]) {
         clearTimeout(productCodeSearchTimeout.value[familyId]);
      }
      productCodeSearchError.value[familyId] = '';
      if (!query || query.length < 2) {
         productCodeSuggestions.value[familyId] = [];
         productCodeSearchLoading.value[familyId] = false;
         return;
      }
      productCodeSearchLoading.value[familyId] = true;
      productCodeSearchTimeout.value[familyId] = setTimeout(() => {
         searchProductBySku(
            query,
            (products, error) => {
               productCodeSuggestions.value[familyId] = products;
               if (error) {
                  productCodeSearchError.value[familyId] = error;
               }
               productCodeSearchLoading.value[familyId] = false;
            },
            () => {}
         );
      }, 300);
   };

   const selectProductCodeSuggestion = (familyId: string, product: any) => {
      const family = families.value.find((f) => f.id === familyId);
      if (!family) return;
      family.product_code = product.sku;
      family.name = product.name || family.name;
      family.product = product;
      if (product.brand_id) {
         family.brand_id = product.brand_id;
      }
      productCodeSuggestions.value[familyId] = [];
      productCodeSearchError.value[familyId] = '';
      productCodeSearchLoading.value[familyId] = false;
      activeProductCodeFamilyId.value = null;
      saveFamily(family);
   };

   const openProductCodeSuggestions = (familyId: string, currentQuery: string) => {
      activeProductCodeFamilyId.value = familyId;
      performProductCodeSearch(familyId, currentQuery);
   };

   const closeProductCode = (familyId: string, event?: FocusEvent) => {
      const nextTarget = event?.relatedTarget as HTMLElement | null;
      if (nextTarget?.dataset?.productSuggestion === 'true') {
         return;
      }
      closeProductCodeSuggestions(familyId);
      const family = families.value.find((f) => f.id === familyId);
      if (!family) {
         return;
      }
      saveFamily(family);
   };

   const closeProductCodeSuggestions = (familyId: string) => {
      window.setTimeout(() => {
         if (activeProductCodeFamilyId.value === familyId) {
            activeProductCodeFamilyId.value = null;
         }
      }, 150);
   };

   const syncNetPriceFamilyProductLink = async (family: (typeof families.value)[number]) => {
      const sku = String(family.product_code || '').trim();
      const normalizedSku = sku.length > 0 ? sku : null;
      if (lastSyncedNetPriceSkuByFamilyId.value[family.id] === normalizedSku) {
         return;
      }
      lastSyncedNetPriceSkuByFamilyId.value[family.id] = normalizedSku;
   };

   const saveFamily = async (family: (typeof families.value)[number]) => {
      isSavingById.value = { ...isSavingById.value, [family.id]: true };
      try {
         const payload = {
            name: family.name || null,
            brand_id: family.brand_id || null,
            product_code: family.product_code || null,
            quantity: family.quantity,
            discount: family.discount,
            minimum_margin: family.minimum_margin,
            target_margin: family.target_margin,
            unit: family.unit || null,
            packing: family.packing || null,
            lead_time_week: family.lead_time_week,
            net_price: family.net_price,
         };
         const updatedFamily = await updateFamily(family.id, payload);
         await syncNetPriceFamilyProductLink(family);
         const familyIndex = families.value.findIndex((row) => row.id === family.id);
         if (familyIndex !== -1) {
            const previous = families.value[familyIndex];
            const resolvedProduct = previous.product;
            if (
               previous.type === 'net_price' &&
               previous.product_code &&
               resolvedProduct?.sku === previous.product_code
            ) {
               families.value[familyIndex] = {
                  ...previous,
                  ...updatedFamily,
                  product: resolvedProduct,
               };
            } else {
               families.value[familyIndex] = {
                  ...previous,
                  ...updatedFamily,
               };
            }
         }
         triggerSavedFlash(family.id);
      } catch (error) {
         // eslint-disable-next-line no-console
         console.error('[FamilyPage] Failed to save family fields:', error);
      } finally {
         isSavingById.value = { ...isSavingById.value, [family.id]: false };
      }
   };

   const deleteFamily = async (family: (typeof families.value)[number]) => {
      const confirmed = window.confirm('Delete this family?');
      if (!confirmed) return;
      isDeletingById.value = { ...isDeletingById.value, [family.id]: true };
      errorMessage.value = '';
      try {
         await deleteFamilyApi(family.id);
         await loadData();
         if (activeProductCodeFamilyId.value === family.id) {
            activeProductCodeFamilyId.value = null;
         }
         const nextDeleting = { ...isDeletingById.value };
         delete nextDeleting[family.id];
         isDeletingById.value = nextDeleting;
      } catch (error) {
         errorMessage.value = error instanceof Error ? error.message : 'Failed to delete family.';
      } finally {
         isDeletingById.value = { ...isDeletingById.value, [family.id]: false };
      }
   };

   return {
      t,
      userRole,
      brands,
      families,
      isLoading,
      errorMessage,
      loadData,
      codeQuery,
      typeQuery,
      skuQuery,
      familyTypeTab,
      exactMatch,
      showDiscountOnly,
      brandIdFilter,
      isSavingById,
      isDeletingById,
      savedFlashById,
      isCreatingFamily,
      currentPage,
      productCodeSuggestions,
      productCodeSearchLoading,
      productCodeSearchError,
      productCodeSearchTimeout,
      activeProductCodeFamilyId,
      lastSyncedNetPriceSkuByFamilyId,
      brandLookup,
      hasActiveFilters,
      filteredFamilies,
      totalPages,
      paginatedFamilies,
      shownResultsText,
      goToPage,
      syncUrlWithFilters,
      applyUrlFilters,
      clearFilters,
      addFamily,
      formatListPrice,
      truncateDescription,
      triggerSavedFlash,
      performProductCodeSearch,
      selectProductCodeSuggestion,
      openProductCodeSuggestions,
      closeProductCode,
      closeProductCodeSuggestions,
      syncNetPriceFamilyProductLink,
      saveFamily,
      deleteFamily,
   };
}
