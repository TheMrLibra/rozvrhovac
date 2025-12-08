<template>
  <div class="teachers-view">
    <header class="teachers-view__header">
      <h1 class="teachers-view__title">Manage Teachers</h1>
      <router-link to="/admin" class="teachers-view__back">Back</router-link>
    </header>
    <main class="teachers-view__content">
      <div class="teachers-view__section">
        <h2>Add New Teacher</h2>
        <form @submit.prevent="createTeacher" class="teachers-view__form">
          <input
            v-model="newTeacher.full_name"
            type="text"
            placeholder="Full Name"
            class="teachers-view__input"
            required
          />
          <input
            v-model.number="newTeacher.max_weekly_hours"
            type="number"
            placeholder="Max Weekly Hours"
            min="1"
            class="teachers-view__input"
            required
          />
          <input
            v-model="availabilityInput"
            type="text"
            placeholder="Availability (e.g., monday:1,2,3 tuesday:1,2)"
            class="teachers-view__input"
          />
          <small class="teachers-view__hint">Format: day:hour1,hour2 (e.g., monday:1,2,3 tuesday:1,2)</small>
          <button type="submit" class="teachers-view__button" :disabled="loading">
            Add Teacher
          </button>
        </form>
      </div>

      <div class="teachers-view__section">
        <h2>Teachers List</h2>
        <div v-if="teachers.length > 0" class="teachers-view__list">
          <div
            v-for="teacher in teachers"
            :key="teacher.id"
            class="teachers-view__item"
          >
            <div class="teachers-view__item-info">
              <span class="teachers-view__item-name">{{ teacher.full_name }}</span>
              <span class="teachers-view__item-hours">Max Hours: {{ teacher.max_weekly_hours }}</span>
              <div v-if="teacher.capabilities && teacher.capabilities.length > 0" class="teachers-view__item-subjects">
                Subjects: {{ getTeacherSubjects(teacher.capabilities) }}
              </div>
              <div v-else class="teachers-view__item-no-subjects">No subjects assigned</div>
            </div>
            <div class="teachers-view__item-actions">
              <button
                @click="editTeacher(teacher)"
                class="teachers-view__edit"
                :disabled="loading"
              >
                Edit
              </button>
              <button
                @click="manageCapabilities(teacher)"
                class="teachers-view__capabilities"
                :disabled="loading"
              >
                Manage Specializations
              </button>
              <button
                @click="deleteTeacher(teacher.id)"
                class="teachers-view__delete"
                :disabled="loading"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
        <div v-else class="teachers-view__empty">No teachers yet</div>
      </div>

      <!-- Edit Modal -->
      <div v-if="editingTeacher" class="teachers-view__modal">
        <div class="teachers-view__modal-content">
          <h3>Edit Teacher</h3>
          <form @submit.prevent="updateTeacher" class="teachers-view__form">
            <input
              v-model="editingTeacher.full_name"
              type="text"
              placeholder="Full Name"
              class="teachers-view__input"
              required
            />
            <input
              v-model.number="editingTeacher.max_weekly_hours"
              type="number"
              placeholder="Max Weekly Hours"
              min="1"
              class="teachers-view__input"
              required
            />
            <input
              v-model="editAvailabilityInput"
              type="text"
              placeholder="Availability"
              class="teachers-view__input"
            />
            <div class="teachers-view__modal-actions">
              <button type="submit" class="teachers-view__button" :disabled="loading">
                Save
              </button>
              <button
                type="button"
                @click="editingTeacher = null"
                class="teachers-view__button teachers-view__button--secondary"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      </div>

      <!-- Capabilities Modal -->
      <div v-if="managingCapabilities" class="teachers-view__modal">
        <div class="teachers-view__modal-content teachers-view__modal-content--large">
          <h3>Manage Specializations for {{ managingCapabilities.full_name }}</h3>
          <div class="teachers-view__capabilities-section">
            <h4>Add New Specialization</h4>
            <form @submit.prevent="addCapability" class="teachers-view__form">
              <select
                v-model="newCapability.subject_id"
                class="teachers-view__input"
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
              <select
                v-model="newCapability.class_group_id"
                class="teachers-view__input"
              >
                <option :value="null">All Classes (or select specific class)</option>
                <option
                  v-for="classGroup in classes"
                  :key="classGroup.id"
                  :value="classGroup.id"
                >
                  {{ classGroup.name }}
                </option>
              </select>
              <button type="submit" class="teachers-view__button" :disabled="loading">
                Add Specialization
              </button>
            </form>
          </div>
          <div class="teachers-view__capabilities-section">
            <h4>Current Specializations</h4>
            <div v-if="teacherCapabilities.length > 0" class="teachers-view__capabilities-list">
              <div
                v-for="capability in teacherCapabilities"
                :key="capability.id"
                class="teachers-view__capability-item"
              >
                <span class="teachers-view__capability-subject">
                  {{ getSubjectName(capability.subject_id) }}
                </span>
                <span v-if="capability.class_group_id" class="teachers-view__capability-class">
                  (Class: {{ getClassName(capability.class_group_id) }})
                </span>
                <button
                  @click="removeCapability(capability.id)"
                  class="teachers-view__capability-remove"
                  :disabled="loading"
                >
                  Remove
                </button>
              </div>
            </div>
            <div v-else class="teachers-view__empty">No specializations yet</div>
          </div>
          <div class="teachers-view__modal-actions">
            <button
              type="button"
              @click="managingCapabilities = null"
              class="teachers-view__button teachers-view__button--secondary"
            >
              Close
            </button>
          </div>
        </div>
      </div>

      <div v-if="error" class="teachers-view__error">{{ error }}</div>
      <div v-if="success" class="teachers-view__success">{{ success }}</div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import api from '@/services/api'

