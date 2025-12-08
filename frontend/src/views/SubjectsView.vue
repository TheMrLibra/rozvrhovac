<template>
  <div class="subjects-view">
    <header class="subjects-view__header">
      <h1 class="subjects-view__title">Manage Subjects</h1>
      <router-link to="/admin" class="subjects-view__back">Back</router-link>
    </header>
    <main class="subjects-view__content">
      <div class="subjects-view__section">
        <h2>Add New Subject</h2>
        <form @submit.prevent="createSubject" class="subjects-view__form">
          <input
            v-model="newSubject.name"
            type="text"
            placeholder="Subject Name"
            class="subjects-view__input"
            required
          />
          <select
            v-model="newSubject.grade_level_id"
            class="subjects-view__input"
          >
            <option :value="null">All Grade Levels</option>
            <option
              v-for="gradeLevel in gradeLevels"
              :key="gradeLevel.id"
              :value="gradeLevel.id"
            >
              {{ gradeLevel.name }}
            </option>
          </select>
          <div class="subjects-view__field-group">
            <div class="subjects-view__field">
              <label class="subjects-view__label">
                <input
                  v-model="newSubject.allow_multiple_in_one_day"
                  type="checkbox"
                />
                Can be taught more than once per day
              </label>
              <small class="subjects-view__hint">If checked, this subject can appear multiple times in the same day</small>
            </div>
            <div class="subjects-view__field">
              <label class="subjects-view__label">
                <input
                  v-model="newSubject.allow_consecutive_hours"
                  type="checkbox"
                />
                Allow consecutive hours
              </label>
              <small class="subjects-view__hint">If checked, this subject can be scheduled in consecutive time slots</small>
            </div>
            <div v-if="newSubject.allow_consecutive_hours" class="subjects-view__field">
              <label class="subjects-view__label">Maximum consecutive hours</label>
              <input
                v-model.number="newSubject.max_consecutive_hours"
                type="number"
                placeholder="e.g., 2"
                min="1"
                class="subjects-view__input"
              />
              <small class="subjects-view__hint">Maximum number of consecutive hours allowed (leave empty for no limit)</small>
            </div>
            <div class="subjects-view__field">
              <label class="subjects-view__label">Required block length (if any)</label>
              <input
                v-model.number="newSubject.required_block_length"
                type="number"
                placeholder="e.g., 2 for 2-hour lab blocks"
                min="1"
                class="subjects-view__input"
              />
              <small class="subjects-view__hint">If specified, this subject must be scheduled in blocks of this many hours</small>
            </div>
            <div class="subjects-view__checkbox-group">
              <label class="subjects-view__checkbox">
                <input
                  v-model="newSubject.is_laboratory"
                  type="checkbox"
                />
                Is Laboratory
              </label>
              <label class="subjects-view__checkbox">
                <input
                  v-model="newSubject.requires_specialized_classroom"
                  type="checkbox"
                />
                Requires Specialized Classroom
              </label>
            </div>
          </div>
          <button type="submit" class="subjects-view__button" :disabled="loading">
            Add Subject
          </button>
        </form>
      </div>

      <div class="subjects-view__section">
        <h2>Subjects List</h2>
        <div v-if="subjects.length > 0" class="subjects-view__list">
          <div
            v-for="subject in subjects"
            :key="subject.id"
            class="subjects-view__item"
          >
            <div class="subjects-view__item-info">
              <span class="subjects-view__item-name">{{ subject.name }}</span>
              <span class="subjects-view__item-details">
                <span v-if="subject.grade_level_id">Grade: {{ getGradeLevelName(subject.grade_level_id) }}</span>
                <span v-if="subject.is_laboratory" class="subjects-view__badge">Lab</span>
                <span v-if="subject.requires_specialized_classroom" class="subjects-view__badge">Specialized</span>
              </span>
            </div>
            <div class="subjects-view__item-actions">
              <button
                @click="editSubject(subject)"
                class="subjects-view__edit"
                :disabled="loading"
              >
                Edit
              </button>
              <button
                @click="deleteSubject(subject.id)"
                class="subjects-view__delete"
                :disabled="loading"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
        <div v-else class="subjects-view__empty">No subjects yet</div>
      </div>

      <!-- Edit Modal -->
      <div v-if="editingSubject" class="subjects-view__modal">
        <div class="subjects-view__modal-content">
          <h3>Edit Subject</h3>
          <form @submit.prevent="updateSubject" class="subjects-view__form">
            <input
              v-model="editingSubject.name"
              type="text"
              placeholder="Subject Name"
              class="subjects-view__input"
              required
            />
            <select
              v-model="editingSubject.grade_level_id"
              class="subjects-view__input"
            >
              <option :value="null">All Grade Levels</option>
              <option
                v-for="gradeLevel in gradeLevels"
                :key="gradeLevel.id"
                :value="gradeLevel.id"
              >
                {{ gradeLevel.name }}
              </option>
            </select>
            <div class="subjects-view__field-group">
              <div class="subjects-view__field">
                <label class="subjects-view__label">
                  <input
                    v-model="editingSubject.allow_multiple_in_one_day"
                    type="checkbox"
                  />
                  Can be taught more than once per day
                </label>
                <small class="subjects-view__hint">If checked, this subject can appear multiple times in the same day</small>
              </div>
              <div class="subjects-view__field">
                <label class="subjects-view__label">
                  <input
                    v-model="editingSubject.allow_consecutive_hours"
                    type="checkbox"
                  />
                  Allow consecutive hours
                </label>
                <small class="subjects-view__hint">If checked, this subject can be scheduled in consecutive time slots</small>
              </div>
              <div v-if="editingSubject.allow_consecutive_hours" class="subjects-view__field">
                <label class="subjects-view__label">Maximum consecutive hours</label>
                <input
                  v-model.number="editingSubject.max_consecutive_hours"
                  type="number"
                  placeholder="e.g., 2"
                  min="1"
                  class="subjects-view__input"
                />
                <small class="subjects-view__hint">Maximum number of consecutive hours allowed (leave empty for no limit)</small>
              </div>
              <div class="subjects-view__field">
                <label class="subjects-view__label">Required block length (if any)</label>
                <input
                  v-model.number="editingSubject.required_block_length"
                  type="number"
                  placeholder="e.g., 2 for 2-hour lab blocks"
                  min="1"
                  class="subjects-view__input"
                />
                <small class="subjects-view__hint">If specified, this subject must be scheduled in blocks of this many hours</small>
              </div>
              <div class="subjects-view__checkbox-group">
                <label class="subjects-view__checkbox">
                  <input
                    v-model="editingSubject.is_laboratory"
                    type="checkbox"
                  />
                  Is Laboratory
                </label>
                <label class="subjects-view__checkbox">
                  <input
                    v-model="editingSubject.requires_specialized_classroom"
                    type="checkbox"
                  />
                  Requires Specialized Classroom
                </label>
              </div>
            </div>
            <div class="subjects-view__modal-actions">
              <button type="submit" class="subjects-view__button" :disabled="loading">
                Save
              </button>
              <button
                type="button"
                @click="editingSubject = null"
                class="subjects-view__button subjects-view__button--secondary"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      </div>

      <div v-if="error" class="subjects-view__error">{{ error }}</div>
      <div v-if="success" class="subjects-view__success">{{ success }}</div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import api from '@/services/api'

