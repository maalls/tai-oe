import fs from 'fs';
import path from 'path';
import { defineConfig, loadEnv } from 'vite';
import vue from '@vitejs/plugin-vue';

function parseEnvFile(filePath: string): Record<string, string> {
   if (!fs.existsSync(filePath)) {
      return {};
   }

   const content = fs.readFileSync(filePath, 'utf-8');
   const out: Record<string, string> = {};

   for (const line of content.split(/\r?\n/)) {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith('#')) {
         continue;
      }
      const idx = trimmed.indexOf('=');
      if (idx <= 0) {
         continue;
      }
      const key = trimmed.slice(0, idx).trim();
      let value = trimmed.slice(idx + 1).trim();
      if (
         (value.startsWith('"') && value.endsWith('"')) ||
         (value.startsWith("'") && value.endsWith("'"))
      ) {
         value = value.slice(1, -1);
      }
      out[key] = value;
   }

   return out;
}

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
   const localEnv = loadEnv(mode, process.cwd(), '');
   const apiUrl = localEnv.VITE_API_URL || process.env.VITE_API_URL || 'http://127.0.0.1:8088';
   
   // Determine proxy target: if apiUrl is relative path (like /api), use localhost:8080, otherwise use apiUrl
   const apiProxyTarget = apiUrl.startsWith('http') ? apiUrl : 'http://localhost:8080';
   
   const sharedEnvRel = localEnv.SUPABASE_ENV_FILE || '../supabase/.env.prod';
   const sharedEnvPath = path.isAbsolute(sharedEnvRel)
      ? sharedEnvRel
      : path.resolve(process.cwd(), sharedEnvRel);
   const sharedEnv = parseEnvFile(sharedEnvPath);

   const sharedUrl =
      sharedEnv.SUPABASE_PUBLIC_URL || sharedEnv.API_EXTERNAL_URL || sharedEnv.SITE_URL || '';

   const viteSupabaseUrl = localEnv.VITE_SUPABASE_URL || process.env.VITE_SUPABASE_URL || sharedUrl;
   const viteSupabaseAnon =
      localEnv.VITE_SUPABASE_ANON_KEY ||
      process.env.VITE_SUPABASE_ANON_KEY ||
      sharedEnv.ANON_KEY ||
      '';

   if (viteSupabaseUrl) {
      process.env.VITE_SUPABASE_URL = viteSupabaseUrl;
   }
   if (viteSupabaseAnon) {
      process.env.VITE_SUPABASE_ANON_KEY = viteSupabaseAnon;
   }

   return {
      define: {
         'import.meta.env.VITE_SUPABASE_URL': JSON.stringify(viteSupabaseUrl),
         'import.meta.env.VITE_SUPABASE_ANON_KEY': JSON.stringify(viteSupabaseAnon),
      },
      plugins: [vue()],
      server: {
         middlewareMode: false,
         allowedHosts: ['gme.ai-oe.co', 'localhost', '127.0.0.1'],
         proxy: {
            '/api': {
               target: apiProxyTarget,
               changeOrigin: true,
            },
         },
      },
      preview: {
         host: '0.0.0.0',
         port: 5173,
         allowedHosts: ['gme.ai-oe.co', 'localhost', '127.0.0.1'],
         proxy: {
            '/api': {
               target: apiProxyTarget,
               changeOrigin: true,
            },
         },
      },
   };
});
