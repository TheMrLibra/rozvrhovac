<template>
  <div class="timetables-list-view">
    <header class="timetables-list-view__header">
      <h1 class="timetables-list-view__title">Timetables</h1>
      <div class="timetables-list-view__controls">
        <button
          v-if="authStore.user?.role === 'ADMIN'"
          @click="showGenerateForm = !showGenerateForm"
          class="timetables-list-view__button"
        >
          Generate New Fixed Timetable
        </button>
        <router-link to="/dashboard" class="timetables-list-view__back">Dashboard</router-link>
      </div>
    </header>
    <main class="timetables-list-view__content">
      <!-- Generate Form -->
      <div v-if="showGenerateForm && authStore.user?.role === 'ADMIN'" class="timetables-list-view__section">
        <h2>Generate New Fixed Timetable</h2>
        <form @submit.prevent="generateTimetable" class="timetables-list-view__form">
          <input
            v-model="timetableName"
            type="text"
            placeholder="Timetable name (e.g., Spring 2025)"
            class="timetables-list-view__input"
            required
          />
          <div class="timetables-list-view__form-row">
            <div class="timetables-list-view__form-group">
              <label class="timetables-list-view__label">Valid From</label>
              <input
                v-model="timetableValidFrom"
                type="date"
                class="timetables-list-view__input"
                required
              />
            </div>
            <div class="timetables-list-view__form-group">
              <label class="timetables-list-view__label">Valid To</label>
              <input
                v-model="timetableValidTo"
                type="date"
                class="timetables-list-view__input"
                required
              />
            </div>
          </div>
          <button type="submit" class="timetables-list-view__button" :disabled="loading">
            {{ loading ? 'Generating...' : 'Generate' }}
          </button>
        </form>
      </div>

      <!-- Calendar View -->
      <div class="timetables-list-view__section">
        <h2>Class Timetable Calendar</h2>
        <TimetableCalendar
          :timetables="timetables"
          @date-selected="onDateSelected"
        />
      </div>

      <!-- Fixed (Primary) Timetables -->
      <div class="timetables-list-view__section">
        <h2>Fixed Timetables</h2>
        <div v-if="loading" class="timetables-list-view__loading">Loading timetables...</div>
        <div v-else-if="primaryTimetables.length > 0" class="timetables-list-view__list">
          <div
            v-for="timetable in primaryTimetables"
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
          No fixed timetables found. Generate one to get started.
        </div>
      </div>

      <!-- Substitute Timetables -->
      <div class="timetables-list-view__section">
        <h2>Substitute Timetables</h2>
        <div v-if="loading" class="timetables-list-view__loading">Loading timetables...</div>
        <div v-else-if="substituteTimetables.length > 0" class="timetables-list-view__list">
          <div
            v-for="timetable in substituteTimetables"
            :key="timetable.id"
            class="timetables-list-view__item"
          >
            <div class="timetables-list-view__item-info">
              <h3 class="timetables-list-view__item-name">{{ timetable.name }}</h3>
              <div class="timetables-list-view__item-details">
                <span v-if="timetable.substitute_for_date">
                  For Date: {{ formatDate(timetable.substitute_for_date) }}
                </span>
                <span v-else>No date specified</span>
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
          No substitute timetables found.
        </div>
      </div>

      <!-- Generate Substitute Timetable -->
      <div v-if="authStore.user?.role === 'ADMIN' && primaryTimetables.length > 0" class="timetables-list-view__section">
        <h2>Generate Substitute Timetable</h2>
        <form @submit.prevent="generateSubstituteTimetable" class="timetables-list-view__form">
          <select
            v-model="substituteForm.base_timetable_id"
            class="timetables-list-view__input"
            required
          >
            <option value="">Select Base Timetable</option>
            <option
              v-for="timetable in primaryTimetables"
              :key="timetable.id"
              :value="timetable.id"
            >
              {{ timetable.name }}
            </option>
          </select>
          <input
            v-model="substituteForm.substitute_date"
            type="date"
            class="timetables-list-view__input"
            required
          />
          <button type="submit" class="timetables-list-view__button" :disabled="loading">
            {{ loading ? 'Generating...' : 'Generate Substitute' }}
          </button>
        </form>
      </div>

    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useAlert } from '@/composables/useAlert'
