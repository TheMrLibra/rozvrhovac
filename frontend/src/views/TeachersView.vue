<template>
  <div class="teachers-view">
    <header class="teachers-view__header">
      <h1 class="teachers-view__title">{{ t('teachers.title') }}</h1>
      <router-link to="/dashboard" class="teachers-view__back">{{ t('common.dashboard') }}</router-link>
    </header>
    <main class="teachers-view__content">
      <div class="teachers-view__section">
        <h2>{{ t('teachers.addNewTeacher') }}</h2>
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
            :placeholder="t('teachers.availabilityPlaceholder')"
            class="teachers-view__input"
          />
          <small class="teachers-view__hint">{{ t('teachers.availabilityFormat') }}</small>
          <button type="submit" class="teachers-view__button" :disabled="loading">
            {{ t('teachers.addTeacher') }}
          </button>
        </form>
      </div>

      <!-- Teacher Filter -->
      <div class="teachers-view__section">
        <h2>{{ t('teachers.filterByTeacher') }}</h2>
        <select
          v-model="selectedTeacherId"
          class="teachers-view__filter"
          @change="onTeacherChange"
        >
          <option :value="null">{{ t('teachers.allTeachers') }}</option>
          <option
            v-for="teacher in teachers"
            :key="teacher.id"
            :value="teacher.id"
          >
            {{ teacher.full_name }}
          </option>
        </select>
      </div>

      <!-- Selected Teacher's Today's Timetable -->
      <div v-if="selectedTeacherId" class="teachers-view__section">
        <h2>{{ t('teachers.todaysTimetableFor') }} {{ getSelectedTeacherName() }}</h2>
        <div v-if="loadingTimetable" class="teachers-view__loading">{{ t('teachers.loadingTimetable') }}</div>
        <div v-else-if="todaysTimetableEntries.length > 0" class="teachers-view__timetable-list">
          <div
            v-for="entry in sortedTimetableEntries"
            :key="`${entry.lesson_index}-${entry.class_group?.id || 'no-class'}`"
            class="teachers-view__timetable-item"
          >
            <div class="teachers-view__timetable-time">
              {{ getLessonTime(entry.lesson_index) }}
            </div>
            <div class="teachers-view__timetable-details">
              <span class="teachers-view__timetable-subject">{{ entry.subject?.name || 'Unknown Subject' }}</span>
              <span class="teachers-view__timetable-class">{{ entry.class_group?.name || 'Unknown Class' }}</span>
              <span v-if="entry.classroom" class="teachers-view__timetable-classroom">{{ entry.classroom?.name }}</span>
            </div>
          </div>
        </div>
        <div v-else class="teachers-view__empty">{{ t('teachers.noLessonsToday') }}</div>
      </div>

      <!-- Selected Teacher's Absences -->
      <div v-if="selectedTeacherId" class="teachers-view__section">
        <h2>{{ t('teachers.absencesFor') }} {{ getSelectedTeacherName() }}</h2>
        <div v-if="loadingAbsences" class="teachers-view__loading">{{ t('teachers.loadingAbsences') }}</div>
        <div v-else-if="teacherAbsences.length > 0" class="teachers-view__absences-list">
          <div
            v-for="absence in teacherAbsences"
            :key="absence.id"
            class="teachers-view__absence-item"
          >
            <div class="teachers-view__absence-info">
              <span class="teachers-view__absence-dates">
                {{ formatDate(absence.date_from) }} - {{ formatDate(absence.date_to) }}
              </span>
              <span v-if="absence.reason" class="teachers-view__absence-reason">
                {{ t('dashboard.reason') }}: {{ absence.reason }}
              </span>
            </div>
            <button
              v-if="authStore.user?.role === 'ADMIN'"
              @click="deleteAbsence(absence.id)"
              class="teachers-view__absence-delete"
              :disabled="loading"
            >
              Delete
            </button>
          </div>
        </div>
        <div v-else class="teachers-view__empty">{{ t('teachers.noAbsencesReported') }}</div>
      </div>

      <div class="teachers-view__section">
        <h2>{{ t('teachers.teachersList') }}</h2>
        <div v-if="filteredTeachers.length > 0" class="teachers-view__list">
          <div
            v-for="teacher in filteredTeachers"
            :key="teacher.id"
            class="teachers-view__item"
          >
            <div class="teachers-view__item-info">
              <span class="teachers-view__item-name">{{ teacher.full_name }}</span>
              <span class="teachers-view__item-hours">{{ t('teachers.maxHours') }}: {{ teacher.max_weekly_hours }}</span>
              <div v-if="teacher.capabilities && teacher.capabilities.length > 0" class="teachers-view__item-subjects">
                {{ t('teachers.subjects') }}: {{ getTeacherSubjects(teacher.capabilities) }}
              </div>
              <div v-else class="teachers-view__item-no-subjects">{{ t('teachers.noSubjectsAssigned') }}</div>
            </div>
            <div class="teachers-view__item-actions">
              <button
                @click="editTeacher(teacher)"
                class="teachers-view__edit"
                :disabled="loading"
              >
                {{ t('teachers.edit') }}
              </button>
              <button
                @click="manageCapabilities(teacher)"
                class="teachers-view__capabilities"
                :disabled="loading"
              >
                {{ t('teachers.manageSpecializations') }}
              </button>
              <button
                @click="reportAbsence(teacher)"
                class="teachers-view__absence"
                :disabled="loading"
              >
                {{ t('teachers.reportAbsence') }}
              </button>
              <button
                v-if="authStore.user?.role === 'ADMIN'"
                @click="deleteTeacher(teacher.id)"
                class="teachers-view__delete"
                :disabled="loading"
              >
                {{ t('teachers.delete') }}
              </button>
            </div>
          </div>
        </div>
        <div v-else class="teachers-view__empty">{{ t('teachers.noTeachers') }}</div>
      </div>

      <!-- Edit Modal -->
      <div v-if="editingTeacher" class="teachers-view__modal">
        <div class="teachers-view__modal-content">
          <h3>{{ t('teachers.editTeacher') }}</h3>
          <form @submit.prevent="updateTeacher" class="teachers-view__form">
            <input
              v-model="editingTeacher.full_name"
              type="text"
              :placeholder="t('teachers.fullName')"
              class="teachers-view__input"
              required
            />
            <input
              v-model.number="editingTeacher.max_weekly_hours"
              type="number"
              :placeholder="t('teachers.maxWeeklyHours')"
              min="1"
              class="teachers-view__input"
              required
            />
            <input
              v-model="editAvailabilityInput"
              type="text"
              :placeholder="t('teachers.availability')"
              class="teachers-view__input"
            />
            <div class="teachers-view__modal-actions">
              <button type="submit" class="teachers-view__button" :disabled="loading">
                {{ t('teachers.save') }}
              </button>
              <button
                type="button"
                @click="editingTeacher = null"
                class="teachers-view__button teachers-view__button--secondary"
              >
                {{ t('teachers.cancel') }}
              </button>
            </div>
          </form>
        </div>
      </div>

      <!-- Absence Reporting Modal -->
      <div v-if="reportingAbsence" class="teachers-view__modal">
        <div class="teachers-view__modal-content">
          <h3>{{ t('teachers.reportAbsenceFor') }} {{ reportingAbsence.full_name }}</h3>
          <form @submit.prevent="submitAbsence" class="teachers-view__form">
            <div class="teachers-view__field">
              <label class="teachers-view__label">{{ t('teachers.dateFrom') }}</label>
              <input
                v-model="newAbsence.date_from"
                type="date"
                class="teachers-view__input"
                required
              />
            </div>
            <div class="teachers-view__field">
              <label class="teachers-view__label">{{ t('teachers.dateTo') }}</label>
              <input
                v-model="newAbsence.date_to"
                type="date"
                class="teachers-view__input"
                required
              />
            </div>
            <div class="teachers-view__field">
              <label class="teachers-view__label">{{ t('teachers.reasonOptional') }}</label>
              <textarea
                v-model="newAbsence.reason"
                :placeholder="t('teachers.reasonForAbsence')"
                class="teachers-view__input"
                rows="3"
              ></textarea>
            </div>
            <div class="teachers-view__modal-actions">
              <button type="submit" class="teachers-view__button" :disabled="loading">
                {{ t('teachers.reportAbsence') }}
              </button>
              <button
                type="button"
                @click="reportingAbsence = null; newAbsence = { date_from: '', date_to: '', reason: '' }"
                class="teachers-view__button teachers-view__button--secondary"
              >
                {{ t('teachers.cancel') }}
              </button>
            </div>
          </form>
        </div>
      </div>

      <!-- Capabilities Modal -->
      <div v-if="managingCapabilities" class="teachers-view__modal">
        <div class="teachers-view__modal-content teachers-view__modal-content--large">
          <h3>{{ t('teachers.manageSpecializationsFor') }} {{ managingCapabilities.full_name }}</h3>
          <div class="teachers-view__capabilities-section">
            <h4>{{ t('teachers.addNewSpecialization') }}</h4>
            <form @submit.prevent="addCapability" class="teachers-view__form">
              <select
                v-model="newCapability.subject_id"
                class="teachers-view__input"
                required
              >
                <option value="">{{ t('teachers.selectSubject') }}</option>
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
                <option :value="null">{{ t('teachers.allClassesOrSelect') }}</option>
                <option
                  v-for="classGroup in classes"
                  :key="classGroup.id"
                  :value="classGroup.id"
                >
                  {{ classGroup.name }}
                </option>
              </select>
              <button type="submit" class="teachers-view__button" :disabled="loading">
                {{ t('teachers.addSpecialization') }}
              </button>
            </form>
          </div>
          <div class="teachers-view__capabilities-section">
            <h4>{{ t('teachers.currentSpecializations') }}</h4>
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
                  ({{ t('teachers.class') }}: {{ getClassName(capability.class_group_id) }})
                </span>
                <button
                  @click="removeCapability(capability.id)"
                  class="teachers-view__capability-remove"
                  :disabled="loading"
                >
                  {{ t('teachers.remove') }}
                </button>
              </div>
            </div>
            <div v-else class="teachers-view__empty">{{ t('teachers.noSpecializationsYet') }}</div>
          </div>
          <div class="teachers-view__modal-actions">
            <button
              type="button"
              @click="managingCapabilities = null"
              class="teachers-view__button teachers-view__button--secondary"
            >
              {{ t('teachers.close') }}
            </button>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useI18nStore } from '@/stores/i18n'
