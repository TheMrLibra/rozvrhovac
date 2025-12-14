<template>
  <div class="classes-view">
    <header class="classes-view__header">
      <h1 class="classes-view__title">{{ t('classes.title') }}</h1>
      <div class="classes-view__header-center">
        <select
          v-model="selectedClassId"
          class="classes-view__filter"
          @change="onClassChange"
        >
          <option :value="null">{{ t('classes.selectAClass') }}</option>
          <option
            v-for="classItem in classes"
            :key="classItem.id"
            :value="classItem.id"
          >
            {{ classItem.name }}
          </option>
        </select>
      </div>
      <div class="classes-view__header-actions">
        <button
          @click="showCreateClassModal = true"
          class="classes-view__button"
        >
          {{ t('classes.addClass') }}
        </button>
        <router-link to="/dashboard" class="classes-view__back">{{ t('classes.back') }}</router-link>
      </div>
    </header>
    <main class="classes-view__content">        
      <!-- Class Details -->
      <div v-if="selectedClassId" class="classes-view__details">
        <!-- Timetable Section -->
        <div class="classes-view__section">
          <h2>{{ t('classes.timetable') }}</h2>
          <div v-if="loadingTimetable" class="classes-view__loading">{{ t('classes.loadingTimetable') }}</div>
          <div v-else-if="primaryTimetable && classTimetableEntries.length > 0" class="classes-view__timetable-wrapper">
            <TimetableGrid
              :timetable="{ ...primaryTimetable, entries: classTimetableEntries }"
              :lunch-hours="actualLunchHours"
            />
          </div>
          <div v-else class="classes-view__empty">{{ t('classes.noTimetableAvailable') }}</div>
        </div>

        <!-- Subjects Section -->
        <div class="classes-view__section">
          <h2>{{ t('classes.subjects') }}</h2>
          <div v-if="sortedClassAllocations.length > 0" class="classes-view__subjects-list">
            <div
              v-for="allocation in sortedClassAllocations"
              :key="allocation.id"
              class="classes-view__subject-item"
            >
              <div class="classes-view__subject-info">
                <span class="classes-view__subject-name">{{ getSubjectName(allocation.subject_id) }}</span>
                <span class="classes-view__subject-teacher">
                  <span v-if="allocation.primary_teacher">
                    {{ allocation.primary_teacher.full_name }}
                  </span>
                  <span v-else class="classes-view__no-teacher">{{ t('classes.noPrimaryTeacher') }}</span>
                </span>
                <span class="classes-view__subject-hours">{{ allocation.weekly_hours }} {{ t('classes.hoursPerWeek') }}</span>
              </div>
              <button
                @click="editAllocation(allocation)"
                class="classes-view__button classes-view__button--edit"
              >
                {{ t('common.edit') }}
              </button>
            </div>
          </div>
          <div v-else class="classes-view__empty">{{ t('classes.noSubjectsAllocated') }}</div>

           <button
              v-if="authStore.user?.role === 'ADMIN'"
              @click="showSubjectModal = true"
              class="classes-view__button"
            >
              {{ t('classes.manageSubjects') }}
          </button>
        </div>

        <!-- Class Info Section -->
        <div v-if="authStore.user?.role === 'ADMIN'" class="classes-view__section">
          <h2>{{ t('classes.classInformation') }}</h2>
          <div v-if="selectedClass" class="classes-view__class-info">
            <div class="classes-view__info-item">
              <label class="classes-view__info-label">{{ t('classes.numberOfStudents') }}:</label>
              <input
                v-model.number="numberOfStudentsInput"
                type="number"
                min="1"
                class="classes-view__input classes-view__input--inline"
                :placeholder="t('classes.enterNumberOfStudents')"
              />
              <button
                @click="updateClassInfo"
                class="classes-view__button classes-view__button--save"
                :disabled="loading"
              >
                {{ t('common.save') }}
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Subject Management Modal -->
      <div v-if="showSubjectModal && selectedClassId" class="classes-view__modal">
        <div class="classes-view__modal-content classes-view__modal-content--large">
          <h3>{{ t('classes.manageSubjectAllocations') }} {{ getSelectedClassName() }}</h3>
          <div class="classes-view__allocations-section">
            <h4>{{ t('classes.addSubjectAllocation') }}</h4>
            <form @submit.prevent="addAllocation" class="classes-view__form">
              <select
                v-model="newAllocation.subject_id"
                class="classes-view__input"
                required
              >
                <option value="">{{ t('classes.selectSubject') }}</option>
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
                :placeholder="t('classes.hoursPerWeekPlaceholder')"
                min="1"
                class="classes-view__input"
                required
              />
              <select
                v-model="newAllocation.primary_teacher_id"
                class="classes-view__input"
              >
                <option :value="null">{{ t('classes.selectPrimaryTeacher') }}</option>
                <option
                  v-for="teacher in getTeachersForSubject(newAllocation.subject_id || 0)"
                  :key="teacher.id"
                  :value="teacher.id"
                >
                  {{ teacher.full_name }}
                </option>
              </select>
              <label class="classes-view__checkbox-label">
                <input
                  v-model="newAllocation.allow_multiple_in_one_day"
                  type="checkbox"
                  class="classes-view__checkbox"
                  @change="handleMultipleInOneDayChange(false)"
                />
                {{ t('classes.allowMultipleInOneDay') }}
              </label>
              <div v-if="newAllocation.allow_multiple_in_one_day" class="classes-view__form-group">
                <label class="classes-view__label">{{ t('classes.requiredConsecutiveHours') }}</label>
                <input
                  v-model.number="newAllocation.required_consecutive_hours"
                  type="number"
                  :placeholder="t('classes.requiredConsecutiveHoursPlaceholder')"
                  min="1"
                  class="classes-view__input"
                />
              </div>
              <button type="submit" class="classes-view__button" :disabled="loading">
                {{ t('classes.addAllocation') }}
              </button>
            </form>
          </div>
          <div class="classes-view__allocations-section">
            <h4>{{ t('classes.currentSubjectAllocations') }}</h4>
            <div v-if="sortedClassAllocations.length > 0" class="classes-view__allocations-list">
              <div
                v-for="allocation in sortedClassAllocations"
                :key="allocation.id"
                class="classes-view__allocation-item"
              >
                <span class="classes-view__allocation-subject">
                  {{ getSubjectName(allocation.subject_id) }}
                </span>
                <span class="classes-view__allocation-hours">
                  {{ allocation.weekly_hours }} {{ t('classes.hoursPerWeek') }}
                </span>
                <span v-if="allocation.primary_teacher" class="classes-view__allocation-teacher">
                  {{ t('classes.primary') }}: {{ allocation.primary_teacher.full_name }}
                </span>
                <span v-else class="classes-view__allocation-teacher classes-view__allocation-teacher--none">
                  {{ t('classes.noPrimaryTeacher') }}
                </span>
                <button
                  @click="editAllocation(allocation)"
                  class="classes-view__allocation-edit"
                  :disabled="loading"
                >
                  {{ t('common.edit') }}
                </button>
                <button
                  @click="removeAllocation(allocation.id)"
                  class="classes-view__allocation-remove"
                  :disabled="loading"
                >
                  {{ t('classes.removeAllocation') }}
                </button>
              </div>
            </div>
            <div v-else class="classes-view__empty">{{ t('classes.noSubjectAllocationsYet') }}</div>
          </div>
          <div class="classes-view__modal-actions">
            <button
              type="button"
              @click="showSubjectModal = false"
              class="classes-view__button classes-view__button--secondary"
            >
              {{ t('common.close') }}
            </button>
          </div>
        </div>
      </div>

      <!-- Create Class Modal -->
      <div v-if="showCreateClassModal" class="classes-view__modal">
        <div class="classes-view__modal-content">
          <h3>{{ t('classes.addNewClass') }}</h3>
          <form @submit.prevent="createClass" class="classes-view__form">
            <div class="classes-view__form-group">
              <label class="classes-view__label">{{ t('classes.className') }}</label>
              <input
                v-model="newClass.name"
                type="text"
                :placeholder="t('classes.classNamePlaceholder')"
                class="classes-view__input"
                required
              />
            </div>
            <div class="classes-view__form-group">
              <label class="classes-view__label">{{ t('classes.gradeLevel') }}</label>
              <select
                v-model="newClass.grade_level_id"
                class="classes-view__input"
                required
              >
                <option value="">{{ t('classes.selectGradeLevel') }}</option>
                <option
                  v-for="gradeLevel in gradeLevels"
                  :key="gradeLevel.id"
                  :value="gradeLevel.id"
                >
                  {{ gradeLevel.name }}
                </option>
              </select>
            </div>
            <div class="classes-view__modal-actions">
              <button type="submit" class="classes-view__button" :disabled="loading">
                {{ t('classes.createClass') }}
              </button>
              <button
                type="button"
                @click="showCreateClassModal = false; resetNewClass()"
                class="classes-view__button classes-view__button--secondary"
              >
                {{ t('common.cancel') }}
              </button>
            </div>
          </form>
        </div>
      </div>

      <!-- Edit Allocation Modal -->
      <div v-if="editingAllocation" class="classes-view__modal">
        <div class="classes-view__modal-content">
          <h3>{{ t('classes.editSubjectAllocation') }}</h3>
          <form @submit.prevent="updateAllocation" class="classes-view__form">
            <input
              v-model.number="editingAllocation.weekly_hours"
              type="number"
              :placeholder="t('classes.hoursPerWeekPlaceholder')"
              min="1"
              class="classes-view__input"
              required
            />
            <select
              v-model="editingAllocation.primary_teacher_id"
              class="classes-view__input"
            >
              <option :value="null">{{ t('classes.selectPrimaryTeacher') }}</option>
              <option
                v-for="teacher in getTeachersForSubject(editingAllocation.subject_id)"
                :key="teacher.id"
                :value="teacher.id"
              >
                {{ teacher.full_name }}
              </option>
            </select>
            <label class="classes-view__checkbox-label">
              <input
                v-model="editingAllocation.allow_multiple_in_one_day"
                type="checkbox"
                class="classes-view__checkbox"
                @change="handleMultipleInOneDayChange(true)"
              />
              {{ t('classes.allowMultipleInOneDay') }}
            </label>
            <div v-if="editingAllocation.allow_multiple_in_one_day" class="classes-view__form-group">
              <label class="classes-view__label">{{ t('classes.requiredConsecutiveHours') }}</label>
              <input
                v-model.number="editingAllocation.required_consecutive_hours"
                type="number"
                :placeholder="t('classes.requiredConsecutiveHoursPlaceholder')"
                min="1"
                class="classes-view__input"
              />
            </div>
            <div class="classes-view__modal-actions">
              <button type="submit" class="classes-view__button" :disabled="loading">
                {{ t('common.save') }}
              </button>
              <button
                type="button"
                @click="editingAllocation = null"
                class="classes-view__button classes-view__button--secondary"
              >
                {{ t('common.cancel') }}
              </button>
            </div>
          </form>
        </div>
      </div>

    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useI18nStore } from '@/stores/i18n'
