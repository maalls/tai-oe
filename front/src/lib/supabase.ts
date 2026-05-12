/**
 * Supabase client for frontend authentication and data operations.
 * Singleton instance to avoid multiple GoTrueClient warnings.
 */
import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || 'http://localhost:8003';
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || '';

function getStorageKey(url: string): string {
   try {
      const host = new URL(url).host.replace(/[^a-zA-Z0-9]/g, '_');
      return `rag-supabase-auth-${host}`;
   } catch {
      return 'rag-supabase-auth';
   }
}

if (!supabaseAnonKey) {
   console.warn('VITE_SUPABASE_ANON_KEY is not set in environment variables');
}

// Singleton pattern to ensure only one Supabase client instance exists
let supabaseInstance: ReturnType<typeof createClient> | null = null;

function getSupabaseClient() {
   if (!supabaseInstance) {
      supabaseInstance = createClient(supabaseUrl, supabaseAnonKey, {
         auth: {
            persistSession: true,
            autoRefreshToken: true,
            // Keep sessions separate for local/prod Supabase endpoints.
            storageKey: getStorageKey(supabaseUrl),
            storage: window.localStorage, // Explicit storage (faster than default)
            detectSessionInUrl: true,
            flowType: 'implicit', // Simpler auth flow
         },
         global: {
            headers: {
               'X-Client-Info': 'rag-client',
            },
         },
      });
   }
   return supabaseInstance;
}

export const supabase = getSupabaseClient();
