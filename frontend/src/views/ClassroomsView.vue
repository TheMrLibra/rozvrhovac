<template>
  <div class="classrooms-view">
    <header class="classrooms-view__header">
      <h1 class="classrooms-view__title">Manage Classrooms</h1>
      <router-link to="/admin" class="classrooms-view__back">Back</router-link>
    </header>
    <main class="classrooms-view__content">
      <div class="classrooms-view__section">
        <h2>Add New Classroom</h2>
        <form @submit.prevent="createClassroom" class="classrooms-view__form">
          <input
            v-model="newClassroom.name"
            type="text"
            placeholder="Classroom Name"
            class="classrooms-view__input"
            required
          />
          <input
            v-model.number="newClassroom.capacity"
            type="number"
            placeholder="Capacity (optional)"
            min="1"
            class="classrooms-view__input"
          />
          <div class="classrooms-view__field">
            <label class="classrooms-view__label">Specializations (select subjects, optional)</label>
            <select
              v-model="newClassroom.specializations"
              multiple
              class="classrooms-view__input classrooms-view__input--multiselect"
            >
              <option
                v-for="subject in subjects"
                :key="subject.id"
                :value="subject.id"
              >
                {{ subject.name }}
              </option>
            </select>
            <small class="classrooms-view__hint">Hold Ctrl/Cmd to select multiple subjects. Leave empty for no specializations.</small>
          </div>
          <input
            v-model="restrictionsInput"
            type="text"
            placeholder="Restrictions (comma-separated, e.g., no_physical_education)"
            class="classrooms-view__input"
          />
          <button type="submit" class="classrooms-view__button" :disabled="loading">
            Add Classroom
          </button>
        </form>
      </div>

      <div class="classrooms-view__section">
        <h2>Classrooms List</h2>
        <div v-if="classrooms.length > 0" class="classrooms-view__list">
          <div
            v-for="classroom in classrooms"
            :key="classroom.id"
            class="classrooms-view__item"
          >
            <div class="classrooms-view__item-info">
              <span class="classrooms-view__item-name">{{ classroom.name }}</span>
              <span class="classrooms-view__item-details">
                <span v-if="classroom.capacity">Capacity: {{ classroom.capacity }}</span>
                <span v-if="classroom.specializations && classroom.specializations.length > 0">
                  Specializations: {{ getSpecializationNames(classroom.specializations) }}
                </span>
                <span v-else class="classrooms-view__item-no-specializations">
                  No specializations
                </span>
              </span>
            </div>
            <div class="classrooms-view__item-actions">
              <button
                @click="editClassroom(classroom)"
                class="classrooms-view__edit"
                :disabled="loading"
              >
                Edit
              </button>
              <button
                @click="deleteClassroom(classroom.id)"
                class="classrooms-view__delete"
                :disabled="loading"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
        <div v-else class="classrooms-view__empty">No classrooms yet</div>
      </div>

      <!-- Edit Modal -->
      <div v-if="editingClassroom" class="classrooms-view__modal">
        <div class="classrooms-view__modal-content">
          <h3>Edit Classroom</h3>
          <form @submit.prevent="updateClassroom" class="classrooms-view__form">
            <input
              v-model="editingClassroom.name"
              type="text"
              placeholder="Classroom Name"
              class="classrooms-view__input"
              required
            />
            <input
              v-model.number="editingClassroom.capacity"
              type="number"
              placeholder="Capacity"
              min="1"
              class="classrooms-view__input"
            />
            <div class="classrooms-view__field">
              <label class="classrooms-view__label">Specializations (select subjects, optional)</label>
              <select
                v-model="editingClassroom.specializations"
                multiple
                class="classrooms-view__input classrooms-view__input--multiselect"
              >
                <option
                  v-for="subject in subjects"
                  :key="subject.id"
                  :value="subject.id"
                >
                  {{ subject.name }}
                </option>
              </select>
              <small class="classrooms-view__hint">Hold Ctrl/Cmd to select multiple subjects. Leave empty for no specializations.</small>
            </div>
            <input
              v-model="editRestrictionsInput"
              type="text"
              placeholder="Restrictions (comma-separated)"
              class="classrooms-view__input"
            />
            <div class="classrooms-view__modal-actions">
              <button type="submit" class="classrooms-view__button" :disabled="loading">
                Save
              </button>
              <button
                type="button"
                @click="editingClassroom = null"
                class="classrooms-view__button classrooms-view__button--secondary"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      </div>

      <div v-if="error" class="classrooms-view__error">{{ error }}</div>
      <div v-if="success" class="classrooms-view__success">{{ success }}</div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import api from '@/services/api'

interface Classroom {
  id: number
  name: string
  capacity: number | null
  specializations: number[] | null  // List of subject IDs
  restrictions: string[] | null
  school_id: number
}

interface Subject {
  id: number
  name: string
}

