import { computed } from 'vue'
import { useI18nStore } from '@/stores/i18n'

/**
 * Composable for easy access to translations
 * Usage: const { t, currentLanguage, setLanguage } = useI18n()
 */
export function useI18n() {
  const i18nStore = useI18nStore()

  return {
    t: computed(() => i18nStore.t),
    currentLanguage: computed(() => i18nStore.currentLanguage),
    setLanguage: i18nStore.setLanguage,
    getCurrentLanguage: i18nStore.getCurrentLanguage
  }
}

