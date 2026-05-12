import { createRouter, createWebHistory } from 'vue-router';
import SourcePage from '../components/admin/components/source/IndexPage.vue';
import DatabasePage from '../components/admin/components/database/IndexPage.vue';
import CartouchesPage from '../components/database/CartouchesPage.vue';
import CommercePage from '../components/database/CommercePage.vue';
import QdrantPage from '../components/admin/components/qdrant/IndexPage.vue';
import AdminFlowPage from '../components/admin/components/flow/IndexPage.vue';
import ChatPage from '../components/chat/IndexPage.vue';
import MailPage from '../components/mail/IndexPage.vue';
import OpportunityPage from '../components/opportunity/IndexPage.vue';
import OpportunitySourcePage from '../components/opportunity/components/source/SourcePage.vue';
import OpportunityAccountPage from '../components/opportunity/components/account/AccountPage.vue';
import OpportunityQuotePage from '../components/opportunity/components/quote/QuotePage.vue';
import OpportunityPreviewPage from '../components/opportunity/components/preview/PreviewPage.vue';
import OpportunitySendPage from '../components/opportunity/components/send/SendPage.vue';
import OpportunityPipelinePage from '../components/opportunity/components/pipeline/PipelinePage.vue';
import OpportunitySettingsPage from '../components/opportunity/components/settings/SettingsPage.vue';
import OpportunityDocumentsPage from '../components/opportunity/components/documents/DocumentsPage.vue';
import OpportunityDocumentDetailPage from '../components/opportunity/components/documents/DocumentDetailPage.vue';
import OpportunityInvoicesPage from '../components/opportunity/components/invoices/InvoicesPage.vue';
import OpportunityInvoiceDetailPage from '../components/opportunity/components/invoices/InvoiceDetailPage.vue';
import OpportunityActionsPage from '../components/opportunity/components/actions/ActionsPage.vue';
import OpportunityChatPage from '../components/opportunity/components/chat/ChatPage.vue';
import AccountPage from '../components/account/IndexPage.vue';
import AccountEditPage from '../components/account/Edit.vue';
import ContactPage from '../components/contact/IndexPage.vue';
import ContactDetailPage from '../components/contact/DetailPage.vue';
import ClientPage from '../components/client/IndexPage.vue';
import ProductPage from '../components/products/IndexPage.vue';
import ProductDetailPage from '../components/products/DetailPage.vue';
import ProductBrandPage from '../components/products/BrandPage.vue';
import ProductBrandEditPage from '../components/products/BrandEditPage.vue';
import ProductEditPage from '../components/products/edit.vue';
import ProductFamilyPage from '../components/family/index.vue';
import FamilyDiscountPage from '../components/family/show.vue';
import VendorPage from '../components/vendor/index.vue';
import VendorEditPage from '../components/vendor/Edit.vue';
import AdminPage from '../components/admin/IndexPage.vue';
import SettingsPage from '../components/settings/IndexPage.vue';
import LoginPage from '../components/login/IndexPage.vue';
import ResetPasswordPage from '../components/login/ResetPasswordPage.vue';
import { useAuth } from '../stores/auth';
import i18n from '../i18n';

