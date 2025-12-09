<template>
  <div class="classes-view">
    <header class="classes-view__header">
      <h1 class="classes-view__title">Classes</h1>
      <router-link to="/dashboard" class="classes-view__back">Dashboard</router-link>
    </header>
    <main class="classes-view__content">
      <!-- Class Filter -->
      <div class="classes-view__section">
        <h2>Select Class</h2>
        <select
          v-model="selectedClassId"
          class="classes-view__filter"
          @change="onClassChange"
        >
          <option :value="null">Select a class...</option>
          <option
            v-for="classItem in classes"
            :key="classItem.id"
            :value="classItem.id"
          >
            {{ classItem.name }}
          </option>
        </select>
      </div>

      <!-- Class Details -->
      <div v-if="selectedClassId" class="classes-view__details">
        <!-- Timetable Section -->
        <div class="classes-view__section">
          <h2>Timetable</h2>
          <div v-if="loadingTimetable" class="classes-view__loading">Loading timetable...</div>
          <div v-else-if="primaryTimetable && classTimetableEntries.length > 0" class="classes-view__timetable-wrapper">
            <TimetableGrid
              :timetable="{ ...primaryTimetable, entries: classTimetableEntries }"
              :lunch-hours="actualLunchHours"
            />
          </div>
          <div v-else class="classes-view__empty">No timetable available for this class</div>
        </div>

        <!-- Subjects Section -->
        <div class="classes-view__section">
          <h2>Subjects</h2>
          <div v-if="classAllocations.length > 0" class="classes-view__subjects-list">
            <div
              v-for="allocation in classAllocations"
              :key="allocation.id"
              class="classes-view__subject-item"
            >
              <div class="classes-view__subject-info">
                <span class="classes-view__subject-name">{{ getSubjectName(allocation.subject_id) }}</span>
                <span class="classes-view__subject-hours">{{ allocation.weekly_hours }} hours/week</span>
              </div>
              <div class="classes-view__subject-teachers">
                <strong>Teachers:</strong>
                <span v-if="getTeachersForSubject(allocation.subject_id).length > 0">
                  {{ getTeachersForSubject(allocation.subject_id).map((t: Teacher) => t.full_name).join(', ') }}
                </span>
                <span v-else class="classes-view__no-teachers">No teachers assigned</span>
              </div>
            </div>
          </div>
          <div v-else class="classes-view__empty">No subjects allocated to this class</div>
        </div>

        <!-- Management Section (Admin only) -->
        <div v-if="authStore.user?.role === 'ADMIN'" class="classes-view__section">
          <h2>Manage Class</h2>
          <div class="classes-view__management-actions">
            <button
              @click="showSubjectModal = true"
              class="classes-view__button"
            >
              Manage Subjects
            </button>
          </div>
        </div>
      </div>

      <!-- Subject Management Modal -->
      <div v-if="showSubjectModal && selectedClassId" class="classes-view__modal">
        <div class="classes-view__modal-content classes-view__modal-content--large">
          <h3>Manage Subject Allocations for {{ getSelectedClassName() }}</h3>
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
              @click="showSubjectModal = false"
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
import { ref, onMounted, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import api from '@/services/api'
import TimetableGrid from '@/components/TimetableGrid.vue'

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

interface Teacher {
  id: number
  full_name: string
  capabilities?: any[]
}

interface Timetable {
  id: number
  name: string
  entries: any[]
  is_primary?: number
}

const authStore = useAuthStore()
const classes = ref<ClassGroup[]>([])
const subjects = ref<Subject[]>([])
const teachers = ref<Teacher[]>([])
const selectedClassId = ref<number | null>(null)
const loading = ref(false)
const loadingTimetable = ref(false)
const error = ref('')
const success = ref('')
const showSubjectModal = ref(false)
const classAllocations = ref<SubjectAllocation[]>([])
const editingAllocation = ref<SubjectAllocation | null>(null)
const primaryTimetable = ref<Timetable | null>(null)
const schoolSettings = ref<any>(null)

const newAllocation = ref({
  subject_id: null as number | null,
  weekly_hours: 1
})

const classTimetableEntries = computed(() => {
  if (!primaryTimetable.value || !selectedClassId.value) return []
  return primaryTimetable.value.entries.filter(
    (entry: any) => entry.class_group_id === selectedClassId.value
  )
})

const actualLunchHours = computed(() => {
  if (!schoolSettings.value?.possible_lunch_hours || !schoolSettings.value?.lunch_duration_minutes || !schoolSettings.value?.class_hour_length_minutes) {
    return []
  }
  
  const lunchHoursCount = Math.ceil(schoolSettings.value.lunch_duration_minutes / schoolSettings.value.class_hour_length_minutes)
  const possibleHours = [...schoolSettings.value.possible_lunch_hours].sort((a, b) => a - b)
  
  for (let i = 0; i <= possibleHours.length - lunchHoursCount; i++) {
    const consecutive = possibleHours.slice(i, i + lunchHoursCount)
    const isConsecutive = consecutive.every((hour, idx) => hour === consecutive[0] + idx)
    if (isConsecutive) {
      return consecutive
    }
  }
  
  return possibleHours.slice(0, lunchHoursCount)
})

function getSelectedClassName(): string {
  const classItem = classes.value.find(c => c.id === selectedClassId.value)
  return classItem ? classItem.name : ''
}

function getSubjectName(subjectId: number): string {
  const subject = subjects.value.find(s => s.id === subjectId)
  return subject ? subject.name : 'Unknown'
}

function getTeachersForSubject(subjectId: number): Teacher[] {
  return teachers.value.filter(teacher => {
    if (!teacher.capabilities) return false
    return teacher.capabilities.some((cap: any) => 
      cap.subject_id === subjectId && 
      (cap.class_group_id === selectedClassId.value || cap.class_group_id === null)
    )
  })
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
    const schoolId = authStore.user?.school_id
    if (!schoolId) return
    
    const response = await api.get(`/subjects/schools/${schoolId}/subjects`)
    subjects.value = response.data
  } catch (err: any) {
    console.error('Failed to load subjects:', err)
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

async function loadSchoolSettings() {
  try {
    const schoolId = authStore.user?.school_id
    if (!schoolId) return
    
    const response = await api.get(`/schools/${schoolId}/settings`)
    schoolSettings.value = response.data
  } catch (err: any) {
    console.error('Failed to load school settings:', err)
  }
}

async function loadClassAllocations() {
  if (!selectedClassId.value) return
  
  try {
    const response = await api.get(`/subjects/class-subject-allocations?class_group_id=${selectedClassId.value}`)
    classAllocations.value = response.data
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to load allocations'
  }
}

async function loadPrimaryTimetable() {
  if (!selectedClassId.value) return
  
  loadingTimetable.value = true
  try {
    const schoolId = authStore.user?.school_id
    if (!schoolId) return
    
    // Get all timetables and find the primary one
    const response = await api.get(`/timetables/schools/${schoolId}/timetables`)
    const timetables = response.data
    
    // Find primary timetable (is_primary === 1)
    const primary = timetables.find((t: any) => t.is_primary === 1)
    
    if (primary) {
      // Get full timetable with entries
      const fullResponse = await api.get(`/timetables/schools/${schoolId}/timetables/${primary.id}`)
      primaryTimetable.value = fullResponse.data
    } else {
      primaryTimetable.value = null
    }
  } catch (err: any) {
    console.error('Failed to load timetable:', err)
    primaryTimetable.value = null
  } finally {
    loadingTimetable.value = false
  }
}

async function onClassChange() {
  if (selectedClassId.value) {
    await loadClassAllocations()
    await loadPrimaryTimetable()
  } else {
    classAllocations.value = []
    primaryTimetable.value = null
  }
}

async function addAllocation() {
  if (!selectedClassId.value || !newAllocation.value.subject_id) return
  
  loading.value = true
  error.value = ''
  success.value = ''
  
  try {
    await api.post('/subjects/class-subject-allocations', {
      class_group_id: selectedClassId.value,
      subject_id: newAllocation.value.subject_id,
      weekly_hours: newAllocation.value.weekly_hours
    })
    success.value = 'Allocation added successfully'
    newAllocation.value = { subject_id: null, weekly_hours: 1 }
    await loadClassAllocations()
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
    await loadClassAllocations()
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
    await loadClassAllocations()
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to remove allocation'
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await loadClasses()
  await loadSubjects()
  await loadTeachers()
  await loadSchoolSettings()
})
</script>

<style lang="scss" scoped>
@import '../styles/neo.scss';

.classes-view {
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
  }

  &__content {
    padding: 2rem;
    max-width: 1400px;
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

  &__filter {
    @extend %neo-input;
    width: 100%;
    max-width: 400px;
    padding: 0.75rem;
    border-radius: 12px;
    font-size: 1rem;
  }

  &__details {
    display: flex;
    flex-direction: column;
    gap: 2rem;
  }

  &__timetable-wrapper {
    overflow-x: auto;
  }

  &__subjects-list {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  &__subject-item {
    @extend %neo-list-item;
    padding: 1rem;
    margin-bottom: 0.5rem;
  }

  &__subject-info {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.5rem;
  }

  &__subject-name {
    font-weight: 600;
    color: $neo-text;
    font-size: 1.1rem;
  }

  &__subject-hours {
    color: $neo-text;
    font-weight: 600;
  }

  &__subject-teachers {
    color: $neo-text-light;
    font-size: 0.9rem;
  }

  &__no-teachers {
    color: $neo-text-muted;
    font-style: italic;
  }

  &__management-actions {
    display: flex;
    gap: 1rem;
  }

  &__form {
    display: flex;
    gap: 1rem;
    margin-bottom: 2rem;
    flex-wrap: wrap;
  }

  &__input {
    @extend %neo-input;
    flex: 1;
    min-width: 200px;
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
    white-space: nowrap;
    font-weight: 600;

    &:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }

    &--secondary {
      @extend %neo-button--secondary;
    }
  }

  &__loading {
    text-align: center;
    padding: 2rem;
    color: $neo-text-light;
  }

  &__empty {
    padding: 2rem;
    text-align: center;
    color: $neo-text-muted;
    font-style: italic;
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

    &--large {
      max-width: 700px;
    }

    h3, h4 {
      color: $neo-text;
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
    border-bottom: 1px solid rgba(0, 0, 0, 0.05);

    &:last-child {
      border-bottom: none;
    }

    h4 {
      margin-bottom: 1rem;
      color: $neo-text;
    }
  }

  &__allocations-list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  &__allocation-item {
    @extend %neo-list-item;
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 0.75rem;
  }

  &__allocation-subject {
    font-weight: 600;
    color: $neo-text;
    flex: 1;
    
  }

  &__allocation-hours {
    color: $neo-text;
    font-weight: 600;
  }

  &__allocation-edit,
  &__allocation-remove {
    @extend %neo-button;
    padding: 0.25rem 0.75rem;
    border-radius: 8px;
    cursor: pointer;
    font-size: 0.875rem;
    font-weight: 600;

    &:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
  }

  &__allocation-edit {
    @extend %neo-button--warning;
  }

  &__allocation-remove {
    background: lighten(#dc3545, 35%);
    border-color: lighten(#dc3545, 35%);

    &:hover:not(:disabled) {
      background: lighten(#dc3545, 35%);
      border-color: lighten(#dc3545, 35%);
    }

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
