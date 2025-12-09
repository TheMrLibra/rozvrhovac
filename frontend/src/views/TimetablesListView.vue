<template>
  <div class="timetables-list-view">
    <header class="timetables-list-view__header">
      <h1 class="timetables-list-view__title">Timetables</h1>
      <div class="timetables-list-view__controls">
        <button
          @click="showGenerateForm = !showGenerateForm"
          class="timetables-list-view__button"
        >
          Generate New Timetable
        </button>
        <router-link to="/dashboard" class="timetables-list-view__back">Back</router-link>
      </div>
    </header>
    <main class="timetables-list-view__content">
      <!-- Generate Form -->
      <div v-if="showGenerateForm" class="timetables-list-view__section">
        <h2>Generate New Timetable</h2>
        <form @submit.prevent="generateTimetable" class="timetables-list-view__form">
          <input
            v-model="timetableName"
            type="text"
            placeholder="Timetable name (e.g., Spring 2025)"
            class="timetables-list-view__input"
            required
          />
          <button type="submit" class="timetables-list-view__button" :disabled="loading">
            {{ loading ? 'Generating...' : 'Generate' }}
          </button>
        </form>
        <div v-if="error" class="timetables-list-view__error">{{ error }}</div>
        <div v-if="success" class="timetables-list-view__success">{{ success }}</div>
      </div>

      <!-- Timetables List -->
      <div class="timetables-list-view__section">
        <h2>All Timetables</h2>
        <div v-if="loading" class="timetables-list-view__loading">Loading timetables...</div>
        <div v-else-if="timetables.length > 0" class="timetables-list-view__list">
          <div
            v-for="timetable in timetables"
            :key="timetable.id"
            class="timetables-list-view__item"
          >
            <div class="timetables-list-view__item-info">
              <h3 class="timetables-list-view__item-name">{{ timetable.name }}</h3>
              <div class="timetables-list-view__item-details">
                <span v-if="timetable.valid_from || timetable.valid_to">
                  Valid: 
                  {{ timetable.valid_from ? formatDate(timetable.valid_from) : 'N/A' }} - 
                  {{ timetable.valid_to ? formatDate(timetable.valid_to) : 'N/A' }}
                </span>
                <span v-else>No validity period set</span>
              </div>
              <div class="timetables-list-view__item-stats">
                <span>{{ timetable.entries?.length || 0 }} entries</span>
              </div>
            </div>
            <div class="timetables-list-view__item-actions">
              <button
                @click="viewTimetable(timetable.id)"
                class="timetables-list-view__view"
                :disabled="loading"
              >
                View
              </button>
              <button
                @click="validateTimetable(timetable.id)"
                class="timetables-list-view__validate"
                :disabled="loading"
              >
                Validate
              </button>
              <button
                @click="deleteTimetable(timetable.id)"
                class="timetables-list-view__delete"
                :disabled="loading"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
        <div v-else class="timetables-list-view__empty">
          No timetables found. Generate one to get started.
        </div>
      </div>

      <!-- Validation Results -->
      <div v-if="validationResult" class="timetables-list-view__section">
        <h2>Validation Results</h2>
        <div v-if="validationResult.is_valid" class="timetables-list-view__valid">
          ✓ Timetable is valid!
        </div>
        <div v-else>
          <div class="timetables-list-view__errors">
            <div
              v-for="(err, index) in validationResult.errors"
              :key="index"
              class="timetables-list-view__error-item"
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
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import api from '@/services/api'

interface Timetable {
  id: number
  name: string
  valid_from: string | null
  valid_to: string | null
  entries?: any[]
}

const router = useRouter()
const authStore = useAuthStore()
const timetables = ref<Timetable[]>([])
const loading = ref(false)
const error = ref('')
const success = ref('')
const showGenerateForm = ref(false)
const timetableName = ref('')
const validationResult = ref<any>(null)

function formatDate(dateString: string): string {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  return date.toLocaleDateString()
}

async function loadTimetables() {
  loading.value = true
  error.value = ''
  try {
    const schoolId = authStore.user?.school_id
    if (schoolId) {
      const response = await api.get(`/timetables/schools/${schoolId}/timetables`)
      timetables.value = response.data
    }
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to load timetables'
  } finally {
    loading.value = false
  }
}

