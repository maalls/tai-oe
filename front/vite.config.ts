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
   const apiUrl = localEnv.VITE_API_URL || process.env.VITE_API_URL;
   if (!apiUrl) {
      throw new Error(
         'Missing required VITE_API_URL. Define it in your .env/.env.local or environment before starting Vite.'
      );
   }

   const apiProxyTargetEnv = localEnv.VITE_API_PROXY_TARGET || process.env.VITE_API_PROXY_TARGET;
   const apiProxyTarget = apiUrl.startsWith('http') ? apiUrl : apiProxyTargetEnv;
   if (!apiProxyTarget) {
      throw new Error(
         'Missing required VITE_API_PROXY_TARGET when VITE_API_URL is relative. Define it in your .env/.env.local or environment.'
      );
   }

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
      build: {
         rollupOptions: {
            output: {
               manualChunks(id) {
                  if (!id.includes('/node_modules/')) {
                     return undefined;
                  }

                  if (id.includes('/pdfjs-dist/') || id.includes('/vue3-pdf-app/')) {
                     return 'vendor-pdf';
                  }

                  if (id.includes('/@supabase/supabase-js/')) {
                     return 'vendor-supabase';
                  }

                  if (id.includes('/marked/') || id.includes('/dompurify/')) {
                     return 'vendor-text';
                  }

                  if (id.includes('/lucide-vue-next/')) {
                     return 'vendor-icons';
                  }

                  if (
                     id.includes('/vue/') ||
                     id.includes('/vue-router/') ||
                     id.includes('/vue-i18n/')
                  ) {
                     return 'vendor-vue';
                  }

                  return 'vendor-misc';
               },
            },
         },
      },
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
