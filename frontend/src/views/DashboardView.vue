<template>
  <div class="dashboard-view">
    <header class="dashboard-view__header">
      <div class="dashboard-view__header-content">
        <h1 class="dashboard-view__title">Dashboard</h1>
      </div>
        <div v-if="authStore.user?.role === 'ADMIN'" class="dashboard-view__admin-links">
            <router-link to="/settings" class="dashboard-view__link">School Settings</router-link>
            <router-link to="/classes" class="dashboard-view__link">Classes</router-link>
            <router-link to="/teachers" class="dashboard-view__link">Teachers</router-link>
            <router-link to="/timetables" class="dashboard-view__link">Timetables</router-link>
        </div>
      <button @click="handleLogout" class="dashboard-view__logout">Logout</button>
    </header>
    <main class="dashboard-view__content">
      <div v-if="authStore.user?.role === 'ADMIN'" class="dashboard-view__sections-grid">
        <!-- Currently Running Lessons -->
        <div class="dashboard-view__lessons-section">
          <h2 class="dashboard-view__section-title">
            <span class="dashboard-view__section-icon">⏰</span>
            Currently Running Lessons
          </h2>
          <div v-if="loadingLessons" class="dashboard-view__loading">Loading...</div>
          <div v-else-if="currentLessons.length === 0" class="dashboard-view__empty">
            No lessons are currently running
          </div>
          <div v-else class="dashboard-view__lessons-list">
            <div
              v-for="lesson in currentLessons"
              :key="lesson.id"
              class="dashboard-view__lesson-item"
            >
              <div class="dashboard-view__lesson-header">
                <span class="dashboard-view__lesson-class">{{ lesson.class_group?.name || 'Unknown Class' }}</span>
                <span class="dashboard-view__lesson-time">{{ lesson.timeRange }}</span>
              </div>
              <div class="dashboard-view__lesson-details">
                <div class="dashboard-view__lesson-detail">
                  <span class="dashboard-view__lesson-label">Subject:</span>
                  <span class="dashboard-view__lesson-value">{{ lesson.subject?.name || 'N/A' }}</span>
                </div>
                <div class="dashboard-view__lesson-detail">
                  <span class="dashboard-view__lesson-label">Teacher:</span>
                  <span class="dashboard-view__lesson-value">{{ lesson.teacher?.full_name || 'N/A' }}</span>
                </div>
                <div v-if="lesson.classroom" class="dashboard-view__lesson-detail">
                  <span class="dashboard-view__lesson-label">Classroom:</span>
                  <span class="dashboard-view__lesson-value">{{ lesson.classroom?.name || 'N/A' }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Today's Absent Teachers -->
        <div class="dashboard-view__absences-section">
          <h2 class="dashboard-view__section-title">
            <span class="dashboard-view__section-icon">📅</span>
            Today's Absent Teachers
          </h2>
          <div v-if="loadingAbsences" class="dashboard-view__loading">Loading...</div>
          <div v-else-if="todayAbsences.length === 0" class="dashboard-view__empty">
            No teachers are absent today
          </div>
          <div v-else class="dashboard-view__absences-list">
            <div
              v-for="absence in todayAbsences"
              :key="absence.id"
              class="dashboard-view__absence-item"
            >
              <div class="dashboard-view__absence-info">
                <span class="dashboard-view__absence-name">
                  {{ absence.teacher?.full_name || 'Unknown Teacher' }}
                </span>
                <span class="dashboard-view__absence-dates">
                  {{ formatDate(absence.date_from) }} - {{ formatDate(absence.date_to) }}
                </span>
              </div>
              <div v-if="absence.reason" class="dashboard-view__absence-reason">
                {{ absence.reason }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="authStore.user?.role === 'TEACHER'" class="dashboard-view__teacher-links">
        <router-link to="/teacher" class="dashboard-view__link">Teacher Dashboard</router-link>
        <router-link to="/absence" class="dashboard-view__link">Report Absence</router-link>
        <router-link to="/timetable" class="dashboard-view__link">View Timetable</router-link>
      </div>
      <div v-else-if="authStore.user?.role === 'SCHOLAR'" class="dashboard-view__scholar-links">
        <router-link to="/scholar" class="dashboard-view__link">Scholar Dashboard</router-link>
        <router-link to="/timetable" class="dashboard-view__link">View Timetable</router-link>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import api from '@/services/api'

interface Absence {
  id: number
  teacher_id: number
  date_from: string
  date_to: string
  reason: string | null
  school_id: number
  teacher?: {
    id: number
    full_name: string
  }
}

interface TimetableEntry {
  id: number
  class_group_id: number
  subject_id: number
  teacher_id: number
  classroom_id: number | null
  day_of_week: number
  lesson_index: number
  class_group?: {
    id: number
    name: string
  }
  subject?: {
    id: number
    name: string
  }
  teacher?: {
    id: number
    full_name: string
  }
  classroom?: {
    id: number
    name: string
  }
}

interface CurrentLesson extends TimetableEntry {
  timeRange: string
}

const router = useRouter()
const authStore = useAuthStore()
const absences = ref<Absence[]>([])
const loadingAbsences = ref(false)
const timetables = ref<any[]>([])
const schoolSettings = ref<any>(null)
const loadingLessons = ref(false)
const currentLessons = ref<CurrentLesson[]>([])

const today = new Date()
today.setHours(0, 0, 0, 0)
const todayStr = today.toISOString().split('T')[0]

const todayAbsences = computed(() => {
  return absences.value.filter(absence => {
    const dateFrom = new Date(absence.date_from)
    const dateTo = new Date(absence.date_to)
    dateFrom.setHours(0, 0, 0, 0)
    dateTo.setHours(0, 0, 0, 0)
    const todayDate = new Date(todayStr)
    todayDate.setHours(0, 0, 0, 0)
    return todayDate >= dateFrom && todayDate <= dateTo
  })
})

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

async function loadAbsences() {
  if (authStore.user?.role !== 'ADMIN' || !authStore.user?.school_id) {
    return
  }

  loadingAbsences.value = true
  try {
    const response = await api.get(`/absences/schools/${authStore.user.school_id}/absences`)
    absences.value = response.data
  } catch (err: any) {
    console.error('Failed to load absences:', err)
  } finally {
    loadingAbsences.value = false
  }
}

function handleLogout() {
  authStore.logout()
  router.push('/login')
}

function getBreakDuration(breakIndex: number, breakDurations: number[] | null, defaultBreak: number): number {
  if (breakDurations && breakDurations.length > 0) {
    if (breakIndex < breakDurations.length) {
      return breakDurations[breakIndex]
    } else {
      return breakDurations[breakDurations.length - 1]
    }
  }
  return defaultBreak
}

function calculateCurrentLesson(): number | null {
  if (!schoolSettings.value) return null

  const now = new Date()
  const currentDayOfWeek = (now.getDay() + 6) % 7 // Monday = 0, Sunday = 6
  
  // Check if it's a weekday (Monday-Friday)
  if (currentDayOfWeek > 4) return null

  const startTime = schoolSettings.value.start_time || '08:00'
  const classHourLength = schoolSettings.value.class_hour_length_minutes || 45
  const defaultBreakDuration = schoolSettings.value.break_duration_minutes || 10
  const breakDurations = schoolSettings.value.break_durations || null

  // Parse start time
  const [startHours, startMinutes] = startTime.split(':').map(Number)
  const schoolStart = new Date()
  schoolStart.setHours(startHours, startMinutes, 0, 0)

  // Calculate lesson times
  let currentTime = new Date(schoolStart)
  const maxLessons = 10 // Reasonable max

  for (let lessonIndex = 1; lessonIndex <= maxLessons; lessonIndex++) {
    const lessonStart = new Date(currentTime)
    const lessonEnd = new Date(currentTime.getTime() + classHourLength * 60000)

    // Check if current time is within this lesson
    if (now >= lessonStart && now < lessonEnd) {
      return lessonIndex
    }

    // Move to next lesson (add break after this lesson)
    const breakDuration = getBreakDuration(lessonIndex - 1, breakDurations, defaultBreakDuration)
    currentTime = new Date(lessonEnd.getTime() + breakDuration * 60000)

    // If we've passed the current time, no lesson is running
    if (currentTime > now) {
      break
    }
  }

  return null
}

function formatTimeRange(lessonIndex: number): string {
  if (!schoolSettings.value) return ''

  const startTime = schoolSettings.value.start_time || '08:00'
  const classHourLength = schoolSettings.value.class_hour_length_minutes || 45
  const defaultBreakDuration = schoolSettings.value.break_duration_minutes || 10
  const breakDurations = schoolSettings.value.break_durations || null

  const [startHours, startMinutes] = startTime.split(':').map(Number)
  const schoolStart = new Date()
  schoolStart.setHours(startHours, startMinutes, 0, 0)

  let currentTime = new Date(schoolStart)

  for (let i = 1; i < lessonIndex; i++) {
    const breakDuration = getBreakDuration(i - 1, breakDurations, defaultBreakDuration)
    currentTime = new Date(currentTime.getTime() + classHourLength * 60000 + breakDuration * 60000)
  }

  const lessonStart = new Date(currentTime)
  const lessonEnd = new Date(currentTime.getTime() + classHourLength * 60000)

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false })
  }

  return `${formatTime(lessonStart)} - ${formatTime(lessonEnd)}`
}

