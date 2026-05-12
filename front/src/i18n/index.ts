import { createI18n } from 'vue-i18n';
import en from './locales/en';
import fr from './locales/fr';

export type MessageSchema = typeof en;

const LOCALE_STORAGE_KEY = 'user-locale';

// Get saved locale from localStorage or default to 'fr'
const savedLocale = localStorage.getItem(LOCALE_STORAGE_KEY) as 'en' | 'fr' | null;
const initialLocale = savedLocale || 'fr';

const i18n = createI18n<[MessageSchema], 'en' | 'fr'>({
   legacy: false,
   locale: initialLocale,
   fallbackLocale: 'en',
   messages: {
      en,
      fr,
   },
});

export { LOCALE_STORAGE_KEY };
export default i18n;
