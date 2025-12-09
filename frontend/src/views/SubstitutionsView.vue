<template>
  <div class="substitutions-view">
    <header class="substitutions-view__header">
      <h1 class="substitutions-view__title">Manage Substitutions</h1>
      <router-link to="/admin" class="substitutions-view__back">Back</router-link>
    </header>
    <main class="substitutions-view__content">
      <div class="substitutions-view__section">
        <h2>Generate Substitutions</h2>
        <form @submit.prevent="generateSubstitutions" class="substitutions-view__form">
          <select
            v-model="selectedAbsenceId"
            class="substitutions-view__input"
            required
          >
            <option value="">Select Absence</option>
            <option
              v-for="absence in absences"
              :key="absence.id"
              :value="absence.id"
            >
              Teacher {{ absence.teacher_id }}: {{ formatDate(absence.date_from) }} - {{ formatDate(absence.date_to) }}
            </option>
          </select>
          <button type="submit" class="substitutions-view__button" :disabled="loading">
            Generate Substitutions
          </button>
        </form>
      </div>

      <div class="substitutions-view__section">
        <h2>Substitutions</h2>
        <div v-if="substitutions.length > 0" class="substitutions-view__list">
          <div
            v-for="substitution in substitutions"
            :key="substitution.id"
            class="substitutions-view__item"
          >
            <div class="substitutions-view__item-info">
              <span class="substitutions-view__item-status" :class="`substitutions-view__item-status--${substitution.status.toLowerCase()}`">
                {{ substitution.status }}
              </span>
              <span class="substitutions-view__item-details">
                Entry ID: {{ substitution.timetable_entry_id }}
                <span v-if="substitution.substitute_teacher_id">
                  → Substitute Teacher: {{ substitution.substitute_teacher_id }}
                </span>
                <span v-else class="substitutions-view__item-warning">No substitute found</span>
              </span>
            </div>
            <div class="substitutions-view__item-actions">
              <button
                v-if="substitution.status === 'AUTO_GENERATED'"
                @click="approveSubstitution(substitution.id)"
                class="substitutions-view__approve"
                :disabled="loading"
              >
                Approve
              </button>
              <button
                @click="editSubstitution(substitution)"
                class="substitutions-view__edit"
                :disabled="loading"
              >
                Edit
              </button>
            </div>
          </div>
        </div>
        <div v-else class="substitutions-view__empty">No substitutions yet</div>
      </div>

      <!-- Edit Modal -->
      <div v-if="editingSubstitution" class="substitutions-view__modal">
        <div class="substitutions-view__modal-content">
          <h3>Edit Substitution</h3>
          <form @submit.prevent="updateSubstitution" class="substitutions-view__form">
            <select
              v-model="editingSubstitution.substitute_teacher_id"
              class="substitutions-view__input"
            >
              <option :value="null">No Substitute</option>
              <option
                v-for="teacher in teachers"
                :key="teacher.id"
                :value="teacher.id"
              >
                {{ teacher.full_name }}
              </option>
            </select>
            <select
              v-model="editingSubstitution.status"
              class="substitutions-view__input"
            >
              <option value="AUTO_GENERATED">Auto Generated</option>
              <option value="CONFIRMED">Confirmed</option>
              <option value="MANUAL_OVERRIDE">Manual Override</option>
            </select>
            <div class="substitutions-view__modal-actions">
              <button type="submit" class="substitutions-view__button" :disabled="loading">
                Save
              </button>
              <button
                type="button"
                @click="editingSubstitution = null"
                class="substitutions-view__button substitutions-view__button--secondary"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      </div>

      <div v-if="error" class="substitutions-view__error">{{ error }}</div>
      <div v-if="success" class="substitutions-view__success">{{ success }}</div>
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
}

interface Teacher {
  id: number
  full_name: string
}

interface Substitution {
  id: number
  timetable_entry_id: number
  original_teacher_id: number
  substitute_teacher_id: number | null
  status: string
  school_id: number
}

const authStore = useAuthStore()
const substitutions = ref<Substitution[]>([])
const absences = ref<Absence[]>([])
const teachers = ref<Teacher[]>([])
const loading = ref(false)
const error = ref('')
const success = ref('')
const editingSubstitution = ref<Substitution | null>(null)
const selectedAbsenceId = ref<number | null>(null)

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString()
}

async function loadAbsences() {
  try {
    const schoolId = authStore.user?.school_id
    if (!schoolId) return
    
    const response = await api.get(`/absences/schools/${schoolId}/absences`)
    absences.value = response.data
  } catch (err: any) {
    console.error('Failed to load absences:', err)
  }
}