const router = createRouter({
   history: createWebHistory(),
   routes: [
      {
         path: '/login',
         name: 'login',
         component: LoginPage,
         meta: { requiresGuest: true, titleKey: 'pageTitles.login' },
      },
      {
         path: '/reset-password',
         name: 'reset-password',
         component: ResetPasswordPage,
         meta: { titleKey: 'pageTitles.login' },
      },
      {
         path: '/',
         redirect: '/vendors',
      },
      {
         path: '/admin/source',
         name: 'admin-source',
         component: SourcePage,
         meta: { requiresAuth: true, titleKey: 'pageTitles.adminSource' },
      },
      {
         path: '/admin/database',
         component: DatabasePage,
         redirect: '/admin/database/cartouches',
         meta: { requiresAuth: true, titleKey: 'pageTitles.adminDatabase' },
         children: [
            {
               path: 'cartouches',
               name: 'cartouches',
               component: CartouchesPage,
               meta: { titleKey: 'pageTitles.adminDatabaseCartouches' },
            },
            {
               path: 'commerce',
               name: 'commerce',
               component: CommercePage,
               meta: { titleKey: 'pageTitles.adminDatabaseCommerce' },
            },
         ],
      },
      {
         path: '/admin/qdrant',
         name: 'admin-qdrant',
         component: QdrantPage,
         meta: { requiresAuth: true, titleKey: 'pageTitles.adminQdrant' },
      },
      {
         path: '/admin/flow',
         name: 'admin-flow',
         component: AdminFlowPage,
         meta: { requiresAuth: true, titleKey: 'pageTitles.adminFlow' },
      },
      {
         path: '/source',
         redirect: '/admin/source',
      },
      {
         path: '/database',
         redirect: '/admin/database',
      },
      {
         path: '/database/:subpath(.*)',
         redirect: (to) => `/admin/database/${to.params.subpath}`,
      },
      {
         path: '/qdrant',
         redirect: '/admin/qdrant',
      },
      {
         path: '/chat',
         name: 'chat',
         component: ChatPage,
         meta: { requiresAuth: true, titleKey: 'pageTitles.chat' },
      },
      {
         path: '/mail',
         name: 'mail',
         component: MailPage,
         meta: { requiresAuth: true, titleKey: 'pageTitles.mail' },
      },
      {
         path: '/mail/:category',
         name: 'mail-category',
         component: MailPage,
         meta: {
            requiresAuth: true,
            titleKey: 'pageTitles.mailCategory',
            titleParams: (to: any) => ({ category: String(to.params.category || '').trim() }),
         },
      },
      {
         path: '/opportunities',
         name: 'opportunities',
         component: OpportunityPage,
         meta: { requiresAuth: true, titleKey: 'pageTitles.opportunities' },
      },
      {
         path: '/opportunities/:id',
         redirect: (to) => `/opportunities/${to.params.id}/source`,
      },
      {
         path: '/opportunities/:id/source',
         name: 'opportunity-source',
         component: OpportunitySourcePage,
         meta: { requiresAuth: true, titleKey: 'pageTitles.opportunitySource' },
      },
      {
         path: '/opportunities/:id/account',
         name: 'opportunity-account',
         component: OpportunityAccountPage,
         meta: { requiresAuth: true, titleKey: 'pageTitles.opportunityAccount' },
      },
      {
         path: '/opportunities/:id/quote',
         name: 'opportunity-quote',
         component: OpportunityQuotePage,
         meta: { requiresAuth: true, titleKey: 'pageTitles.opportunityQuote' },
      },
      {
         path: '/opportunities/:id/preview',
         name: 'opportunity-preview',
         component: OpportunityPreviewPage,
         meta: { requiresAuth: true, titleKey: 'pageTitles.opportunityPreview' },
      },
      {
         path: '/opportunities/:id/send',
         name: 'opportunity-send',
         component: OpportunitySendPage,
         meta: { requiresAuth: true, titleKey: 'pageTitles.opportunitySend' },
      },
      {
         path: '/opportunities/:id/pipeline',
         name: 'opportunity-pipeline',
         component: OpportunityPipelinePage,
         meta: { requiresAuth: true, titleKey: 'pageTitles.opportunityPipeline' },
      },
      {
         path: '/opportunities/:id/settings',
         name: 'opportunity-settings',
         component: OpportunitySettingsPage,
         meta: { requiresAuth: true, titleKey: 'pageTitles.opportunitySettings' },
      },
      {
         path: '/opportunities/:id/documents',
         name: 'opportunity-documents',
         component: OpportunityDocumentsPage,
         meta: { requiresAuth: true, titleKey: 'pageTitles.opportunityDocuments' },
      },
      {
         path: '/opportunities/:id/documents/:documentId',
         name: 'opportunity-document-detail',
         component: OpportunityDocumentDetailPage,
         meta: { requiresAuth: true, titleKey: 'pageTitles.opportunityDocuments' },
      },
      {
         path: '/opportunities/:id/invoices',
         name: 'opportunity-invoices',
         component: OpportunityInvoicesPage,
         meta: { requiresAuth: true, titleKey: 'pageTitles.opportunityInvoices' },
      },
      {
         path: '/opportunities/:id/invoices/:invoiceId',
         name: 'opportunity-invoice-detail',
         component: OpportunityInvoiceDetailPage,
         meta: { requiresAuth: true, titleKey: 'pageTitles.opportunityInvoice' },
      },
      {
         path: '/opportunities/:id/actions',
         name: 'opportunity-actions',
         component: OpportunityActionsPage,
         meta: { requiresAuth: true, titleKey: 'pageTitles.opportunityActions' },
      },
      {
         path: '/opportunities/:id/chat',
         name: 'opportunity-chat',
         component: OpportunityChatPage,
         meta: { requiresAuth: true, titleKey: 'pageTitles.opportunityChat' },
      },
      {
         path: '/accounts',
         name: 'accounts',
         component: AccountPage,
         meta: { requiresAuth: true, titleKey: 'pageTitles.accounts' },
      },
      {
         path: '/accounts/:id',
         name: 'account-detail',
         component: AccountEditPage,
         meta: { requiresAuth: true, titleKey: 'pageTitles.accountDetail' },
      },
      {
         path: '/contacts',
         name: 'contacts',
         component: ContactPage,
         meta: { requiresAuth: true, titleKey: 'pageTitles.contacts' },
      },
      {
         path: '/contacts/:id',
         name: 'contact-detail',
         component: ContactDetailPage,
         meta: { requiresAuth: true, titleKey: 'pageTitles.contactDetail' },
      },
      {
         path: '/client',
         name: 'client',
         component: ClientPage,
         meta: { requiresAuth: true, titleKey: 'pageTitles.client' },
      },
      {
         path: '/products',
         name: 'products',
         component: ProductPage,
         meta: { requiresAuth: true, titleKey: 'pageTitles.products' },
      },
      {
         path: '/products/new',
         name: 'product-new',
         component: ProductEditPage,
         meta: { requiresAuth: true, titleKey: 'pageTitles.productNew' },
      },
      {
         path: '/products/:id/edit',
         name: 'product-edit',
         component: ProductEditPage,
         meta: { requiresAuth: true, titleKey: 'pageTitles.productEdit' },
      },
      {
         path: '/products/brand',
         redirect: '/vendors/brand',
      },
      {
         path: '/products/family',
         redirect: '/vendors/family',
      },
      {
         path: '/vendors/brand',
         name: 'vendors-brand',
         component: ProductBrandPage,
         meta: { requiresAuth: true, titleKey: 'pageTitles.productsBrand' },
      },
      {
         path: '/vendors/brand/new',
         name: 'vendor-brand-new',
         component: ProductBrandEditPage,
         meta: { requiresAuth: true, titleKey: 'pageTitles.productsBrand' },
      },
      {
         path: '/vendors/brand/:id',
         name: 'vendor-brand-edit',
         component: ProductBrandEditPage,
         meta: { requiresAuth: true, titleKey: 'pageTitles.productsBrand' },
      },
      {
         path: '/vendors/family',
         name: 'vendors-family',
         component: ProductFamilyPage,
         meta: { requiresAuth: true, titleKey: 'pageTitles.productsFamily' },
      },
      {
         path: '/family/:id/discount',
         name: 'family-discount',
         component: FamilyDiscountPage,
         meta: { requiresAuth: true, titleKey: 'pageTitles.familyDiscount' },
      },
      {
         path: '/products/:id',
         name: 'product-detail',
         component: ProductDetailPage,
         meta: { requiresAuth: true, titleKey: 'pageTitles.productDetail' },
      },
      {
         path: '/vendors',
         name: 'vendors',
         component: VendorPage,
         meta: { requiresAuth: true, titleKey: 'pageTitles.vendors' },
      },
      {
         path: '/vendors/new',
         name: 'vendor-new',
         component: VendorEditPage,
         meta: { requiresAuth: true, titleKey: 'pageTitles.vendorDetail' },
      },
      {
         path: '/vendors/:id',
         name: 'vendor-detail',
         component: VendorEditPage,
         meta: { requiresAuth: true, titleKey: 'pageTitles.vendorDetail' },
      },
      {
         path: '/admin',
         name: 'admin',
         component: AdminPage,
         meta: { requiresAuth: true, titleKey: 'pageTitles.admin' },
      },
      {
         path: '/settings',
         name: 'settings',
         component: SettingsPage,
         meta: { requiresAuth: true, titleKey: 'pageTitles.settings' },
      },
   ],
});

