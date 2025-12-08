<template>
  <div class="classes-view">
    <header class="classes-view__header">
      <h1 class="classes-view__title">Manage Classes</h1>
      <router-link to="/admin" class="classes-view__back">Back</router-link>
    </header>
    <main class="classes-view__content">
      <!-- Grade Levels Section -->
      <div class="classes-view__section">
        <h2>Grade Levels</h2>
        <form @submit.prevent="createGradeLevel" class="classes-view__form">
          <input
            v-model="newGradeLevel.name"
            type="text"
            placeholder="Grade level name (e.g., 1st, 2nd)"
            class="classes-view__input"
            required
          />
          <input
            v-model.number="newGradeLevel.level"
            type="number"
            placeholder="Level (for sorting)"
            class="classes-view__input"
            min="1"
          />
          <button type="submit" class="classes-view__button" :disabled="loading">
            Add Grade Level
          </button>
        </form>
        <div v-if="gradeLevels.length > 0" class="classes-view__list">
          <div
            v-for="gradeLevel in gradeLevels"
            :key="gradeLevel.id"
            class="classes-view__item"
          >
            <span class="classes-view__item-name">{{ gradeLevel.name }}</span>
            <span v-if="gradeLevel.level" class="classes-view__item-level">Level: {{ gradeLevel.level }}</span>
          </div>
        </div>
        <div v-else class="classes-view__empty">No grade levels yet</div>
      </div>

      <!-- Classes Section -->
      <div class="classes-view__section">
        <h2>Classes</h2>
        <form @submit.prevent="createClass" class="classes-view__form">
          <input
            v-model="newClass.name"
            type="text"
            placeholder="Class name (e.g., 1.A, 1.B)"
            class="classes-view__input"
            required
          />
          <select
            v-model="newClass.grade_level_id"
            class="classes-view__input"
            required
          >
            <option value="">Select grade level</option>
            <option
              v-for="gradeLevel in gradeLevels"
              :key="gradeLevel.id"
              :value="gradeLevel.id"
            >
              {{ gradeLevel.name }}
            </option>
          </select>
          <button type="submit" class="classes-view__button" :disabled="loading || !newClass.grade_level_id">
            Add Class
          </button>
        </form>
        <div v-if="classes.length > 0" class="classes-view__list">
          <div
            v-for="classItem in classes"
            :key="classItem.id"
            class="classes-view__item classes-view__item--class"
          >
            <div class="classes-view__item-main">
              <span class="classes-view__item-name">{{ classItem.name }}</span>
              <span class="classes-view__item-grade">
                Grade: {{ getGradeLevelName(classItem.grade_level_id) }}
              </span>
            </div>
            <div class="classes-view__item-actions">
              <button
                @click="manageSubjectAllocations(classItem)"
                class="classes-view__manage-subjects"
                :disabled="loading"
              >
                Manage Subjects
              </button>
              <button
                @click="deleteClass(classItem.id)"
                class="classes-view__delete"
                :disabled="loading"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
        <div v-else class="classes-view__empty">No classes yet. Create a grade level first.</div>
      </div>

      <!-- Subject Allocations Modal -->
      <div v-if="managingAllocations" class="classes-view__modal">
        <div class="classes-view__modal-content classes-view__modal-content--large">
          <h3>Manage Subject Allocations for {{ managingAllocations.name }}</h3>
          <div class="classes-view__allocations-section">
            <h4>Add Subject Allocation</h4>
            <form @submit.prevent="addAllocation" class="classes-view__form">
              <select
                v-model="newAllocation.subject_id"
                class="classes-view__input"
                required
              >
                <option value="">Select Subject</option>
                <option
                  v-for="subject in subjects"
                  :key="subject.id"
                  :value="subject.id"
                >
                  {{ subject.name }}
                </option>
              </select>
              <input
                v-model.number="newAllocation.weekly_hours"
                type="number"
                placeholder="Hours per week"
                min="1"
                class="classes-view__input"
                required
              />
              <button type="submit" class="classes-view__button" :disabled="loading">
                Add Allocation
              </button>
            </form>
          </div>
          <div class="classes-view__allocations-section">
            <h4>Current Subject Allocations</h4>
            <div v-if="classAllocations.length > 0" class="classes-view__allocations-list">
              <div
                v-for="allocation in classAllocations"
                :key="allocation.id"
                class="classes-view__allocation-item"
              >
                <span class="classes-view__allocation-subject">
                  {{ getSubjectName(allocation.subject_id) }}
                </span>
                <span class="classes-view__allocation-hours">
                  {{ allocation.weekly_hours }} hours/week
                </span>
                <button
                  @click="editAllocation(allocation)"
                  class="classes-view__allocation-edit"
                  :disabled="loading"
                >
                  Edit
                </button>
                <button
                  @click="removeAllocation(allocation.id)"
                  class="classes-view__allocation-remove"
                  :disabled="loading"
                >
                  Remove
                </button>
              </div>
            </div>
            <div v-else class="classes-view__empty">No subject allocations yet</div>
          </div>
          <div class="classes-view__modal-actions">
            <button
              type="button"
              @click="managingAllocations = null"
              class="classes-view__button classes-view__button--secondary"
            >
              Close
            </button>
          </div>
        </div>
      </div>

      <!-- Edit Allocation Modal -->
      <div v-if="editingAllocation" class="classes-view__modal">
        <div class="classes-view__modal-content">
          <h3>Edit Subject Allocation</h3>
          <form @submit.prevent="updateAllocation" class="classes-view__form">
            <input
              v-model.number="editingAllocation.weekly_hours"
              type="number"
              placeholder="Hours per week"
              min="1"
              class="classes-view__input"
              required
            />
            <div class="classes-view__modal-actions">
              <button type="submit" class="classes-view__button" :disabled="loading">
                Save
              </button>
              <button
                type="button"
                @click="editingAllocation = null"
                class="classes-view__button classes-view__button--secondary"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      </div>

      <div v-if="error" class="classes-view__error">{{ error }}</div>
      <div v-if="success" class="classes-view__success">{{ success }}</div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '@/services/api'

