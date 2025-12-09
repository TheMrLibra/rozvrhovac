<template>
  <div class="login-view">
    <div class="login-view__language-switcher">
      <LanguageSwitcher />
    </div>
    <div class="login-view__container">
      <h1 class="login-view__title">Rozvrhovac</h1>
      <form @submit.prevent="handleLogin" class="login-view__form">
        <div class="login-view__field">
          <label class="login-view__label">{{ t('login.email') }}</label>
          <input
            v-model="email"
            type="email"
            required
            class="login-view__input"
            :placeholder="t('login.email')"
          />
        </div>
        <div class="login-view__field">
          <label class="login-view__label">{{ t('login.password') }}</label>
          <input
            v-model="password"
            type="password"
            required
            class="login-view__input"
            :placeholder="t('login.password')"
          />
        </div>
        <button type="submit" class="login-view__button" :disabled="loading">
          {{ loading ? t('common.loading') : t('login.loginButton') }}
        </button>
        <div v-if="error" class="login-view__error">{{ t('login.loginError') }}</div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useI18nStore } from '@/stores/i18n'
import LanguageSwitcher from '@/components/LanguageSwitcher.vue'

const router = useRouter()
const authStore = useAuthStore()
const i18nStore = useI18nStore()
const t = i18nStore.t

const email = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

async function handleLogin() {
  loading.value = true
  error.value = ''
  try {
    await authStore.login(email.value, password.value)
    router.push('/dashboard')
  } catch (err: any) {
    error.value = err.response?.data?.detail || t('login.loginError')
  } finally {
    loading.value = false
  }
}
</script>

<style lang="scss" scoped>
@import '../styles/neo.scss';

.login-view {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  position: relative;
  z-index: 1;

  &__language-switcher {
    position: absolute;
    top: 2rem;
    right: 2rem;
  }

  &__container {
    @extend %neo-modal;
    padding: 3rem;
    width: 100%;
    max-width: 400px;
  }

  &__title {
    text-align: center;
    margin-bottom: 2rem;
    color: $neo-text;
    font-size: 2rem;
    font-weight: 700;
  }

  &__form {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  &__field {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  &__label {
    font-weight: 600;
    color: $neo-text;
  }

  &__input {
    @extend %neo-input;
    padding: 0.875rem;
    font-size: 1rem;
  }

  &__button {
    @extend %neo-button;
    @extend %neo-button--primary;
    padding: 0.875rem;
    border-radius: 12px;
    font-size: 1rem;
    font-weight: 600;
    cursor: pointer;
    margin-top: 0.5rem;

    &:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
  }

  &__error {
    @extend %neo-message;
    @extend %neo-message--error;
    text-align: center;
    margin-top: 0.5rem;
    padding: 0.75rem;
    border-radius: 12px;
  }
}
</style>