interface Teacher {
  id: number
  full_name: string
  max_weekly_hours: number
  availability: Record<string, number[]> | null
  school_id: number
  capabilities?: TeacherCapability[]
}

interface Subject {
  id: number
  name: string
}

interface ClassGroup {
  id: number
  name: string
}

interface TeacherCapability {
  id: number
  teacher_id: number
  subject_id: number
  class_group_id: number | null
}

const authStore = useAuthStore()
const teachers = ref<Teacher[]>([])
const subjects = ref<Subject[]>([])
const classes = ref<ClassGroup[]>([])
const loading = ref(false)
const error = ref('')
const success = ref('')
const editingTeacher = ref<Teacher | null>(null)
const managingCapabilities = ref<Teacher | null>(null)
const teacherCapabilities = ref<TeacherCapability[]>([])

const newTeacher = ref({
  full_name: '',
  max_weekly_hours: 20,
  availability: null as Record<string, number[]> | null
})

const newCapability = ref({
  subject_id: null as number | null,
  class_group_id: null as number | null
})

const availabilityInput = ref('')
const editAvailabilityInput = ref('')

function parseAvailability(input: string): Record<string, number[]> | null {
  if (!input.trim()) return null
  const result: Record<string, number[]> = {}
  const parts = input.split(/\s+/)
  for (const part of parts) {
    const [day, hours] = part.split(':')
    if (day && hours) {
      result[day.trim()] = hours.split(',').map(h => parseInt(h.trim())).filter(h => !isNaN(h))
    }
  }
  return Object.keys(result).length > 0 ? result : null
}

function formatAvailability(availability: Record<string, number[]> | null): string {
  if (!availability) return ''
  return Object.entries(availability)
    .map(([day, hours]) => `${day}:${hours.join(',')}`)
    .join(' ')
}

// Removed unused computed - using direct assignment instead

