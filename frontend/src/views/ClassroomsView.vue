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
                <span v-if="classroom.capacity" class="classrooms-view__capacity">
                  Capacity: {{ classroom.capacity }} students
                </span>
                <span v-else class="classrooms-view__capacity classrooms-view__capacity--none">
                  Capacity: Not set
                </span>
                <span v-if="classroom.specializations && classroom.specializations.length > 0" class="classrooms-view__specializations">
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
@import '../styles/neo.scss';

.classrooms-view {
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

  &__back {
    @extend %neo-button;
    @extend %neo-button--secondary;
    padding: 0.75rem 1.5rem;
    text-decoration: none;
    border-radius: 12px;
    font-weight: 500;

    &:hover {
      background: $neo-bg-light;
      border-color: $neo-bg-base;
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    }
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
  }

  &__input {
    @extend %neo-input;
    padding: 0.75rem;
    border-radius: 12px;
    font-size: 1rem;

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
    color: $neo-text;
    
  }

  &__hint {
    display: block;
    color: $neo-text-muted;
    font-size: 0.875rem;
    margin-top: -0.25rem;
  }

  &__button {
    @extend %neo-button;
    padding: 0.75rem 2rem;
    border-radius: 12px;
    cursor: pointer;
    font-size: 1rem;
    align-self: flex-start;
    font-weight: 600;

    &:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }

    &--secondary {
      background: $neo-bg-light;
      border-color: $neo-bg-light;

      &:hover:not(:disabled) {
        background: $neo-bg-light;
        border-color: $neo-bg-base;
      }
    }
  }

  &__list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  &__item {
    @extend %neo-list-item;
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem;
    margin-bottom: 0.5rem;

    &-info {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }

    &-name {
      font-weight: 600;
      color: $neo-text;
    }

    &-details {
      display: flex;
      gap: 1rem;
      color: $neo-text-light;
      font-size: 0.875rem;
    }

    &-no-specializations {
      color: $neo-text-muted;
      font-style: italic;
      font-size: 0.875rem;
    }
  }

  &__capacity {
    font-weight: 600;
    color: $neo-text;

    &--none {
      color: $neo-text-muted;
      font-weight: normal;
    }
  }

  &__specializations {
    margin-left: 1rem;
  }

  &__item-actions {
    display: flex;
    gap: 0.5rem;
  }

  &__edit,
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

  &__edit {
    @extend %neo-button--warning;
  }

  &__delete {
    @extend %neo-button--danger;
  }

  &__empty {
    padding: 2rem;
    text-align: center;
    color: $neo-text-muted;
    font-style: italic;
  }

  &__modal {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.3);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
  }

  &__modal-content {
    @extend %neo-modal;
    padding: 2rem;
    max-width: 500px;
    width: 90%;
    max-height: 90vh;
    overflow-y: auto;

    h3 {
      color: $neo-text;
    }
  }

  &__modal-actions {
    display: flex;
    gap: 1rem;
    margin-top: 1rem;
  }

  &__error {
    @extend %neo-message;
    @extend %neo-message--error;
    padding: 1rem;
    border-radius: 12px;
    margin-top: 1rem;
  }

  &__success {
    @extend %neo-message;
    @extend %neo-message--success;
    padding: 1rem;
    border-radius: 12px;
    margin-top: 1rem;
  }
}
</style>