import { useAlert } from '@/composables/useAlert'
import api from '@/services/api'

const i18nStore = useI18nStore()
const t = i18nStore.t
const alert = useAlert()

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
const editingTeacher = ref<Teacher | null>(null)
const managingCapabilities = ref<Teacher | null>(null)
const teacherCapabilities = ref<TeacherCapability[]>([])
const reportingAbsence = ref<Teacher | null>(null)
const selectedTeacherId = ref<number | null>(null)
const teacherAbsences = ref<any[]>([])
const loadingAbsences = ref(false)
const todaysTimetableEntries = ref<any[]>([])
const loadingTimetable = ref(false)
const schoolSettings = ref<any>(null)
const newAbsence = ref({
  date_from: '',
  date_to: '',
  reason: ''
})

const filteredTeachers = computed(() => {
  if (!selectedTeacherId.value) {
    return teachers.value
  }
  return teachers.value.filter(t => t.id === selectedTeacherId.value)
})

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
    console.error('Failed to load teachers:', err)
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
    alert.success('Teacher created successfully')
    newTeacher.value = { full_name: '', max_weekly_hours: 20, availability: null }
    availabilityInput.value = ''
    await loadTeachers()
  } catch (err: any) {
    alert.error(err.response?.data?.detail || 'Failed to create teacher')
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
    alert.success('Teacher updated successfully')
    editingTeacher.value = null
    await loadTeachers()
  } catch (err: any) {
    alert.error(err.response?.data?.detail || 'Failed to update teacher')
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
    console.error('Failed to load capabilities:', err)
  }
}