import { useAlert } from '@/composables/useAlert'
import api from '@/services/api'
import TimetableGrid from '@/components/TimetableGrid.vue'

const authStore = useAuthStore()
const i18nStore = useI18nStore()
const t = i18nStore.t
const alert = useAlert()

interface ClassGroup {
  id: number
  name: string
  grade_level_id: number
  school_id: number
  number_of_students?: number | null
}

interface GradeLevel {
  id: number
  name: string
  level?: number | null
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
  primary_teacher_id?: number | null
  allow_multiple_in_one_day?: boolean | null
  required_consecutive_hours?: number | null
  primary_teacher?: {
    id: number
    full_name: string
  } | null
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
  class_lunch_hours?: { [classId: number]: { [day: number]: number[] } }
}

const classes = ref<ClassGroup[]>([])
const gradeLevels = ref<GradeLevel[]>([])
const subjects = ref<Subject[]>([])
const teachers = ref<Teacher[]>([])
const selectedClassId = ref<number | null>(null)
const loading = ref(false)
const loadingTimetable = ref(false)
const showSubjectModal = ref(false)
const showCreateClassModal = ref(false)
const classAllocations = ref<SubjectAllocation[]>([])
const editingAllocation = ref<SubjectAllocation | null>(null)
const primaryTimetable = ref<Timetable | null>(null)
const schoolSettings = ref<any>(null)