const authStore = useAuthStore()
const classrooms = ref<Classroom[]>([])
const subjects = ref<Subject[]>([])
const loading = ref(false)
const error = ref('')
const success = ref('')
const editingClassroom = ref<Classroom | null>(null)

const newClassroom = ref({
  name: '',
  capacity: null as number | null,
  specializations: [] as number[],
  restrictions: null as string[] | null
})

const restrictionsInput = ref('')
const editRestrictionsInput = ref('')

function parseList(input: string): string[] | null {
  if (!input.trim()) return null
  return input.split(',').map(s => s.trim()).filter(s => s.length > 0)
}

function formatList(list: string[] | null): string {
  return list ? list.join(', ') : ''
}

function getSpecializationNames(subjectIds: number[]): string {
  return subjectIds
    .map(id => {
      const subject = subjects.value.find(s => s.id === id)
      return subject ? subject.name : `Unknown (${id})`
    })
    .join(', ')
}

async function loadSubjects() {
  try {
    const schoolId = authStore.user?.school_id
    if (!schoolId) return
    
    const response = await api.get(`/subjects/schools/${schoolId}/subjects`)
    subjects.value = response.data
  } catch (err: any) {
    console.error('Failed to load subjects:', err)
  }
}

async function loadClassrooms() {
  try {
    const schoolId = authStore.user?.school_id
    if (!schoolId) return
    
    const response = await api.get(`/classrooms/schools/${schoolId}/classrooms`)
    classrooms.value = response.data
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to load classrooms'
  }
}

async function createClassroom() {
  loading.value = true
  error.value = ''
  success.value = ''
  
  try {
    const schoolId = authStore.user?.school_id
    if (!schoolId) {
      throw new Error('School ID not found')
    }
    
    const classroomData = {
      ...newClassroom.value,
      specializations: newClassroom.value.specializations.length > 0 ? newClassroom.value.specializations : null,
      restrictions: parseList(restrictionsInput.value)
    }
    
    await api.post(`/classrooms/schools/${schoolId}/classrooms`, classroomData)
    success.value = 'Classroom created successfully'
    newClassroom.value = { name: '', capacity: null, specializations: [], restrictions: null }
    restrictionsInput.value = ''
    await loadClassrooms()
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to create classroom'
  } finally {
    loading.value = false
  }
}

function editClassroom(classroom: Classroom) {
  editingClassroom.value = {
    ...classroom,
    specializations: classroom.specializations ? [...classroom.specializations] : []  // Empty array means no specializations
  }
  editRestrictionsInput.value = formatList(classroom.restrictions)
}

async function updateClassroom() {
  if (!editingClassroom.value) return
  
  loading.value = true
  error.value = ''
  success.value = ''
  
  try {
    const schoolId = authStore.user?.school_id
    if (!schoolId) {
      throw new Error('School ID not found')
    }
    
    const updateData: any = {}
    if (editingClassroom.value.name) updateData.name = editingClassroom.value.name
    updateData.capacity = editingClassroom.value.capacity
    updateData.specializations = editingClassroom.value.specializations && editingClassroom.value.specializations.length > 0 
      ? editingClassroom.value.specializations 
      : null
    updateData.restrictions = parseList(editRestrictionsInput.value)
    
    await api.put(`/classrooms/schools/${schoolId}/classrooms/${editingClassroom.value.id}`, updateData)
    success.value = 'Classroom updated successfully'
    editingClassroom.value = null
    await loadClassrooms()
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to update classroom'
  } finally {
    loading.value = false
  }
}

async function deleteClassroom(classroomId: number) {
  if (!confirm('Are you sure you want to delete this classroom?')) {
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
    
    await api.delete(`/classrooms/schools/${schoolId}/classrooms/${classroomId}`)
    success.value = 'Classroom deleted successfully'
    await loadClassrooms()
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to delete classroom'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadClassrooms()
  loadSubjects()
})
</script>

<style lang="scss" scoped>
.classrooms-view {
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

    &--multiselect {
      min-height: 100px;
    }
  }

  &__field {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  &__label {
    font-weight: 600;
    color: #333;
  }

  &__hint {
    display: block;
    color: #666;
    font-size: 0.875rem;
    margin-top: -0.25rem;
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
    background-color: #f8f9fa;
    border-radius: 4px;
    border: 1px solid #dee2e6;

    &-info {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }

    &-name {
      font-weight: 600;
      color: #333;
    }

    &-details {
      display: flex;
      gap: 1rem;
      color: #666;
      font-size: 0.875rem;
    }

    &-no-specializations {
      color: #999;
      font-style: italic;
      font-size: 0.875rem;
    }
  }

  &__item-actions {
    display: flex;
    gap: 0.5rem;
  }

  &__edit {
    padding: 0.5rem 1rem;
    background-color: #ffc107;
    color: #333;
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

  &__empty {
    padding: 2rem;
    text-align: center;
    color: #666;
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
    background: white;
    padding: 2rem;
    border-radius: 8px;
    max-width: 500px;
    width: 90%;
    max-height: 90vh;
    overflow-y: auto;
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

