import { ref, computed } from 'vue';
import { supabase } from '../lib/supabase';
import { fetchProfile, updateProfile } from '../api/profile';
import type { User, Session } from '@supabase/supabase-js';

const user = ref<User | null>(null);
const session = ref<Session | null>(null);
const loading = ref(true);

async function clearInvalidSession() {
   user.value = null;
   session.value = null;
   try {
      await supabase.auth.signOut();
   } catch {
      // Best effort cleanup only.
   }
}

export function useAuth() {
   const isAuthenticated = computed(() => !!user.value);

   async function signUp(email: string, password: string) {
      const { data, error } = await supabase.auth.signUp({
         email,
         password,
      });
      if (error) throw error;
      return data;
   }

   async function signIn(email: string, password: string) {
      const { data, error } = await supabase.auth.signInWithPassword({
         email,
         password,
      });
      if (error) throw error;
      user.value = data.user;
      session.value = data.session;
      // Optionnel: fetch profile côté backend si besoin
      return data;
   }

   async function signOut() {
      const { error } = await supabase.auth.signOut();
      if (error) throw error;
      user.value = null;
      session.value = null;
   }

   async function updateDisplayName(displayName: string) {
      if (!user.value) throw new Error('No authenticated user');
      const fullName = displayName.trim();
      // Met à jour le nom côté auth (supabase)
      const currentMetadata = (user.value.user_metadata || {}) as Record<string, any>;
      const { data, error } = await supabase.auth.updateUser({
         data: {
            ...currentMetadata,
            full_name: fullName,
         },
      });
      if (error) throw error;
      if (data?.user) {
         user.value = data.user;
         if (session.value) {
            session.value = {
               ...session.value,
               user: data.user,
            };
         }
      }
      // Met à jour le profil côté backend
      const token = await getValidToken();
      await updateProfile(token, { full_name: fullName });
   }

   async function initialize() {
      try {
         loading.value = true;
         //console.log('[Auth] Initializing authentication state');
         const {
            data: { session: currentSession },
         } = await supabase.auth.getSession();
         session.value = currentSession;
         user.value = currentSession?.user ?? null;
         //console.log('[Auth] Current session:', currentSession);

         // Set up auth state change listener to refresh session
         supabase.auth.onAuthStateChange(async (_event, newSession) => {
            //console.log('[Auth] Auth state changed:', event);
            session.value = newSession;
            user.value = newSession?.user ?? null;
         });
      } catch (error) {
         console.error('[Auth] Error fetching initial session:::', error);
         throw error;
      } finally {
         loading.value = false;
      }

      return;
   }

   async function getValidToken(): Promise<string> {
      // Resolve current session and proactively refresh if token is missing/near expiry.
      const {
         data: { session: currentSession },
      } = await supabase.auth.getSession();

      let effectiveSession = currentSession;
      const nowSeconds = Math.floor(Date.now() / 1000);
      const expiresAt = currentSession?.expires_at ?? 0;
      const shouldRefresh = !currentSession?.access_token || expiresAt <= nowSeconds + 60;

      if (shouldRefresh) {
         const { data: refreshed, error } = await supabase.auth.refreshSession();
         if (error) {
            await clearInvalidSession();
            throw new Error('Session expired, please sign in again');
         }
         effectiveSession = refreshed.session;
      }

      if (effectiveSession?.access_token) {
         // Important: a token can still be unexpired but revoked (session_not_found).
         // Verify with auth service and attempt one refresh fallback when invalid.
         const { error: verifyError } = await supabase.auth.getUser(effectiveSession.access_token);
         if (verifyError) {
            const { data: refreshed, error: refreshError } = await supabase.auth.refreshSession();
            if (refreshError || !refreshed.session?.access_token) {
               await clearInvalidSession();
               throw new Error('Session expired, please sign in again');
            }

            const { error: verifyRefreshedError } = await supabase.auth.getUser(
               refreshed.session.access_token
            );
            if (verifyRefreshedError) {
               await clearInvalidSession();
               throw new Error('Session expired, please sign in again');
            }

            session.value = refreshed.session;
            user.value = refreshed.session.user ?? null;
            return refreshed.session.access_token;
         }

         session.value = effectiveSession;
         user.value = effectiveSession.user ?? null;
         return effectiveSession.access_token;
      }

      await clearInvalidSession();
      throw new Error('Session expired, please sign in again');
   }

   return {
      user: computed(() => user.value),
      session: computed(() => session.value),
      isAuthenticated,
      loading: computed(() => loading.value),
      signUp,
      signIn,
      signOut,
      updateDisplayName,
      initialize,
      getValidToken,
   };
}
