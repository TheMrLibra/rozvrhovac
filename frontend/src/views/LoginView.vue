<template>
  <div class="login-view">
    <div class="login-view__container">
      <h1 class="login-view__title">Rozvrhovac</h1>
      <form @submit.prevent="handleLogin" class="login-view__form">
        <div class="login-view__field">
          <label class="login-view__label">Email</label>
          <input
            v-model="email"
            type="email"
            required
            class="login-view__input"
            placeholder="your@email.com"
          />
        </div>
        <div class="login-view__field">
          <label class="login-view__label">Password</label>
          <input
            v-model="password"
            type="password"
            required
            class="login-view__input"
            placeholder="Password"
          />
        </div>
        <button type="submit" class="login-view__button" :disabled="loading">
          {{ loading ? 'Logging in...' : 'Login' }}
        </button>
        <div v-if="error" class="login-view__error">{{ error }}</div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

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
    error.value = err.response?.data?.detail || 'Login failed'
  } finally {
    loading.value = false
  }
}
</script>

<style lang="scss" scoped>
@import '../styles/glass.scss';

.login-view {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  position: relative;
  z-index: 1;

  &__container {
    @extend %glass-modal;
    padding: 3rem;
    width: 100%;
    max-width: 400px;
  }

  &__title {
    text-align: center;
    margin-bottom: 2rem;
    color: rgba(255, 255, 255, 0.95);
    font-size: 2rem;
    font-weight: 700;
    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
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
    color: rgba(255, 255, 255, 0.95);
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
  }

  &__input {
    @extend %glass-input;
    padding: 0.875rem;
    border-radius: 12px;
    font-size: 1rem;
  }

  &__button {
    @extend %glass-button;
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
    color: rgba(255, 200, 200, 0.95);
    text-align: center;
    margin-top: 0.5rem;
    padding: 0.75rem;
    background: rgba(220, 53, 69, 0.2);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    border: 1px solid rgba(220, 53, 69, 0.3);
    border-radius: 12px;
  }
}
</style>

