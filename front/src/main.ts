import { createApp } from 'vue';
import './style.css';
import App from './App.vue';
import router from './router';
import i18n from './i18n';
import { useAuth } from './stores/auth';

//console.log('[Main] Starting application initialization');

const requiredApiUrl = import.meta.env.VITE_API_URL;
if (!requiredApiUrl || !requiredApiUrl.trim()) {
   throw new Error('Missing required environment variable: VITE_API_URL');
}

if (import.meta.env.DEV) {
   window.addEventListener('unhandledrejection', (event) => {
      console.group('[Diag] Unhandled Promise Rejection');
      console.error('reason:', event.reason);
      console.error('event:', event);
      console.trace('trace');
      console.groupEnd();
   });

   window.addEventListener('error', (event) => {
      console.group('[Diag] Global Error Event');
      console.error('message:', event.message);
      console.error('filename:', event.filename);
      console.error('lineno:', event.lineno, 'colno:', event.colno);
      console.error('error:', event.error);
      console.groupEnd();
   });
}

const app = createApp(App);

// Initialize auth but don't block on it
// The app will show immediately and auth happens in background
const { initialize } = useAuth();
//console.log('[Main] Calling auth.initialize()');

initialize()
   .catch((err) => {
      console.error('[Main] Failed to initialize auth:', err);
      console.error('[Main] Auth error details:', {
         message: err instanceof Error ? err.message : String(err),
         stack: err instanceof Error ? err.stack : undefined,
      });
   })
   .finally(() => {
      //console.log('[Main] Auth initialization complete (or failed with fallback)');
   });

// Mount app immediately (don't wait for auth)
//console.log('[Main] Mounting Vue app');
app.use(router).use(i18n).mount('#app');
//console.log('[Main] Vue app mounted successfully');
