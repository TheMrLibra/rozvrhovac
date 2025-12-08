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
import { ref, onMounted } from 'vue'
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
.admin-dashboard {
  min-height: 100vh;
  background-color: #f5f5f5;

  &__header {
    background: white;
    padding: 1rem 2rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  }

  &__title {
    color: #333;
  }

  &__back {
    padding: 0.5rem 1rem;
    background-color: #6c757d;
    color: white;
    text-decoration: none;
    border-radius: 4px;

    &:hover {
      background-color: #5a6268;
    }
  }

  &__content {
    padding: 2rem;
    max-width: 1200px;
    margin: 0 auto;
  }

  &__section {
    background: white;
    padding: 2rem;
    border-radius: 8px;
    margin-bottom: 2rem;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);

    h2 {
      margin-bottom: 1rem;
      color: #333;
    }
  }

  &__form {
    display: flex;
    gap: 1rem;
    margin-bottom: 1rem;
  }

  &__input {
    flex: 1;
    padding: 0.75rem;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 1rem;
  }

  &__button {
    padding: 0.75rem 2rem;
    background-color: #4a90e2;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 1rem;

    &:hover:not(:disabled) {
      background-color: #357abd;
    }

    &:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }
  }

  &__error {
    color: #dc3545;
    margin-top: 1rem;
  }

  &__success {
    color: #28a745;
    margin-top: 1rem;
  }

  &__valid {
    color: #28a745;
    font-weight: 600;
  }

  &__errors {
    margin-top: 1rem;
  }

  &__error-item {
    padding: 0.5rem;
    background-color: #f8d7da;
    color: #721c24;
    border-radius: 4px;
    margin-bottom: 0.5rem;
  }
}
</style>