async function generateTimetable() {
  loading.value = true
  error.value = ''
  success.value = ''
  validationResult.value = null
  
  try {
    const schoolId = authStore.user?.school_id
    if (!schoolId) {
      throw new Error('School ID not found')
    }
    
    const response = await api.post(`/timetables/schools/${schoolId}/timetables/generate`, {
      name: timetableName.value
    })
    
    success.value = 'Timetable generated successfully!'
    timetableName.value = ''
    showGenerateForm.value = false
    
    // Reload timetables list
    await loadTimetables()
    
    // Auto-validate the generated timetable
    if (response.data.id) {
      await validateTimetable(response.data.id)
    }
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to generate timetable'
  } finally {
    loading.value = false
  }
}

function viewTimetable(timetableId: number) {
  router.push(`/timetable/${timetableId}`)
}

async function validateTimetable(timetableId: number) {
  loading.value = true
  validationResult.value = null
  
  try {
    const schoolId = authStore.user?.school_id
    if (!schoolId) {
      throw new Error('School ID not found')
    }
    
    const response = await api.post(
      `/timetables/schools/${schoolId}/timetables/${timetableId}/validate`
    )
    validationResult.value = response.data
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to validate timetable'
  } finally {
    loading.value = false
  }
}

async function deleteTimetable(timetableId: number) {
  if (!confirm('Are you sure you want to delete this timetable?')) {
    return
  }
  
  loading.value = true
  error.value = ''
  success.value = ''
  
  try {
    const schoolId = authStore.user?.school_id
    if (!schoolId) {
      throw new Error('School ID not found')
    }
    
    await api.delete(`/timetables/schools/${schoolId}/timetables/${timetableId}`)
    success.value = 'Timetable deleted successfully'
    await loadTimetables()
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to delete timetable'
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await loadTimetables()
})
</script>

<style lang="scss" scoped>
.timetables-list-view {
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

  &__controls {
    display: flex;
    gap: 1rem;
    align-items: center;
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

  &__list {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  &__item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1.5rem;
    border: 1px solid #ddd;
    border-radius: 8px;
    background-color: #fafafa;
    transition: box-shadow 0.2s;

    &:hover {
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }
  }

  &__item-info {
    flex: 1;
  }

  &__item-name {
    margin: 0 0 0.5rem 0;
    color: #333;
    font-size: 1.25rem;
  }

  &__item-details {
    color: #666;
    font-size: 0.875rem;
    margin-bottom: 0.5rem;
  }

  &__item-stats {
    color: #999;
    font-size: 0.875rem;
  }

  &__item-actions {
    display: flex;
    gap: 0.5rem;
  }

  &__view {
    padding: 0.5rem 1rem;
    background-color: #4a90e2;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.875rem;

    &:hover:not(:disabled) {
      background-color: #357abd;
    }

    &:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }
  }

  &__validate {
    padding: 0.5rem 1rem;
    background-color: #28a745;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.875rem;

    &:hover:not(:disabled) {
      background-color: #218838;
    }

    &:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }
  }

  &__delete {
    padding: 0.5rem 1rem;
    background-color: #dc3545;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.875rem;

    &:hover:not(:disabled) {
      background-color: #c82333;
    }

    &:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }
  }

  &__loading {
    text-align: center;
    padding: 2rem;
    color: #666;
  }

  &__empty {
    text-align: center;
    padding: 3rem;
    color: #666;
  }

  &__error {
    color: #dc3545;
    margin-top: 1rem;
    padding: 0.75rem;
    background-color: #f8d7da;
    border-radius: 4px;
  }

  &__success {
    color: #28a745;
    margin-top: 1rem;
    padding: 0.75rem;
    background-color: #d4edda;
    border-radius: 4px;
  }

  &__valid {
    color: #28a745;
    font-weight: 600;
    padding: 1rem;
    background-color: #d4edda;
    border-radius: 4px;
  }

  &__errors {
    margin-top: 1rem;
  }

  &__error-item {
    padding: 0.75rem;
    background-color: #f8d7da;
    color: #721c24;
    border-radius: 4px;
    margin-bottom: 0.5rem;
  }
}
</style>

