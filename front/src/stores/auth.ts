import { ref, computed } from 'vue';
import { supabase } from '../lib/supabase';
import type { User, Session } from '@supabase/supabase-js';

const user = ref<User | null>(null);
const session = ref<Session | null>(null);
const loading = ref(true);

export function useAuth() {
   const isAuthenticated = computed(() => !!user.value);

   async function ensureProfileExists() {
      if (!user.value) return;

      try {
         // Check if profile exists
         const { data: existingProfile, error: fetchError } = await supabase
            .from('profile')
            .select('id')
            .eq('id', user.value.id)
            .maybeSingle();

         if (fetchError) {
            console.error('[Auth] Error checking profile:', fetchError);
            return;
         }

         // Profile doesn't exist, create one
         if (!existingProfile) {
            const { error: insertError } = await (supabase.from('profile') as any).insert({
               id: user.value.id,
               email: user.value.email,
               full_name: user.value.user_metadata?.full_name || '',
            });

            if (insertError) {
               console.error('[Auth] Error creating profile:', insertError);
            } else {
               console.log('[Auth] Profile created successfully for:', user.value.email);
            }
         } else {
            console.log('[Auth] Profile already exists for:', user.value.email);
         }
      } catch (error) {
         console.error('[Auth] Unexpected error in ensureProfileExists:', error);
      }
   }

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

      // Ensure profile exists
      if (data.user) {
         await ensureProfileExists();
      }

      return data;
   }

   async function signOut() {
      const { error } = await supabase.auth.signOut();
      if (error) throw error;
      user.value = null;
      session.value = null;
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
      // Get current session - this will refresh if needed
      const {
         data: { session: currentSession },
      } = await supabase.auth.getSession();
      if (currentSession?.access_token) {
         session.value = currentSession;
         user.value = currentSession.user ?? null;
         return currentSession.access_token;
      }
      throw new Error('No valid authentication token');
   }

   return {
      user: computed(() => user.value),
      session: computed(() => session.value),
      isAuthenticated,
      loading: computed(() => loading.value),
      signUp,
      signIn,
      signOut,
      initialize,
      getValidToken,
   };
}