async function addCapability() {
  if (!managingCapabilities.value || !newCapability.value.subject_id) return
  
  loading.value = true
  
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
    alert.success('Capability added successfully')
    newCapability.value = { subject_id: null, class_group_id: null }
    await loadTeacherCapabilities(managingCapabilities.value.id)
  } catch (err: any) {
    alert.error(err.response?.data?.detail || 'Failed to add capability')
  } finally {
    loading.value = false
  }
}

async function removeCapability(capabilityId: number) {
  if (!managingCapabilities.value) return
  
  loading.value = true
  
  try {
    const schoolId = authStore.user?.school_id
    if (!schoolId) {
      throw new Error('School ID not found')
    }
    
    await api.delete(
      `/teachers/schools/${schoolId}/teachers/${managingCapabilities.value.id}/capabilities/${capabilityId}`
    )
    alert.success('Capability removed successfully')
    await loadTeacherCapabilities(managingCapabilities.value.id)
  } catch (err: any) {
    alert.error(err.response?.data?.detail || 'Failed to remove capability')
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

function reportAbsence(teacher: Teacher) {
  reportingAbsence.value = teacher
  newAbsence.value = { date_from: '', date_to: '', reason: '' }
}

async function submitAbsence() {
  if (!reportingAbsence.value) return
  
  loading.value = true
  
  try {
    const schoolId = authStore.user?.school_id
    if (!schoolId) {
      throw new Error('School ID not found')
    }
    
    await api.post(`/absences/schools/${schoolId}/absences`, {
      teacher_id: reportingAbsence.value.id,
      date_from: newAbsence.value.date_from,
      date_to: newAbsence.value.date_to,
      reason: newAbsence.value.reason || null
    })
    
    alert.success('Absence reported successfully')
    reportingAbsence.value = null
    newAbsence.value = { date_from: '', date_to: '', reason: '' }
    
    // Reload absences if viewing a teacher
    if (selectedTeacherId.value) {
      await loadTeacherAbsences(selectedTeacherId.value)
    }
  } catch (err: any) {
    alert.error(err.response?.data?.detail || 'Failed to report absence')
  } finally {
    loading.value = false
  }
}

function getSelectedTeacherName(): string {
  const teacher = teachers.value.find(t => t.id === selectedTeacherId.value)
  return teacher ? teacher.full_name : 'Unknown'
}

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString()
}

async function loadTeacherAbsences(teacherId: number) {
  loadingAbsences.value = true
  try {
    const schoolId = authStore.user?.school_id
    if (!schoolId) return
    
    const response = await api.get(`/absences/schools/${schoolId}/absences?teacher_id=${teacherId}`)
    teacherAbsences.value = response.data
  } catch (err: any) {
    console.error('Failed to load absences:', err)
    teacherAbsences.value = []
  } finally {
    loadingAbsences.value = false
  }
}

async function onTeacherChange() {
  if (selectedTeacherId.value) {
    await loadTeacherAbsences(selectedTeacherId.value)
    await loadTodaysTimetable(selectedTeacherId.value)
  } else {
    teacherAbsences.value = []
    todaysTimetableEntries.value = []
  }
}

async function loadTodaysTimetable(teacherId: number) {
  if (!selectedTeacherId.value) return
  
  loadingTimetable.value = true
  try {
    const schoolId = authStore.user?.school_id
    if (!schoolId) return
    
    // Get today's day of week (0 = Monday, 4 = Friday)
    const today = new Date()
    const dayOfWeek = (today.getDay() + 6) % 7 // Convert Sunday=0 to Monday=0
    
    const response = await api.get(`/teachers/schools/${schoolId}/teachers/${teacherId}/timetable?day_of_week=${dayOfWeek}`)
    todaysTimetableEntries.value = response.data
    
    // Load school settings if not already loaded
    if (!schoolSettings.value) {
      await loadSchoolSettings()
    }
  } catch (err: any) {
    console.error('Failed to load timetable:', err)
    todaysTimetableEntries.value = []
  } finally {
    loadingTimetable.value = false
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

const sortedTimetableEntries = computed(() => {
  return [...todaysTimetableEntries.value].sort((a, b) => a.lesson_index - b.lesson_index)
})

function getLessonTime(lessonIndex: number): string {
  if (!schoolSettings.value) return `Lesson ${lessonIndex}`
  
  const startTime = new Date(`2000-01-01T${schoolSettings.value.start_time}`)
  const classHourLength = schoolSettings.value.class_hour_length_minutes || 45
  const breakDurations = schoolSettings.value.break_durations || []
  
  // Calculate total minutes from start
  let totalMinutes = 0
  
  // Add time for previous lessons
  for (let i = 1; i < lessonIndex; i++) {
    totalMinutes += classHourLength
    // Add break duration after each lesson (except the last one)
    if (i < lessonIndex) {
      const breakIndex = i - 1
      const breakDuration = breakDurations[breakIndex] || breakDurations[breakDurations.length - 1] || schoolSettings.value.break_duration_minutes || 10
      totalMinutes += breakDuration
    }
  }
  
  // Calculate start time for this lesson
  const lessonStart = new Date(startTime.getTime() + totalMinutes * 60000)
  const lessonEnd = new Date(lessonStart.getTime() + classHourLength * 60000)
  
  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false })
  }
  
  return `${formatTime(lessonStart)} - ${formatTime(lessonEnd)}`
}

