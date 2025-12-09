<template>
  <div class="language-switcher">
    <button
      v-for="lang in languages"
      :key="lang.code"
      @click="switchLanguage(lang.code)"
      :class="[
        'language-switcher__button',
        { 'language-switcher__button--active': i18nStore.currentLanguage === lang.code }
      ]"
      :title="lang.name"
    >
      {{ lang.flag }} {{ lang.code.toUpperCase() }}
    </button>
  </div>
</template>

<script setup lang="ts">
import { useI18nStore, Language } from '@/stores/i18n'

const i18nStore = useI18nStore()

const languages = [
  { code: 'en' as Language, name: 'English', flag: '🇬🇧' },
  { code: 'cs' as Language, name: 'Čeština', flag: '🇨🇿' }
]

function switchLanguage(lang: Language) {
  i18nStore.setLanguage(lang)
}
</script>

<style lang="scss" scoped>
@import '../styles/neo.scss';

.language-switcher {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.language-switcher__button {
  @extend %neo-button;
  @extend %neo-button--secondary;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  min-width: 60px;

  &:hover {
    @include neo-surface(8px, 1.2);
  }

  &--active {
    @include neo-inset(8px, 0.6);
    background: $neo-bg-light;
    font-weight: 700;
  }
}
</style>