import api from '@/services/api'
import TimetableCalendar from '@/components/TimetableCalendar.vue'

const alert = useAlert()

interface Timetable {
  id: number
  name: string
  valid_from: string | null
  valid_to: string | null
  entries?: any[]
  is_primary?: number
  substitute_for_date?: string | null
  base_timetable_id?: number | null
}

const router = useRouter()
const authStore = useAuthStore()
const timetables = ref<Timetable[]>([])
const loading = ref(false)
const showGenerateForm = ref(false)
const timetableName = ref('')
const timetableValidFrom = ref('')
const timetableValidTo = ref('')
const substituteForm = ref({
  base_timetable_id: null as number | null,
  substitute_date: ''
})

const primaryTimetables = computed(() => {
  return timetables.value.filter(t => t.is_primary === 1)
})

const substituteTimetables = computed(() => {
  return timetables.value.filter(t => t.is_primary === 0)
})

function formatDate(dateString: string): string {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  return date.toLocaleDateString()
}

async function loadTimetables() {
  loading.value = true
  try {
    const schoolId = authStore.user?.school_id
    if (schoolId) {
      const response = await api.get(`/timetables/schools/${schoolId}/timetables`)
      timetables.value = response.data
    }
  } catch (err: any) {
    // Error will be shown via API interceptor
    console.error('Failed to load timetables:', err)
  } finally {
    loading.value = false
  }
}

async function generateTimetable() {
  loading.value = true
  
  try {
    const schoolId = authStore.user?.school_id
    if (!schoolId) {
      throw new Error('School ID not found')
    }
    
    if (!timetableValidFrom.value || !timetableValidTo.value) {
      alert.error('Please select both valid from and valid to dates')
      loading.value = false
      return
    }
    
    if (new Date(timetableValidFrom.value) > new Date(timetableValidTo.value)) {
      alert.error('Valid from date must be before valid to date')
      loading.value = false
      return
    }
    
    const response = await api.post(`/timetables/schools/${schoolId}/timetables/generate`, {
      name: timetableName.value,
      valid_from: timetableValidFrom.value,
      valid_to: timetableValidTo.value
    })
    
    alert.success('Timetable generated successfully!')
    timetableName.value = ''
    timetableValidFrom.value = ''
    timetableValidTo.value = ''
    showGenerateForm.value = false
    
    // Reload timetables list
    await loadTimetables()
    
    // Auto-validate the generated timetable
    if (response.data.id) {
      await validateTimetable(response.data.id)
    }
  } catch (err: any) {
    // Error will be shown via API interceptor, but we can add a custom message if needed
    if (!err.response) {
      alert.error('Failed to generate timetable')
    }
  } finally {
    loading.value = false
  }
}

function viewTimetable(timetableId: number) {
  router.push(`/timetable/${timetableId}`)
}

function onDateSelected(date: Date) {
  // Find timetables that are valid for this date
  const dateStr = date.toISOString().split('T')[0]
  const validTimetables = timetables.value.filter(t => {
    if (t.is_primary === 0) {
      // Substitute timetable - check if it's for this date
      return t.substitute_for_date === dateStr
    } else {
      // Primary timetable - check if date is within valid range
      if (!t.valid_from || !t.valid_to) return false
      return dateStr >= t.valid_from && dateStr <= t.valid_to
    }
  })
  
  if (validTimetables.length > 0) {
    // If there's a substitute timetable for this date, use it; otherwise use the primary
    const substitute = validTimetables.find(t => t.is_primary === 0)
    const timetableToView = substitute || validTimetables[0]
    viewTimetable(timetableToView.id)
  }
}

