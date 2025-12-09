<template>
  <div class="admin-dashboard">
    <header class="admin-dashboard__header">
      <h1 class="admin-dashboard__title">Admin Dashboard</h1>
      <router-link to="/dashboard" class="admin-dashboard__back">Back</router-link>
    </header>
    <main class="admin-dashboard__content">
      <div class="admin-dashboard__section">
        <h2>Generate Timetable</h2>
        <form @submit.prevent="generateTimetable" class="admin-dashboard__form">
          <input
            v-model="timetableName"
            type="text"
            placeholder="Timetable name"
            class="admin-dashboard__input"
            required
          />
          <button type="submit" class="admin-dashboard__button" :disabled="loading">
            {{ loading ? 'Generating...' : 'Generate Timetable' }}
          </button>
        </form>
        <div v-if="error" class="admin-dashboard__error">{{ error }}</div>
        <div v-if="success" class="admin-dashboard__success">{{ success }}</div>
      </div>
      <div v-if="validationResult" class="admin-dashboard__section">
        <h2>Validation Results</h2>
        <div v-if="validationResult.is_valid" class="admin-dashboard__valid">
          Timetable is valid!
        </div>
        <div v-else>
          <div class="admin-dashboard__errors">
            <div
              v-for="(err, index) in validationResult.errors"
              :key="index"
              class="admin-dashboard__error-item"
            >
              {{ err.message }}
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import api from '@/services/api'

const authStore = useAuthStore()
const timetableName = ref('')
const loading = ref(false)
const error = ref('')
const success = ref('')
const validationResult = ref<any>(null)

async function generateTimetable() {
  loading.value = true
  error.value = ''
  success.value = ''
  try {
    const schoolId = authStore.user?.school_id
    if (!schoolId) {
      throw new Error('School ID not found')
    }
    const response = await api.post(`/timetables/schools/${schoolId}/timetables/generate`, {
      name: timetableName.value
    })
    success.value = 'Timetable generated successfully!'
    
    // Validate the generated timetable
    if (response.data.id) {
      const validation = await api.post(
        `/timetables/schools/${schoolId}/timetables/${response.data.id}/validate`
      )
      validationResult.value = validation.data
    }
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to generate timetable'
  } finally {
    loading.value = false
  }
}
</script>

<style lang="scss" scoped>
@import '../styles/neo.scss';

.admin-dashboard {
  min-height: 100vh;
  background: transparent;

  &__header {
    @extend %neo-header;
    padding: 1.5rem 2rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    position: sticky;
    top: 0;
    z-index: 100;
  }

  &__title {
    color: $neo-text;
    font-size: 1.75rem;
    font-weight: 700;
    margin: 0;
  }

  &__back {
    @extend %neo-button;
    @extend %neo-button--secondary;
    padding: 0.75rem 1.5rem;
    text-decoration: none;
    border-radius: 12px;
    font-weight: 500;
  }

  &__content {
    padding: 2rem;
    max-width: 1200px;
    margin: 0 auto;
    position: relative;
    z-index: 1;
  }

  &__section {
    @extend %neo-panel;
    padding: 2rem;
    margin-bottom: 2rem;

    h2 {
      margin-bottom: 1rem;
      color: $neo-text;
      font-weight: 700;
    }
  }

  &__form {
    display: flex;
    gap: 1rem;
    margin-bottom: 1rem;
  }

  &__input {
    @extend %neo-input;
    flex: 1;
    padding: 0.75rem;
    font-size: 1rem;
  }

  &__button {
    @extend %neo-button;
    @extend %neo-button--primary;
    padding: 0.75rem 2rem;
    cursor: pointer;
    font-size: 1rem;
    font-weight: 600;

    &:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
  }

  &__error {
    @extend %neo-message;
    @extend %neo-message--error;
    margin-top: 1rem;
    padding: 0.75rem;
    border-radius: 12px;
  }

  &__success {
    @extend %neo-message;
    @extend %neo-message--success;
    margin-top: 1rem;
    padding: 0.75rem;
    border-radius: 12px;
  }

  &__valid {
    @extend %neo-message;
    @extend %neo-message--success;
    font-weight: 600;
    padding: 1rem;
    border-radius: 12px;
  }

  &__errors {
    margin-top: 1rem;
  }

  &__error-item {
    @extend %neo-message;
    @extend %neo-message--error;
    padding: 0.75rem;
    border-radius: 12px;
    margin-bottom: 0.5rem;
  }
}
</style>