interface GradeLevel {
  id: number
  name: string
  level: number | null
  school_id: number
}

interface ClassGroup {
  id: number
  name: string
  grade_level_id: number
  school_id: number
}

interface Subject {
  id: number
  name: string
}

interface SubjectAllocation {
  id: number
  class_group_id: number
  subject_id: number
  weekly_hours: number
}

const gradeLevels = ref<GradeLevel[]>([])
const classes = ref<ClassGroup[]>([])
const subjects = ref<Subject[]>([])
const loading = ref(false)
const error = ref('')
const success = ref('')
const managingAllocations = ref<ClassGroup | null>(null)
const classAllocations = ref<SubjectAllocation[]>([])
const editingAllocation = ref<SubjectAllocation | null>(null)

const newGradeLevel = ref({
  name: '',
  level: null as number | null
})

const newClass = ref({
  name: '',
  grade_level_id: null as number | null
})

const newAllocation = ref({
  subject_id: null as number | null,
  weekly_hours: 1
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
    error.value = err.response?.data?.detail || 'Failed to load grade levels'
  }
}

async function loadClasses() {
  try {
    const response = await api.get('/class-groups/')
    classes.value = response.data
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to load classes'
  }
}

async function loadSubjects() {
  try {
    const { useAuthStore } = await import('@/stores/auth')
    const authStore = useAuthStore()
    const schoolId = authStore.user?.school_id
    if (!schoolId) return
    
    const response = await api.get(`/subjects/schools/${schoolId}/subjects`)
    subjects.value = response.data
  } catch (err: any) {
    console.error('Failed to load subjects:', err)
  }
}

async function loadClassAllocations(classGroupId: number) {
  try {
    const response = await api.get(`/subjects/class-subject-allocations?class_group_id=${classGroupId}`)
    classAllocations.value = response.data
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to load allocations'
  }
}

async function manageSubjectAllocations(classItem: ClassGroup) {
  managingAllocations.value = classItem
  await loadClassAllocations(classItem.id)
}

async function addAllocation() {
  if (!managingAllocations.value || !newAllocation.value.subject_id) return
  
  loading.value = true
  error.value = ''
  success.value = ''
  
  try {
    await api.post('/subjects/class-subject-allocations', {
      class_group_id: managingAllocations.value.id,
      subject_id: newAllocation.value.subject_id,
      weekly_hours: newAllocation.value.weekly_hours
    })
    success.value = 'Allocation added successfully'
    newAllocation.value = { subject_id: null, weekly_hours: 1 }
    await loadClassAllocations(managingAllocations.value.id)
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to add allocation'
  } finally {
    loading.value = false
  }
}

function editAllocation(allocation: SubjectAllocation) {
  editingAllocation.value = { ...allocation }
}