async function loadSchoolSettings() {
  if (!authStore.user?.school_id) return

  try {
    const response = await api.get(`/schools/${authStore.user.school_id}/settings`)
    schoolSettings.value = response.data
  } catch (err: any) {
    console.error('Failed to load school settings:', err)
  }
}

async function loadTimetables() {
  if (!authStore.user?.school_id) return

  try {
    const response = await api.get(`/timetables/schools/${authStore.user.school_id}/timetables`)
    timetables.value = response.data
  } catch (err: any) {
    console.error('Failed to load timetables:', err)
  }
}

function updateCurrentLessons() {
  if (!schoolSettings.value || !timetables.value.length) {
    currentLessons.value = []
    return
  }

  const currentDayOfWeek = (new Date().getDay() + 6) % 7 // Monday = 0
  if (currentDayOfWeek > 4) {
    currentLessons.value = []
    return
  }

  const currentLessonIndex = calculateCurrentLesson()
  if (!currentLessonIndex) {
    currentLessons.value = []
    return
  }

  // Find valid timetable for today
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const todayStr = today.toISOString().split('T')[0]

  let validTimetable: any = null
  for (const timetable of timetables.value) {
    if (timetable.is_primary === 0) {
      // Substitute timetable
      if (timetable.substitute_for_date === todayStr) {
        validTimetable = timetable
        break
      }
    } else {
      // Primary timetable
      if (timetable.valid_from && timetable.valid_to) {
        if (todayStr >= timetable.valid_from && todayStr <= timetable.valid_to) {
          validTimetable = timetable
          // Check if there's a substitute for this date (substitute takes precedence)
          const substitute = timetables.value.find(
            (t: any) => t.is_primary === 0 && t.substitute_for_date === todayStr
          )
          if (substitute) {
            validTimetable = substitute
            break
          }
        }
      }
    }
  }

  if (!validTimetable || !validTimetable.entries) {
    currentLessons.value = []
    return
  }

  // Filter entries for current day and lesson
  const entries = validTimetable.entries.filter((entry: TimetableEntry) => {
    return entry.day_of_week === currentDayOfWeek && entry.lesson_index === currentLessonIndex
  })

  currentLessons.value = entries.map((entry: TimetableEntry) => ({
    ...entry,
    timeRange: formatTimeRange(currentLessonIndex)
  }))
}

