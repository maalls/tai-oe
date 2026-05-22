declare module '*.vue';

interface ImportMetaEnv {
   readonly VITE_API_URL: string;
   readonly VITE_API_USE_PROXY?: string;
}

interface ImportMeta {
   readonly env: ImportMetaEnv;
}
