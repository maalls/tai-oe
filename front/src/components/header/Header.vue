<template>
   <header class="bg-black shadow-lg sticky top-0 z-50">
      <nav class="flex gap-2 px-6 py-4 items-center">
         <RouterLink to="/chat" class="flex items-center gap-3 mr-6" title="Chat">
            <img src="../../assets/logo-white.png" alt="Acme Logo" class="h-8 w-8" />
            <span class="text-xl font-semibold text-white">Acme</span>
         </RouterLink>
         <router-link
            v-for="page in pages"
            :key="page.path"
            :to="page.path"
            class="px-4 py-2 rounded-lg font-medium transition-all duration-200 text-gray-300 hover:bg-slate-800 hover:text-white"
            :class="isRouteActive(page.path) ? 'bg-blue-600! text-white!' : ''"
         >
            {{ t(page.labelKey) }}
         </router-link>
         <div class="ml-auto flex items-center gap-4">
            <span v-if="user" class="text-gray-300 text-sm">{{ user.email }}</span>
            <RouterLink
               to="/settings"
               class="text-gray-300 hover:text-white transition"
               :title="t('nav.settings')"
            >
               <svg
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke-width="1.5"
                  stroke="currentColor"
                  class="w-6 h-6"
               >
                  <path
                     stroke-linecap="round"
                     stroke-linejoin="round"
                     d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.324.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 011.37.49l1.296 2.247a1.125 1.125 0 01-.26 1.431l-1.003.827c-.293.24-.438.613-.431.992a6.759 6.759 0 010 .255c-.007.378.138.75.43.99l1.005.828c.424.35.534.954.26 1.43l-1.298 2.247a1.125 1.125 0 01-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.57 6.57 0 01-.22.128c-.331.183-.581.495-.644.869l-.213 1.28c-.09.543-.56.941-1.11.941h-2.594c-.55 0-1.02-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 01-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 01-1.369-.49l-1.297-2.247a1.125 1.125 0 01.26-1.431l1.004-.827c.292-.24.437-.613.43-.992a6.932 6.932 0 010-.255c.007-.378-.138-.75-.43-.99l-1.004-.828a1.125 1.125 0 01-.26-1.43l1.297-2.247a1.125 1.125 0 011.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.087.22-.128.332-.183.582-.495.644-.869l.214-1.281z"
                  />
                  <path
                     stroke-linecap="round"
                     stroke-linejoin="round"
                     d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                  />
               </svg>
            </RouterLink>
         </div>
      </nav>
   </header>
   <div>
      <div
         style="
            position: absolute;
            top: 70px;
            height: 30px;
            width: 100%;
            text-align: center;
            font-weight: bold;
            font-size: 12px;
            z-index: 30000;
         "
         v-if="message != null"
         :class="[
            message.type == 'error' ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700',
         ]"
         class="p-2"
      >
         {{ message.content }}
      </div>
   </div>
   <!--div v-if="errorMessage" class="mb-4 p-4 bg-red-100 text-red-700 rounded-lg">
      {{ errorMessage }}
   </div>

   <div v-if="successMessage" class="mb-4 p-4 bg-green-100 text-green-700 rounded-lg">
      {{ successMessage }}
   </div-->
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router';
import { useAuth } from '../../stores/auth';
import { useI18n } from '../../i18n/useI18n';
import { ref, onMounted, onBeforeUnmount } from 'vue';

const route = useRoute();
const { user } = useAuth();
const { t } = useI18n();

type HeaderMessage = {
   type: string;
   content: string;
};

const message = ref<HeaderMessage | null>(null);
let clearMessageTimeout: ReturnType<typeof window.setTimeout> | null = null;

const pages = [
   { path: '/mail', labelKey: 'nav.mail' },
   //{ path: '/business', labelKey: 'nav.business' },
   { path: '/opportunities', labelKey: 'nav.opportunities' },
   { path: '/client', labelKey: 'nav.client' },
   { path: '/vendors', labelKey: 'nav.vendors' },
   { path: '/admin', labelKey: 'nav.admin' },
];

onMounted(() => {
   window.addEventListener('header-notification', onHeaderNotification);
});
onBeforeUnmount(() => {
   if (clearMessageTimeout) {
      window.clearTimeout(clearMessageTimeout);
   }
   window.removeEventListener('header-notification', onHeaderNotification);
});

function scheduleMessageClear() {
   if (clearMessageTimeout) {
      window.clearTimeout(clearMessageTimeout);
   }

   clearMessageTimeout = window.setTimeout(() => {
      message.value = null;
      clearMessageTimeout = null;
   }, 3000);
}

function onHeaderNotification(event: any) {
   // handle event.detail or event payload
   message.value = event.detail;
   scheduleMessageClear();
}

const isRouteActive = (pagePath: string) => {
   if (route.path === pagePath || route.path.startsWith(pagePath + '/')) {
      return true;
   }

   if (pagePath === '/vendors' && route.path.startsWith('/products')) {
      return true;
   }

   if (
      pagePath === '/client' &&
      (route.path.startsWith('/contacts') || route.path.startsWith('/accounts'))
   ) {
      return true;
   }

   return false;
};
</script>
