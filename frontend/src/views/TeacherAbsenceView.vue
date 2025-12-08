<template>
  <div class="teacher-absence-view">
    <header class="teacher-absence-view__header">
      <h1 class="teacher-absence-view__title">Report Absence</h1>
      <router-link to="/dashboard" class="teacher-absence-view__back">Back</router-link>
    </header>
    <main class="teacher-absence-view__content">
      <div class="teacher-absence-view__section">
        <h2>Report New Absence</h2>
        <form @submit.prevent="reportAbsence" class="teacher-absence-view__form">
          <input
            v-model="newAbsence.date_from"
            type="date"
            class="teacher-absence-view__input"
            required
          />
          <input
            v-model="newAbsence.date_to"
            type="date"
            class="teacher-absence-view__input"
            required
          />
          <textarea
            v-model="newAbsence.reason"
            placeholder="Reason (optional)"
            class="teacher-absence-view__textarea"
            rows="3"
          ></textarea>
          <button type="submit" class="teacher-absence-view__button" :disabled="loading">
            Report Absence
          </button>
        </form>
      </div>

      <div class="teacher-absence-view__section">
        <h2>My Absences</h2>
        <div v-if="absences.length > 0" class="teacher-absence-view__list">
          <div
            v-for="absence in absences"
            :key="absence.id"
            class="teacher-absence-view__item"
          >
            <div class="teacher-absence-view__item-info">
              <span class="teacher-absence-view__item-dates">
                {{ formatDate(absence.date_from) }} - {{ formatDate(absence.date_to) }}
              </span>
              <span v-if="absence.reason" class="teacher-absence-view__item-reason">
                {{ absence.reason }}
              </span>
            </div>
          </div>
        </div>
        <div v-else class="teacher-absence-view__empty">No absences reported</div>
      </div>

      <div v-if="error" class="teacher-absence-view__error">{{ error }}</div>
      <div v-if="success" class="teacher-absence-view__success">{{ success }}</div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import api from '@/services/api'

interface Absence {
  id: number
  teacher_id: number
  date_from: string
  date_to: string
  reason: string | null
  school_id: number
}

const authStore = useAuthStore()
const absences = ref<Absence[]>([])
const loading = ref(false)
const error = ref('')
const success = ref('')

const newAbsence = ref({
  date_from: '',
  date_to: '',
  reason: ''
})

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString()
}

async function loadAbsences() {
  try {
    const schoolId = authStore.user?.school_id
    const teacherId = authStore.user?.teacher_id
    if (!schoolId || !teacherId) return
    
    const response = await api.get(`/absences/schools/${schoolId}/absences?teacher_id=${teacherId}`)
    absences.value = response.data
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to load absences'
  }
}

async function reportAbsence() {
  loading.value = true
  error.value = ''
  success.value = ''
  
  try {
    const schoolId = authStore.user?.school_id
    const teacherId = authStore.user?.teacher_id
    if (!schoolId || !teacherId) {
      throw new Error('School ID or Teacher ID not found')
    }
    
    const absenceData = {
      teacher_id: teacherId,
      date_from: newAbsence.value.date_from,
      date_to: newAbsence.value.date_to,
      reason: newAbsence.value.reason || null
    }
    
    await api.post(`/absences/schools/${schoolId}/absences`, absenceData)
    success.value = 'Absence reported successfully'
    newAbsence.value = { date_from: '', date_to: '', reason: '' }
    await loadAbsences()
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to report absence'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadAbsences()
})
</script>

<style lang="scss" scoped>
.teacher-absence-view {
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
    flex-direction: column;
    gap: 1rem;
  }

  &__input {
    padding: 0.75rem;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 1rem;

    &:focus {
      outline: none;
      border-color: #4a90e2;
    }
  }

  &__textarea {
    padding: 0.75rem;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 1rem;
    font-family: inherit;
    resize: vertical;

    &:focus {
      outline: none;
      border-color: #4a90e2;
    }
  }

  &__button {
    padding: 0.75rem 2rem;
    background-color: #4a90e2;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 1rem;
    align-self: flex-start;

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
    gap: 0.5rem;
  }

  &__item {
    padding: 1rem;
    background-color: #f8f9fa;
    border-radius: 4px;
    border: 1px solid #dee2e6;

    &-info {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }

    &-dates {
      font-weight: 600;
      color: #333;
    }

    &-reason {
      color: #666;
      font-size: 0.875rem;
    }
  }

  &__empty {
    padding: 2rem;
    text-align: center;
    color: #666;
    font-style: italic;
  }

  &__error {
    color: #dc3545;
    padding: 1rem;
    background-color: #f8d7da;
    border-radius: 4px;
    margin-top: 1rem;
  }

  &__success {
    color: #28a745;
    padding: 1rem;
    background-color: #d4edda;
    border-radius: 4px;
    margin-top: 1rem;
  }
}
</style>