const newClass = ref({
  name: '',
  grade_level_id: null as number | null
})

const selectedClass = computed(() => {
  return classes.value.find(c => c.id === selectedClassId.value) || null
})

const numberOfStudentsInput = ref<number | null>(null)

// Watch selectedClass to update the input value
watch(selectedClass, (newClass: ClassGroup | null) => {
  if (newClass) {
    numberOfStudentsInput.value = newClass.number_of_students || null
  } else {
    numberOfStudentsInput.value = null
  }
}, { immediate: true })

const sortedClassAllocations = computed(() => {
  return [...classAllocations.value].sort((a, b) => {
    const nameA = getSubjectName(a.subject_id).toLowerCase()
    const nameB = getSubjectName(b.subject_id).toLowerCase()
    return nameA.localeCompare(nameB)
  })
})

const newAllocation = ref({
  subject_id: null as number | null,
  weekly_hours: 1,
  primary_teacher_id: null as number | null,
  allow_multiple_in_one_day: null as boolean | null,
  required_consecutive_hours: null as number | null
})

const classTimetableEntries = computed(() => {
  if (!primaryTimetable.value || !selectedClassId.value) return []
  return primaryTimetable.value.entries.filter(
    (entry: any) => entry.class_group_id === selectedClassId.value
  )
})