async function deleteAbsence(absenceId: number) {
  if (!confirm('Are you sure you want to delete this absence?')) {
    return
  }
  
  loading.value = true
  
  try {
    const schoolId = authStore.user?.school_id
    if (!schoolId) {
      throw new Error('School ID not found')
    }
    
    await api.delete(`/absences/schools/${schoolId}/absences/${absenceId}`)
    alert.success('Absence deleted successfully')
    
    // Reload absences
    if (selectedTeacherId.value) {
      await loadTeacherAbsences(selectedTeacherId.value)
    }
  } catch (err: any) {
    alert.error(err.response?.data?.detail || 'Failed to delete absence')
  } finally {
    loading.value = false
  }
}

async function deleteTeacher(teacherId: number) {
  if (!confirm('Are you sure you want to delete this teacher?')) {
    return
  }
  
  loading.value = true
  
  try {
    const schoolId = authStore.user?.school_id
    if (!schoolId) {
      throw new Error('School ID not found')
    }
    
    await api.delete(`/teachers/schools/${schoolId}/teachers/${teacherId}`)
    alert.success('Teacher deleted successfully')
    await loadTeachers()
  } catch (err: any) {
    alert.error(err.response?.data?.detail || 'Failed to delete teacher')
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await loadTeachers()
  await loadSubjects()
  await loadClasses()
  await loadSchoolSettings()
  
  // If user is a teacher, automatically select their own teacher ID
  if (authStore.user?.role === 'TEACHER' && authStore.user?.teacher_id) {
    selectedTeacherId.value = authStore.user.teacher_id
    await onTeacherChange()
  }
})
</script>