function shouldRedirectRecoveryToResetPage(toPath: string): boolean {
   if (typeof window === 'undefined' || toPath === '/reset-password') {
      return false;
   }

   const rawHash = window.location.hash.startsWith('#')
      ? window.location.hash.slice(1)
      : window.location.hash;

   if (!rawHash) {
      return false;
   }

   const hashParams = new URLSearchParams(rawHash);
   const authType = hashParams.get('type');
   const hasRecoveryToken = hashParams.has('access_token') || hashParams.has('token_hash');
   const hasRecoveryError = hashParams.has('error_code') && hashParams.has('error_description');

   return (authType === 'recovery' && hasRecoveryToken) || hasRecoveryError;
}

// Navigation guard for authentication
router.beforeEach(async (to, _from, next) => {
   if (shouldRedirectRecoveryToResetPage(to.path)) {
      next({ path: '/reset-password', hash: window.location.hash });
      return;
   }

   const authStore = useAuth();

   // Only wait for auth initialization on protected routes
   // For guest routes (login), skip the wait to show the page quickly
   if (to.meta.requiresAuth && authStore.loading.value) {
      await new Promise<void>((resolve) => {
         const timeout = setTimeout(() => {
            clearInterval(checkLoading);
            resolve();
         }, 3000); // 3 second timeout (reduced from 5)

         const checkLoading = setInterval(() => {
            if (!authStore.loading.value) {
               clearInterval(checkLoading);
               clearTimeout(timeout);
               resolve();
            }
         }, 50);
      });
   }

   // Refresh session on navigation to ensure it's still valid (with timeout)
   // Disabled: Session refresh was causing AbortError on page loads
   // Supabase client handles session validation automatically
   if (false && to.meta.requiresAuth && authStore.session.value) {
      try {
         const { supabase } = await import('../lib/supabase');

         // Add timeout to prevent hanging navigation (increased to 5 seconds)
         const sessionPromise = supabase.auth.getSession();
         const timeoutPromise = new Promise<null>(
            (resolve) => setTimeout(() => resolve(null), 5000) // 5 second timeout
         );

         type SessionResponse = { data: { session: unknown | null }; error: unknown | null };

         const result = (await Promise.race([
            sessionPromise,
            timeoutPromise,
         ])) as SessionResponse | null;

         if (!result) {
            console.warn('[Router] Session check timed out, allowing navigation to continue');
         } else {
            const sessionResult = result as SessionResponse;
            if (sessionResult.error || !sessionResult.data.session) {
               console.warn('[Router] Session invalid or expired, redirecting to login');
               next('/login');
               return;
            }
         }
      } catch (err) {
         console.error('[Router] Error refreshing session:', err);
         // Continue navigation even on error to prevent getting stuck
      }
   }

   if (to.meta.requiresAuth && !authStore.isAuthenticated.value) {
      next('/login');
   } else if (to.meta.requiresGuest && authStore.isAuthenticated.value) {
      next('/');
   } else {
      next();
   }
});

router.afterEach((to) => {
   if (typeof document === 'undefined') {
      return;
   }

   const i18nGlobal = (i18n as any).global;
   const baseTitle = i18nGlobal.t('pageTitles.app');
   const titleKey = to.meta.titleKey as string | undefined;
   const titleParams =
      typeof to.meta.titleParams === 'function' ? (to.meta.titleParams as any)(to) : undefined;
   const metaTitle = titleKey ? i18nGlobal.t(titleKey, titleParams as any) : undefined;
   const titleParts: string[] = [];

   if (metaTitle && typeof metaTitle === 'string') {
      titleParts.push(metaTitle);
   }

   const idValue = to.params?.id;
   if (idValue !== undefined && idValue !== null && String(idValue).trim() !== '') {
      titleParts.push(String(idValue));
   }

   titleParts.push(baseTitle);
   document.title = titleParts.join(' - ');
});

export default router;