async function loadTeachers() {
  try {
    const schoolId = authStore.user?.school_id
    if (!schoolId) return
    
    const response = await api.get(`/teachers/schools/${schoolId}/teachers`)
    teachers.value = response.data
  } catch (err: any) {
    console.error('Failed to load teachers:', err)
  }
}

async function loadSubstitutions() {
  try {
    const schoolId = authStore.user?.school_id
    if (!schoolId) return
    
    const response = await api.get(`/substitutions/schools/${schoolId}/substitutions`)
    substitutions.value = response.data
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to load substitutions'
  }
}

async function generateSubstitutions() {
  if (!selectedAbsenceId.value) return
  
  loading.value = true
  error.value = ''
  success.value = ''
  
  try {
    const schoolId = authStore.user?.school_id
    if (!schoolId) {
      throw new Error('School ID not found')
    }
    
    // The endpoint expects absence_id as a query parameter
    await api.post(`/substitutions/schools/${schoolId}/substitutions/generate?absence_id=${selectedAbsenceId.value}`)
    success.value = 'Substitutions generated successfully'
    selectedAbsenceId.value = null
    await loadSubstitutions()
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to generate substitutions'
  } finally {
    loading.value = false
  }
}

function editSubstitution(substitution: Substitution) {
  editingSubstitution.value = { ...substitution }
}

async function updateSubstitution() {
  if (!editingSubstitution.value) return
  
  loading.value = true
  error.value = ''
  success.value = ''
  
  try {
    const schoolId = authStore.user?.school_id
    if (!schoolId) {
      throw new Error('School ID not found')
    }
    
    await api.put(`/substitutions/schools/${schoolId}/substitutions/${editingSubstitution.value.id}`, {
      substitute_teacher_id: editingSubstitution.value.substitute_teacher_id,
      status: editingSubstitution.value.status
    })
    success.value = 'Substitution updated successfully'
    editingSubstitution.value = null
    await loadSubstitutions()
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to update substitution'
  } finally {
    loading.value = false
  }
}

async function approveSubstitution(substitutionId: number) {
  loading.value = true
  error.value = ''
  success.value = ''
  
  try {
    const schoolId = authStore.user?.school_id
    if (!schoolId) {
      throw new Error('School ID not found')
    }
    
    const substitution = substitutions.value.find(s => s.id === substitutionId)
    if (!substitution) return
    
    await api.put(`/substitutions/schools/${schoolId}/substitutions/${substitutionId}`, {
      status: 'CONFIRMED',
      substitute_teacher_id: substitution.substitute_teacher_id
    })
    success.value = 'Substitution approved successfully'
    await loadSubstitutions()
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to approve substitution'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadAbsences()
  loadTeachers()
  loadSubstitutions()
})
</script>

<style lang="scss" scoped>
@import '../styles/neo.scss';

.substitutions-view {
  min-height: 100vh;
  background: transparent;

  &__header {
    background: $neo-bg-base;
    padding: 1rem 2rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  }

  &__title {
    color: $neo-text;
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
    background: $neo-bg-base;
    padding: 2rem;
    border-radius: 8px;
    margin-bottom: 2rem;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);

    h2 {
      margin-bottom: 1rem;
      color: $neo-text;
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

    &--secondary {
      background-color: #6c757d;

      &:hover {
        background-color: #5a6268;
      }
    }
  }

  &__list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  &__item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem;
    background: $neo-bg-light;
    border-radius: 4px;
    border: 1px solid #dee2e6;

    &-info {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }

    &-status {
      padding: 0.25rem 0.5rem;
      border-radius: 4px;
      font-size: 0.75rem;
      font-weight: 600;
      display: inline-block;
      width: fit-content;

      &--auto_generated {
        background-color: #ffc107;
        color: $neo-text;
      }

      &--confirmed {
        background-color: #28a745;
        color: white;
      }

      &--manual_override {
        background-color: #17a2b8;
        color: white;
      }
    }

    &-details {
      color: $neo-text-light;
      font-size: 0.875rem;
    }

    &-warning {
      color: #dc3545;
      font-weight: 600;
    }
  }

  &__item-actions {
    display: flex;
    gap: 0.5rem;
  }

  &__approve {
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

  &__edit {
    padding: 0.5rem 1rem;
    background-color: #ffc107;
    color: $neo-text;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.875rem;

    &:hover:not(:disabled) {
      background-color: #e0a800;
    }

    &:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }
  }

  &__empty {
    padding: 2rem;
    text-align: center;
    color: $neo-text-light;
    font-style: italic;
  }

  &__modal {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
  }

  &__modal-content {
    background: $neo-bg-base;
    padding: 2rem;
    border-radius: 8px;
    max-width: 500px;
    width: 90%;
  }

  &__modal-actions {
    display: flex;
    gap: 1rem;
    margin-top: 1rem;
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