interface GradeLevel {
  id: number
  name: string
}

interface Subject {
  id: number
  name: string
  grade_level_id: number | null
  allow_consecutive_hours: boolean
  max_consecutive_hours: number | null
  allow_multiple_in_one_day: boolean
  required_block_length: number | null
  is_laboratory: boolean
  requires_specialized_classroom: boolean
  school_id: number
}

const authStore = useAuthStore()
const subjects = ref<Subject[]>([])
const gradeLevels = ref<GradeLevel[]>([])
const loading = ref(false)
const error = ref('')
const success = ref('')
const editingSubject = ref<Subject | null>(null)

const newSubject = ref({
  name: '',
  grade_level_id: null as number | null,
  allow_consecutive_hours: true,
  max_consecutive_hours: null as number | null,
  allow_multiple_in_one_day: true,
  required_block_length: null as number | null,
  is_laboratory: false,
  requires_specialized_classroom: false
})

function getGradeLevelName(gradeLevelId: number): string {
  const gradeLevel = gradeLevels.value.find(gl => gl.id === gradeLevelId)
  return gradeLevel ? gradeLevel.name : 'Unknown'
}

async function loadGradeLevels() {
  try {
    const response = await api.get('/class-groups/grade-levels/')
    gradeLevels.value = response.data
  } catch (err: any) {
    console.error('Failed to load grade levels:', err)
  }
}