// Get lunch hours for the selected class from timetable data (per day)
const actualLunchHours = computed(() => {
  if (!primaryTimetable.value?.class_lunch_hours || !selectedClassId.value) {
    return {}
  }
  
  // Get lunch hours per day for the selected class from the timetable response
  // Structure: { day: [lunch_hours] } where day is 0-4 (Monday-Friday)
  return primaryTimetable.value.class_lunch_hours[selectedClassId.value] || {}
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
    console.error('Failed to load classes:', err)
  }
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
    console.error('Failed to load allocations:', err)
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

async function updateClassInfo() {
  if (!selectedClass.value) return
  
  loading.value = true
  try {
    await api.put(`/class-groups/${selectedClass.value.id}`, {
      number_of_students: numberOfStudentsInput.value || null
    })
    alert.success('Class information updated successfully')
    // Reload classes to ensure sync
    await loadClasses()
    // Ensure selected class is still selected after reload
    if (selectedClassId.value) {
      const index = classes.value.findIndex(c => c.id === selectedClassId.value)
      if (index !== -1) {
        classes.value[index] = { ...classes.value[index], number_of_students: numberOfStudentsInput.value }
      }
    }
  } catch (err: any) {
    console.error('Failed to update class info:', err)
    alert.error(err.response?.data?.detail || 'Failed to update class information')
    // Reload to revert changes and reset input
    await loadClasses()
    if (selectedClass.value) {
      numberOfStudentsInput.value = selectedClass.value.number_of_students || null
    }
  } finally {
    loading.value = false
  }
}

function resetNewClass() {
  newClass.value = {
    name: '',
    grade_level_id: null
  }
}

async function createClass() {
  if (!newClass.value.name || !newClass.value.grade_level_id) return
  
  loading.value = true
  
  try {
    const classData = {
      name: newClass.value.name,
      grade_level_id: newClass.value.grade_level_id
    }
    
    const response = await api.post('/class-groups/', classData)
    alert.success('Class created successfully')
    showCreateClassModal.value = false
    resetNewClass()
    
    // Reload classes to get fresh data
    await loadClasses()
    
    // Auto-select the newly created class
    if (response.data?.id) {
      selectedClassId.value = response.data.id
      // Ensure the class data is updated in the array with the response data
      const index = classes.value.findIndex(c => c.id === response.data.id)
      if (index !== -1 && response.data.number_of_students !== undefined) {
        classes.value[index] = { ...classes.value[index], ...response.data }
      }
      await onClassChange()
    }
  } catch (err: any) {
    alert.error(err.response?.data?.detail || 'Failed to create class')
  } finally {
    loading.value = false
  }
}

async function addAllocation() {
  if (!selectedClassId.value || !newAllocation.value.subject_id) return
  
  loading.value = true
  
  try {
    await api.post('/subjects/class-subject-allocations', {
      class_group_id: selectedClassId.value,
      subject_id: newAllocation.value.subject_id,
      weekly_hours: newAllocation.value.weekly_hours,
      primary_teacher_id: newAllocation.value.primary_teacher_id || null,
      allow_multiple_in_one_day: newAllocation.value.allow_multiple_in_one_day,
      required_consecutive_hours: newAllocation.value.required_consecutive_hours || null
    })
    alert.success('Allocation added successfully')
    newAllocation.value = { subject_id: null, weekly_hours: 1, primary_teacher_id: null, allow_multiple_in_one_day: null, required_consecutive_hours: null }
    await loadClassAllocations()
  } catch (err: any) {
    alert.error(err.response?.data?.detail || 'Failed to add allocation')
  } finally {
    loading.value = false
  }
}

function editAllocation(allocation: SubjectAllocation) {
  editingAllocation.value = { ...allocation }
}

function handleMultipleInOneDayChange(isEditing: boolean) {
  if (isEditing && editingAllocation.value) {
    if (!editingAllocation.value.allow_multiple_in_one_day) {
      editingAllocation.value.required_consecutive_hours = null
    }
  } else {
    if (!newAllocation.value.allow_multiple_in_one_day) {
      newAllocation.value.required_consecutive_hours = null
    }
  }
}

async function updateAllocation() {
  if (!editingAllocation.value) return
  
  loading.value = true
  
  try {
    await api.put(`/subjects/class-subject-allocations/${editingAllocation.value.id}`, {
      weekly_hours: editingAllocation.value.weekly_hours,
      primary_teacher_id: editingAllocation.value.primary_teacher_id || null,
      allow_multiple_in_one_day: editingAllocation.value.allow_multiple_in_one_day,
      required_consecutive_hours: editingAllocation.value.required_consecutive_hours || null
    })
    alert.success('Allocation updated successfully')
    editingAllocation.value = null
    await loadClassAllocations()
  } catch (err: any) {
    alert.error(err.response?.data?.detail || 'Failed to update allocation')
  } finally {
    loading.value = false
  }
}

async function removeAllocation(allocationId: number) {
  if (!confirm('Are you sure you want to remove this allocation?')) {
    return
  }
  
  loading.value = true
  
  try {
    await api.delete(`/subjects/class-subject-allocations/${allocationId}`)
    alert.success('Allocation removed successfully')
    await loadClassAllocations()
  } catch (err: any) {
    alert.error(err.response?.data?.detail || 'Failed to remove allocation')
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await loadClasses()
  await loadGradeLevels()
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
    display: grid;
    grid-template-columns: 1fr auto 1fr;
    align-items: center;
    gap: 1rem;
    position: sticky;
    top: 0;
    z-index: 100;
  }

  &__title {
    color: $neo-text;
    font-size: 1.75rem;
    font-weight: 700;
  }

  &__header-center {
    display: flex;
    justify-content: center;
    width: 100%;
  }

  &__header-actions {
    display: flex;
    gap: 1rem;
    justify-content: flex-end;
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
    max-width: 500px;
    min-width: 300px;
    padding: 0.75rem 2.5rem 0.75rem 0.75rem;
    border-radius: 12px;
    font-size: 1rem;
    appearance: none;
    background-repeat: no-repeat;
    background-position: right 0.75rem center;
    background-size: 12px;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%234a5568' d='M6 9L1 4h10z'/%3E%3C/svg%3E");
    
    &:focus {
      padding: 0.75rem 2.5rem 0.75rem 0.75rem;
      background-color: $neo-bg-base;
      background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%234a5568' d='M6 9L1 4h10z'/%3E%3C/svg%3E");
      background-repeat: no-repeat;
      background-position: right 0.75rem center;
      background-size: 12px;
    }
    
    &:hover:not(:focus) {
      background-color: $neo-bg-base;
      background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%234a5568' d='M6 9L1 4h10z'/%3E%3C/svg%3E");
      background-repeat: no-repeat;
      background-position: right 0.75rem center;
      background-size: 12px;
    }
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
    padding: 1rem 1.5rem;
    margin-bottom: 0.5rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 1rem;
  }

  &__subject-info {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    flex: 1;
  }

  &__subject-name {
    font-weight: 600;
    color: $neo-text;
    font-size: 1.1rem;
  }

  &__subject-teacher {
    color: $neo-text-light;
    font-size: 0.95rem;
  }

  &__no-teacher {
    color: $neo-text-muted;
    font-style: italic;
  }

  &__subject-hours {
    color: $neo-text;
    font-weight: 500;
    font-size: 0.95rem;
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

    &--inline {
      flex: 0 0 auto;
      min-width: 150px;
      max-width: 200px;
    }
  }

  &__class-info {
    @extend %neo-panel;
    padding: 1.5rem;
  }

  &__info-item {
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  &__info-label {
    font-weight: 600;
    color: $neo-text;
    min-width: 150px;
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

    &--edit {
      padding: 0.5rem 1rem;
      font-size: 0.9rem;
    }

    &--save {
      padding: 0.5rem 1rem;
      font-size: 0.9rem;
      margin-left: 0.5rem;
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

  &__form-group {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    margin-bottom: 1rem;
  }

  &__label {
    font-weight: 600;
    color: $neo-text;
    font-size: 0.95rem;
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

  &__allocation-teacher {
    color: $neo-text;
    font-size: 0.9rem;
    opacity: 0.8;

    &--none {
      opacity: 0.5;
      font-style: italic;
    }
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

  &__checkbox-label {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin: 0.75rem 0;
    cursor: pointer;
    color: $neo-text;
    font-size: 0.95rem;
    user-select: none;
  }

  &__checkbox {
    width: 1.5rem;
    height: 1.5rem;
    cursor: pointer;
    appearance: none;
    -webkit-appearance: none;
    -moz-appearance: none;
    @include neo-inset(8px, 0.5);
    background: $neo-bg-light;
    position: relative;
    transition: all 0.3s ease;
    flex-shrink: 0;
    
    &:hover {
      @include neo-inset(8px, 0.7);
      background: $neo-bg-base;
    }
    
    &:checked {
      background: linear-gradient(135deg, $neo-accent 0%, darken($neo-accent, 5%) 100%);
      box-shadow: 
        inset calc(3px) calc(3px) calc(6px) darken($neo-accent, 15%),
        inset calc(-3px) calc(-3px) calc(6px) lighten($neo-accent, 10%);
      
      &::after {
        content: '';
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%) rotate(45deg);
        width: 0.4rem;
        height: 0.7rem;
        border: solid white;
        border-width: 0 2px 2px 0;
        box-shadow: 
          calc(1px) calc(1px) calc(2px) rgba(0, 0, 0, 0.2),
          calc(-1px) calc(-1px) calc(2px) rgba(255, 255, 255, 0.3);
      }
      
      &:hover {
        background: linear-gradient(135deg, $neo-accent-hover 0%, darken($neo-accent-hover, 5%) 100%);
      }
    }
    
    &:focus {
      outline: none;
      @include neo-surface(8px, 0.4);
    }
    
    &:active {
      @include neo-inset(8px, 0.8);
      transform: scale(0.95);
    }
  }
}
</style>
