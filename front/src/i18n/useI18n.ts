import { useI18n as vueUseI18n } from 'vue-i18n';
import type { MessageSchema } from './index';

export function useI18n() {
   return vueUseI18n<{ message: MessageSchema }, 'en' | 'fr'>();
}