async function validateTimetable(timetableId: number) {
  loading.value = true
  
  try {
    const schoolId = authStore.user?.school_id
    if (!schoolId) {
      throw new Error('School ID not found')
    }
    
    const response = await api.post(
      `/timetables/schools/${schoolId}/timetables/${timetableId}/validate`
    )
    const validationResult = response.data
    
    if (validationResult.is_valid) {
      alert.success('Timetable is valid!')
    } else {
      // Show each validation error as a separate alert
      if (validationResult.errors && validationResult.errors.length > 0) {
        validationResult.errors.forEach((err: any, index: number) => {
          // Stagger the alerts slightly so they don't all appear at once
          setTimeout(() => {
            alert.error(err.message || 'Validation error', 8000) // Show errors for 8 seconds
          }, index * 200)
        })
      } else {
        alert.error('Timetable validation failed')
      }
    }
  } catch (err: any) {
    // Error will be shown via API interceptor
    console.error('Failed to validate timetable:', err)
  } finally {
    loading.value = false
  }
}

async function deleteTimetable(timetableId: number) {
  if (!confirm('Are you sure you want to delete this timetable?')) {
    return
  }
  
  loading.value = true
  
  try {
    const schoolId = authStore.user?.school_id
    if (!schoolId) {
      throw new Error('School ID not found')
    }
    
    await api.delete(`/timetables/schools/${schoolId}/timetables/${timetableId}`)
    alert.success('Timetable deleted successfully')
    await loadTimetables()
  } catch (err: any) {
    if (!err.response) {
      alert.error('Failed to delete timetable')
    }
  } finally {
    loading.value = false
  }
}

async function generateSubstituteTimetable() {
  if (!substituteForm.value.base_timetable_id || !substituteForm.value.substitute_date) {
    alert.error('Please select a base timetable and date')
    return
  }
  
  loading.value = true
  
  try {
    const schoolId = authStore.user?.school_id
    if (!schoolId) {
      throw new Error('School ID not found')
    }
    
    await api.post(
      `/timetables/schools/${schoolId}/timetables/${substituteForm.value.base_timetable_id}/generate-substitute`,
      {
        substitute_date: substituteForm.value.substitute_date
      }
    )
    
    alert.success('Substitute timetable generated successfully!')
    substituteForm.value = { base_timetable_id: null, substitute_date: '' }
    await loadTimetables()
  } catch (err: any) {
    if (!err.response) {
      alert.error('Failed to generate substitute timetable')
    }
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await loadTimetables()
})
</script>

<style lang="scss" scoped>
@import '../styles/neo.scss';

.timetables-list-view {
  min-height: 100vh;
  position: relative;
  z-index: 1;

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
  }

  &__controls {
    display: flex;
    gap: 1rem;
    align-items: center;
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
    @extend %neo-card;
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
    flex-direction: column;
    gap: 1rem;
    margin-bottom: 1rem;
  }

  &__form-row {
    display: flex;
    gap: 1rem;
  }

  &__form-group {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  &__label {
    font-weight: 600;
    color: $neo-text;
    font-size: 0.875rem;
  }

  &__input {
    @extend %neo-input;
    flex: 1;
    padding: 0.75rem;
    border-radius: 12px;
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

  &__list {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  &__item {
    @extend %neo-list-item;
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1.5rem;
    margin-bottom: 1rem;
  }

  &__item-info {
    flex: 1;
  }

  &__item-name {
    margin: 0 0 0.5rem 0;
    color: $neo-text;
    font-size: 1.25rem;
    font-weight: 700;
  }

  &__item-details {
    color: $neo-text-light;
    font-size: 0.875rem;
    margin-bottom: 0.5rem;
  }

  &__item-stats {
    color: $neo-text-muted;
    font-size: 0.875rem;
  }

  &__item-actions {
    display: flex;
    gap: 0.5rem;
  }

  &__view,
  &__validate,
  &__delete {
    @extend %neo-button;
    padding: 0.5rem 1rem;
    border-radius: 10px;
    cursor: pointer;
    font-size: 0.875rem;
    font-weight: 600;

    &:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
  }

  &__view {
    @extend %neo-button--primary;
  }

  &__validate {
    @extend %neo-button--success;
  }

  &__delete {
    @extend %neo-button--danger;
  }

  &__loading {
    text-align: center;
    padding: 2rem;
    color: $neo-text-light;
  }

  &__empty {
    text-align: center;
    padding: 3rem;
    color: $neo-text-muted;
    font-style: italic;
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