async function loadSubjects() {
  try {
    const schoolId = authStore.user?.school_id
    if (!schoolId) return
    
    const response = await api.get(`/subjects/schools/${schoolId}/subjects`)
    subjects.value = response.data
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to load subjects'
  }
}

async function createSubject() {
  loading.value = true
  error.value = ''
  success.value = ''
  
  try {
    const schoolId = authStore.user?.school_id
    if (!schoolId) {
      throw new Error('School ID not found')
    }
    
    const subjectData = {
      ...newSubject.value,
      grade_level_id: newSubject.value.grade_level_id || null
    }
    
    await api.post(`/subjects/schools/${schoolId}/subjects`, subjectData)
    success.value = 'Subject created successfully'
    newSubject.value = {
      name: '',
      grade_level_id: null,
      allow_consecutive_hours: true,
      max_consecutive_hours: null,
      allow_multiple_in_one_day: true,
      required_block_length: null,
      is_laboratory: false,
      requires_specialized_classroom: false
    }
    await loadSubjects()
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to create subject'
  } finally {
    loading.value = false
  }
}

function editSubject(subject: Subject) {
  editingSubject.value = { ...subject }
}

async function updateSubject() {
  if (!editingSubject.value) return
  
  loading.value = true
  error.value = ''
  success.value = ''
  
  try {
    const schoolId = authStore.user?.school_id
    if (!schoolId) {
      throw new Error('School ID not found')
    }
    
    const updateData: any = {}
    if (editingSubject.value.name) updateData.name = editingSubject.value.name
    if (editingSubject.value.grade_level_id !== undefined) updateData.grade_level_id = editingSubject.value.grade_level_id
    updateData.allow_consecutive_hours = editingSubject.value.allow_consecutive_hours
    updateData.max_consecutive_hours = editingSubject.value.max_consecutive_hours
    updateData.allow_multiple_in_one_day = editingSubject.value.allow_multiple_in_one_day
    updateData.required_block_length = editingSubject.value.required_block_length
    updateData.is_laboratory = editingSubject.value.is_laboratory
    updateData.requires_specialized_classroom = editingSubject.value.requires_specialized_classroom
    
    await api.put(`/subjects/schools/${schoolId}/subjects/${editingSubject.value.id}`, updateData)
    success.value = 'Subject updated successfully'
    editingSubject.value = null
    await loadSubjects()
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to update subject'
  } finally {
    loading.value = false
  }
}

async function deleteSubject(subjectId: number) {
  if (!confirm('Are you sure you want to delete this subject?')) {
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
    
    await api.delete(`/subjects/schools/${schoolId}/subjects/${subjectId}`)
    success.value = 'Subject deleted successfully'
    await loadSubjects()
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to delete subject'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadGradeLevels()
  loadSubjects()
})
</script>

<style lang="scss" scoped>
.subjects-view {
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

  &__field-group {
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
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-weight: 600;
    color: #333;
    cursor: pointer;
  }

  &__hint {
    display: block;
    color: #666;
    font-size: 0.875rem;
    margin-top: -0.25rem;
  }

  &__checkbox-group {
    display: flex;
    flex-wrap: wrap;
    gap: 1rem;
    margin-top: 0.5rem;
  }

  &__checkbox {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    cursor: pointer;
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
      align-items: center;
      color: #666;
      font-size: 0.875rem;
    }
  }

  &__badge {
    padding: 0.25rem 0.5rem;
    background-color: #ffc107;
    color: #333;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 600;
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

