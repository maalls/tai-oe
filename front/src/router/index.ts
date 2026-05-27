import { createRouter, createWebHistory } from 'vue-router';
import { useAuth } from '../stores/auth';
import { resolveAdminAccess } from './guards/adminRole';
import i18n from '../i18n';

const SourcePage = () => import('../components/admin/components/source/IndexPage.vue');
const DatabasePage = () => import('../components/admin/components/database/IndexPage.vue');
const AdminUsersPage = () => import('../components/admin/components/users/IndexPage.vue');
const CartouchesPage = () => import('../components/database/CartouchesPage.vue');
const CommercePage = () => import('../components/database/CommercePage.vue');
const AdminFlowPage = () => import('../components/admin/components/flow/IndexPage.vue');
const ChatPage = () => import('../components/chat/IndexPage.vue');
const MailPage = () => import('../components/mail/IndexPage.vue');
const OpportunityPage = () => import('../components/opportunity/IndexPage.vue');
const OpportunitySourcePage = () =>
   import('../components/opportunity/components/source/SourcePage.vue');
const OpportunityAccountPage = () =>
   import('../components/opportunity/components/account/AccountPage.vue');
const OpportunityQuotePage = () =>
   import('../components/opportunity/components/quote/QuotePage.vue');
const OpportunityPreviewPage = () =>
   import('../components/opportunity/components/preview/PreviewPage.vue');
const OpportunitySendPage = () => import('../components/opportunity/components/send/SendPage.vue');
const OpportunityPipelinePage = () =>
   import('../components/opportunity/components/pipeline/PipelinePage.vue');
const OpportunitySettingsPage = () =>
   import('../components/opportunity/components/settings/SettingsPage.vue');
const OpportunityDocumentsPage = () =>
   import('../components/opportunity/components/documents/DocumentsPage.vue');
const OpportunityDocumentDetailPage = () =>
   import('../components/opportunity/components/documents/DocumentDetailPage.vue');
const OpportunityInvoicesPage = () =>
   import('../components/opportunity/components/invoices/InvoicesPage.vue');
const OpportunityInvoiceDetailPage = () =>
   import('../components/opportunity/components/invoices/InvoiceDetailPage.vue');
const OpportunityActionsPage = () =>
   import('../components/opportunity/components/actions/ActionsPage.vue');
const OpportunityChatPage = () => import('../components/opportunity/components/chat/ChatPage.vue');
const AccountPage = () => import('../components/account/IndexPage.vue');
const AccountEditPage = () => import('../components/account/Edit.vue');
const ContactPage = () => import('../components/contact/IndexPage.vue');
const ContactDetailPage = () => import('../components/contact/DetailPage.vue');
const ClientPage = () => import('../components/client/IndexPage.vue');
const ProductPage = () => import('../components/products/IndexPage.vue');
const ProductDetailPage = () => import('../components/products/DetailPage.vue');
const ProductBrandPage = () => import('../components/products/BrandPage.vue');
const ProductBrandEditPage = () => import('../components/products/BrandEditPage.vue');
const ProductEditPage = () => import('../components/products/edit.vue');
const ProductFamilyPage = () => import('../components/family/index.vue');
const FamilyDiscountPage = () => import('../components/family/show.vue');
const VendorPage = () => import('../components/vendor/index.vue');
const VendorEditPage = () => import('../components/vendor/Edit.vue');
const AdminPage = () => import('../components/admin/IndexPage.vue');
const SettingsPage = () => import('../components/settings/IndexPage.vue');
const LoginPage = () => import('../components/login/IndexPage.vue');
const ResetPasswordPage = () => import('../components/login/ResetPasswordPage.vue');
const AuthTestPage = () => import('../components/debug/AuthTestPage.vue');

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
         path: '/admin/flow',
         name: 'admin-flow',
         component: AdminFlowPage,
         meta: { requiresAuth: true, titleKey: 'pageTitles.adminFlow' },
      },
      {
         path: '/admin/users',
         name: 'admin-users',
         component: AdminUsersPage,
         meta: { requiresAuth: true, requiresAdmin: true, titleKey: 'pageTitles.adminUsers' },
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
      {
         path: '/debug/auth-test',
         name: 'debug-auth-test',
         component: AuthTestPage,
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
   } else if (to.meta.requiresAdmin) {
      const isAdmin = await resolveAdminAccess({
         requiresAdmin: true,
         getValidToken: authStore.getValidToken,
      });
      if (!isAdmin) {
         next('/');
         return;
      }
      next();
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