async function loadTeachers() {
  try {
    const schoolId = authStore.user?.school_id
    if (!schoolId) return
    
    const response = await api.get(`/teachers/schools/${schoolId}/teachers`)
    teachers.value = response.data
    
    // Load capabilities for each teacher
    for (const teacher of teachers.value) {
      try {
        const capsResponse = await api.get(`/teachers/schools/${schoolId}/teachers/${teacher.id}/capabilities`)
        teacher.capabilities = capsResponse.data
      } catch (err: any) {
        teacher.capabilities = []
      }
    }
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to load teachers'
  }
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

async function loadClasses() {
  try {
    const response = await api.get('/class-groups/')
    classes.value = response.data
  } catch (err: any) {
    console.error('Failed to load classes:', err)
  }
}

async function createTeacher() {
  loading.value = true
  error.value = ''
  success.value = ''
  
  try {
    const schoolId = authStore.user?.school_id
    if (!schoolId) {
      throw new Error('School ID not found')
    }
    
    const teacherData = {
      ...newTeacher.value,
      availability: parseAvailability(availabilityInput.value)
    }
    
    await api.post(`/teachers/schools/${schoolId}/teachers`, teacherData)
    success.value = 'Teacher created successfully'
    newTeacher.value = { full_name: '', max_weekly_hours: 20, availability: null }
    availabilityInput.value = ''
    await loadTeachers()
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to create teacher'
  } finally {
    loading.value = false
  }
}

function editTeacher(teacher: Teacher) {
  editingTeacher.value = { ...teacher }
  editAvailabilityInput.value = formatAvailability(teacher.availability)
}

async function updateTeacher() {
  if (!editingTeacher.value) return
  
  loading.value = true
  error.value = ''
  success.value = ''
  
  try {
    const schoolId = authStore.user?.school_id
    if (!schoolId) {
      throw new Error('School ID not found')
    }
    
    const updateData = {
      full_name: editingTeacher.value.full_name,
      max_weekly_hours: editingTeacher.value.max_weekly_hours,
      availability: editingTeacher.value.availability
    }
    
    await api.put(`/teachers/schools/${schoolId}/teachers/${editingTeacher.value.id}`, updateData)
    success.value = 'Teacher updated successfully'
    editingTeacher.value = null
    await loadTeachers()
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to update teacher'
  } finally {
    loading.value = false
  }
}

async function manageCapabilities(teacher: Teacher) {
  managingCapabilities.value = teacher
  await loadTeacherCapabilities(teacher.id)
}

async function loadTeacherCapabilities(teacherId: number) {
  try {
    const schoolId = authStore.user?.school_id
    if (!schoolId) return
    
    const response = await api.get(`/teachers/schools/${schoolId}/teachers/${teacherId}/capabilities`)
    teacherCapabilities.value = response.data
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to load capabilities'
  }
}

async function addCapability() {
  if (!managingCapabilities.value || !newCapability.value.subject_id) return
  
  loading.value = true
  error.value = ''
  success.value = ''
  
  try {
    const schoolId = authStore.user?.school_id
    if (!schoolId) {
      throw new Error('School ID not found')
    }
    
    await api.post(
      `/teachers/schools/${schoolId}/teachers/${managingCapabilities.value.id}/capabilities`,
      {
        teacher_id: managingCapabilities.value.id,
        subject_id: newCapability.value.subject_id,
        class_group_id: newCapability.value.class_group_id || null
      }
    )
    success.value = 'Capability added successfully'
    newCapability.value = { subject_id: null, class_group_id: null }
    await loadTeacherCapabilities(managingCapabilities.value.id)
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to add capability'
  } finally {
    loading.value = false
  }
}

async function removeCapability(capabilityId: number) {
  if (!managingCapabilities.value) return
  
  loading.value = true
  error.value = ''
  success.value = ''
  
  try {
    const schoolId = authStore.user?.school_id
    if (!schoolId) {
      throw new Error('School ID not found')
    }
    
    await api.delete(
      `/teachers/schools/${schoolId}/teachers/${managingCapabilities.value.id}/capabilities/${capabilityId}`
    )
    success.value = 'Capability removed successfully'
    await loadTeacherCapabilities(managingCapabilities.value.id)
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to remove capability'
  } finally {
    loading.value = false
  }
}

function getSubjectName(subjectId: number): string {
  const subject = subjects.value.find(s => s.id === subjectId)
  return subject ? subject.name : 'Unknown'
}

function getClassName(classGroupId: number): string {
  const classGroup = classes.value.find(c => c.id === classGroupId)
  return classGroup ? classGroup.name : 'Unknown'
}

function getTeacherSubjects(capabilities: TeacherCapability[]): string {
  const subjectIds = [...new Set(capabilities.map(c => c.subject_id))]
  return subjectIds
    .map(id => getSubjectName(id))
    .join(', ')
}

async function deleteTeacher(teacherId: number) {
  if (!confirm('Are you sure you want to delete this teacher?')) {
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
    
    await api.delete(`/teachers/schools/${schoolId}/teachers/${teacherId}`)
    success.value = 'Teacher deleted successfully'
    await loadTeachers()
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to delete teacher'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadTeachers()
  loadSubjects()
  loadClasses()
})
</script>

<style lang="scss" scoped>
.teachers-view {
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
    margin-top: -0.5rem;
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
      gap: 0.25rem;
    }

    &-name {
      font-weight: 600;
      color: #333;
    }

    &-hours {
      color: #666;
      font-size: 0.875rem;
    }

    &-subjects {
      color: #4a90e2;
      font-size: 0.875rem;
      margin-top: 0.25rem;
      font-weight: 500;
    }

    &-no-subjects {
      color: #999;
      font-size: 0.875rem;
      margin-top: 0.25rem;
      font-style: italic;
    }

    &-actions {
      display: flex;
      gap: 0.5rem;
    }
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

  &__capabilities {
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

  &__capabilities-section {
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

  &__capabilities-list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  &__capability-item {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 0.75rem;
    background-color: #f8f9fa;
    border-radius: 4px;
    border: 1px solid #dee2e6;
  }

  &__capability-subject {
    font-weight: 600;
    color: #333;
  }

  &__capability-class {
    color: #666;
    font-size: 0.875rem;
  }

  &__capability-remove {
    margin-left: auto;
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