async function updateAllocation() {
  if (!editingAllocation.value) return
  
  loading.value = true
  error.value = ''
  success.value = ''
  
  try {
    await api.put(`/subjects/class-subject-allocations/${editingAllocation.value.id}`, {
      weekly_hours: editingAllocation.value.weekly_hours
    })
    success.value = 'Allocation updated successfully'
    editingAllocation.value = null
    if (managingAllocations.value) {
      await loadClassAllocations(managingAllocations.value.id)
    }
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to update allocation'
  } finally {
    loading.value = false
  }
}

async function removeAllocation(allocationId: number) {
  if (!confirm('Are you sure you want to remove this allocation?')) {
    return
  }
  
  loading.value = true
  error.value = ''
  success.value = ''
  
  try {
    await api.delete(`/subjects/class-subject-allocations/${allocationId}`)
    success.value = 'Allocation removed successfully'
    if (managingAllocations.value) {
      await loadClassAllocations(managingAllocations.value.id)
    }
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to remove allocation'
  } finally {
    loading.value = false
  }
}

function getSubjectName(subjectId: number): string {
  const subject = subjects.value.find(s => s.id === subjectId)
  return subject ? subject.name : 'Unknown'
}

async function createGradeLevel() {
  loading.value = true
  error.value = ''
  success.value = ''
  
  try {
    await api.post('/class-groups/grade-levels/', newGradeLevel.value)
    success.value = 'Grade level created successfully'
    newGradeLevel.value = { name: '', level: null }
    await loadGradeLevels()
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to create grade level'
  } finally {
    loading.value = false
  }
}

async function createClass() {
  loading.value = true
  error.value = ''
  success.value = ''
  
  try {
    await api.post('/class-groups/', {
      name: newClass.value.name,
      grade_level_id: newClass.value.grade_level_id
    })
    success.value = 'Class created successfully'
    newClass.value = { name: '', grade_level_id: null }
    await loadClasses()
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to create class'
  } finally {
    loading.value = false
  }
}

async function deleteClass(classId: number) {
  if (!confirm('Are you sure you want to delete this class?')) {
    return
  }
  
  loading.value = true
  error.value = ''
  success.value = ''
  
  try {
    await api.delete(`/class-groups/${classId}`)
    success.value = 'Class deleted successfully'
    await loadClasses()
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to delete class'
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await loadGradeLevels()
  await loadClasses()
  await loadSubjects()
})
</script>

<style lang="scss" scoped>
.classes-view {
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
    margin-bottom: 2rem;
    flex-wrap: wrap;
  }

  &__input {
    flex: 1;
    min-width: 200px;
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
    white-space: nowrap;

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
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 1rem;
    background-color: #f8f9fa;
    border-radius: 4px;
    border: 1px solid #dee2e6;

    &--class {
      justify-content: space-between;
    }

    &-main {
      display: flex;
      flex-direction: column;
      gap: 0.25rem;
    }

    &-actions {
      display: flex;
      gap: 0.5rem;
    }

    &-name {
      font-weight: 600;
      color: #333;
    }

    &-level {
      color: #666;
      font-size: 0.875rem;
    }

    &-grade {
      color: #666;
      font-size: 0.875rem;
    }
  }

  &__manage-subjects {
    padding: 0.5rem 1rem;
    background-color: #17a2b8;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.875rem;

    &:hover:not(:disabled) {
      background-color: #138496;
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

    &--large {
      max-width: 700px;
    }
  }

  &__modal-actions {
    display: flex;
    gap: 1rem;
    margin-top: 1rem;
  }

  &__allocations-section {
    margin-bottom: 2rem;
    padding-bottom: 2rem;
    border-bottom: 1px solid #dee2e6;

    &:last-child {
      border-bottom: none;
    }

    h4 {
      margin-bottom: 1rem;
      color: #333;
    }
  }

  &__allocations-list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  &__allocation-item {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 0.75rem;
    background-color: #f8f9fa;
    border-radius: 4px;
    border: 1px solid #dee2e6;
  }

  &__allocation-subject {
    font-weight: 600;
    color: #333;
    flex: 1;
  }

  &__allocation-hours {
    color: #4a90e2;
    font-weight: 600;
  }

  &__allocation-edit {
    padding: 0.25rem 0.75rem;
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

  &__allocation-remove {
    padding: 0.25rem 0.75rem;
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
}
</style>