async function loadCurrentLessons() {
  if (authStore.user?.role !== 'ADMIN' || !authStore.user?.school_id) {
    return
  }

  loadingLessons.value = true
  try {
    await Promise.all([loadSchoolSettings(), loadTimetables()])
    updateCurrentLessons()
    
    // Update every minute
    setInterval(() => {
      updateCurrentLessons()
    }, 60000)
  } catch (err: any) {
    console.error('Failed to load current lessons:', err)
  } finally {
    loadingLessons.value = false
  }
}

onMounted(() => {
  if (authStore.user?.role === 'ADMIN') {
    loadAbsences()
    loadCurrentLessons()
  }
})
</script>

<style lang="scss" scoped>
@import '../styles/neo.scss';

.dashboard-view {
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
    gap: 2rem;
  }

  &__header-content {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    flex: 1;
  }

  &__title {
    color: $neo-text;
    font-size: 1.75rem;
    font-weight: 700;
  }

  &__logout {
    @extend %neo-button;
    @extend %neo-button--danger;
    padding: 0.75rem 1.5rem;
    border-radius: 12px;
    cursor: pointer;
    font-weight: 600;
  }

  &__content {
    padding: 2rem;
    max-width: 1600px;
    margin: 0 auto;
    position: relative;
    z-index: 1;
  }

  &__sections-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 2rem;
    margin-bottom: 2rem;

    @media (max-width: 1024px) {
      grid-template-columns: 1fr;
    }
  }

  &__lessons-section,
  &__absences-section {
    @extend %neo-card;
    padding: 1.5rem;
  }

  &__section-title {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin: 0 0 1.25rem 0;
    color: $neo-text;
    font-size: 1.25rem;
    font-weight: 600;
  }

  &__section-icon {
    font-size: 1.5rem;
  }

  &__loading,
  &__empty {
    color: $neo-text-muted;
    text-align: center;
    padding: 1rem;
    font-style: italic;
  }

  &__absences-list {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  &__absence-item {
    @include neo-surface(12px, 0.6);
    padding: 1rem;
    background: $neo-bg-light;
    border-radius: 12px;
  }

  &__absence-info {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 1rem;
    margin-bottom: 0.5rem;
  }

  &__absence-name {
    font-weight: 600;
    color: $neo-text;
    font-size: 1rem;
  }

  &__absence-dates {
    color: $neo-text-muted;
    font-size: 0.9rem;
  }

  &__absence-reason {
    color: $neo-text-light;
    font-size: 0.875rem;
    font-style: italic;
    margin-top: 0.5rem;
    padding-top: 0.5rem;
    border-top: 1px solid rgba(0, 0, 0, 0.05);
  }

  &__lessons-list {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  &__lesson-item {
    @include neo-surface(12px, 0.6);
    padding: 1rem;
    background: $neo-bg-light;
    border-radius: 12px;
  }

  &__lesson-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.75rem;
    padding-bottom: 0.75rem;
    border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  }

  &__lesson-class {
    font-weight: 700;
    color: $neo-text;
    font-size: 1.1rem;
  }

  &__lesson-time {
    color: $neo-text-muted;
    font-size: 0.9rem;
    font-weight: 600;
  }

  &__lesson-details {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  &__lesson-detail {
    display: flex;
    gap: 0.5rem;
  }

  &__lesson-label {
    font-weight: 600;
    color: $neo-text-light;
    min-width: 80px;
  }

  &__lesson-value {
    color: $neo-text;
  }

  &__admin-links {
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
  }

  &__teacher-links,
  &__scholar-links {
    display: flex;
    gap: 1.5rem;
    margin-bottom: 2rem;
    flex-wrap: wrap;
  }

  &__link {
    @extend %neo-button;
    @extend %neo-button--secondary;
    display: inline-block;
    padding: 0.75rem 1.5rem;
    color: $neo-text;
    text-decoration: none;
    font-weight: 600;
    transition: all 0.3s ease;
    text-align: center;
    border-radius: 12px;
    font-size: 0.95rem;

    &:hover {
      @include neo-surface(12px, 1.2);
      transform: translateY(-2px);
    }
    
    &:active {
      @include neo-inset(12px, 0.6);
      transform: translateY(0);
    }
  }
}
</style>