<style lang="scss" scoped>
@import '../styles/neo.scss';

.teachers-view {
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
    margin-top: -0.5rem;
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
      gap: 0.25rem;
    }

    &-name {
      font-weight: 600;
      color: $neo-text;
      
    }

    &-hours {
      color: $neo-text-light;
      font-size: 0.875rem;
    }

    &-subjects {
      color: $neo-text;
      font-size: 0.875rem;
      margin-top: 0.25rem;
      font-weight: 500;
    }

    &-no-subjects {
      color: $neo-text-muted;
      font-size: 0.875rem;
      margin-top: 0.25rem;
      font-style: italic;
    }

    &-actions {
      display: flex;
      gap: 0.5rem;
    }
  }

  &__edit,
  &__capabilities,
  &__absence,
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
    background: rgba(255, 193, 7, 0.3);
    border-color: rgba(255, 193, 7, 0.4);
    color: $neo-text;

    &:hover:not(:disabled) {
      background: rgba(255, 193, 7, 0.4);
      border-color: rgba(255, 193, 7, 0.5);
    }
  }

  &__capabilities {
    background: rgba(23, 162, 184, 0.3);
    border-color: rgba(23, 162, 184, 0.4);

    &:hover:not(:disabled) {
      background: rgba(23, 162, 184, 0.4);
      border-color: rgba(23, 162, 184, 0.5);
    }
  }

  &__absence {
    background: rgba(255, 152, 0, 0.3);
    border-color: rgba(255, 152, 0, 0.4);

    &:hover:not(:disabled) {
      background: rgba(255, 152, 0, 0.4);
      border-color: rgba(255, 152, 0, 0.5);
    }
  }

  &__delete {
    background: lighten(#dc3545, 35%);
    border-color: lighten(#dc3545, 35%);

    &:hover:not(:disabled) {
      background: lighten(#dc3545, 35%);
      border-color: lighten(#dc3545, 35%);
    }
  }

  &__empty {
    padding: 2rem;
    text-align: center;
    color: $neo-text-muted;
    font-style: italic;
  }

  &__filter {
    @extend %neo-input;
    width: 100%;
    max-width: 400px;
    padding: 0.75rem;
    border-radius: 12px;
    font-size: 1rem;
  }

  &__loading {
    text-align: center;
    padding: 2rem;
    color: $neo-text-light;
  }

  &__timetable-list {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  &__timetable-item {
    @extend %neo-list-item;
    display: flex;
    gap: 1rem;
    padding: 1rem;
    align-items: center;
  }

  &__timetable-time {
    font-weight: 600;
    color: $neo-text;
    min-width: 140px;
    font-size: 0.9rem;
  }

  &__timetable-details {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    flex: 1;
  }

  &__timetable-subject {
    font-weight: 600;
    color: $neo-text;
    font-size: 1rem;
  }

  &__timetable-class {
    color: $neo-text-light;
    font-size: 0.9rem;
  }

  &__timetable-classroom {
    color: $neo-text-muted;
    font-size: 0.85rem;
    font-style: italic;
  }

  &__absences-list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  &__absence-item {
    @extend %neo-list-item;
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem;
  }

  &__absence-info {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  &__absence-dates {
    font-weight: 600;
    color: $neo-text;
  }

  &__absence-reason {
    color: $neo-text-light;
    font-size: 0.875rem;
  }

  &__absence-delete {
    @extend %neo-button;
    @extend %neo-button--danger;
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

    h3 {
      color: $neo-text;
    }
  }

  &__capabilities-section {
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

  &__capabilities-list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  &__capability-item {
    @extend %neo-list-item;
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 0.75rem;
  }

  &__capability-subject {
    font-weight: 600;
    color: $neo-text;
  }

  &__capability-class {
    color: $neo-text-light;
    font-size: 0.875rem;
  }

  &__capability-remove {
    margin-left: auto;
    @extend %neo-button;
    @extend %neo-button--danger;
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

  &__modal-actions {
    display: flex;
    gap: 1rem;
    margin-top: 1rem;
  }
}
</style>

