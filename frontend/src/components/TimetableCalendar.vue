<template>
  <div class="timetable-calendar">
    <!-- Class Selector -->
    <div class="timetable-calendar__class-selector">
      <label class="timetable-calendar__label">{{ t('components.timetableCalendar.selectClass') }}:</label>
      <select
        v-model="selectedClassId"
        class="timetable-calendar__select"
        @change="onClassChange"
      >
        <option :value="null">{{ t('components.timetableCalendar.allClasses') }}</option>
        <option
          v-for="classGroup in classGroups"
          :key="classGroup.id"
          :value="classGroup.id"
        >
          {{ classGroup.name }}
        </option>
      </select>
    </div>

    <!-- View Toggle -->
    <div class="timetable-calendar__view-toggle">
      <button
        @click="viewMode = 'month'"
        :class="['timetable-calendar__toggle-button', { 'timetable-calendar__toggle-button--active': viewMode === 'month' }]"
      >
        {{ t('components.timetableCalendar.monthView') }}
      </button>
      <button
        @click="viewMode = 'day'"
        :class="['timetable-calendar__toggle-button', { 'timetable-calendar__toggle-button--active': viewMode === 'day' }]"
      >
        {{ t('components.timetableCalendar.dayView') }}
      </button>
    </div>

    <!-- Month View -->
    <div v-if="viewMode === 'month'" class="timetable-calendar__month-view">
      <div class="timetable-calendar__header">
        <button @click="previousMonth" class="timetable-calendar__nav-button">‹</button>
        <h3 class="timetable-calendar__month-year">
          {{ currentMonthName }} {{ currentYear }}
        </h3>
        <button @click="nextMonth" class="timetable-calendar__nav-button">›</button>
      </div>
      <div class="timetable-calendar__weekdays">
        <div
          v-for="day in weekdays"
          :key="day"
          class="timetable-calendar__weekday"
        >
          {{ day }}
        </div>
      </div>
      <div class="timetable-calendar__days">
        <div
          v-for="day in calendarDays"
          :key="day.key"
          :class="[
            'timetable-calendar__day',
            {
              'timetable-calendar__day--other-month': day.isOtherMonth,
              'timetable-calendar__day--today': day.isToday,
              'timetable-calendar__day--has-entries': day.entriesCount > 0
            }
          ]"
          @click="selectDate(day.date)"
        >
          <span class="timetable-calendar__day-number">{{ day.dayNumber }}</span>
          <div v-if="day.entriesCount > 0" class="timetable-calendar__day-entries">
            <div class="timetable-calendar__entries-count">{{ day.entriesCount }}</div>
            <div class="timetable-calendar__entries-preview">
              <div
                v-for="(entry, idx) in day.entriesPreview"
                :key="idx"
                class="timetable-calendar__entry-preview"
              >
                {{ entry.subject }} ({{ entry.lesson }})
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Day View -->
    <div v-else class="timetable-calendar__day-view">
      <div class="timetable-calendar__day-header">
        <button @click="previousDay" class="timetable-calendar__nav-button">‹</button>
        <h3 class="timetable-calendar__day-title">
          {{ selectedDayDate.toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' }) }}
        </h3>
        <button @click="nextDay" class="timetable-calendar__nav-button">›</button>
      </div>
      <div class="timetable-calendar__day-selector">
        <input
          v-model="selectedDayDateInput"
          type="date"
          class="timetable-calendar__date-input"
          @change="onDayDateChange"
        />
        <button @click="goToToday" class="timetable-calendar__today-button">{{ t('components.timetableCalendar.today') }}</button>
      </div>
      <div v-if="loadingDayEntries" class="timetable-calendar__loading">{{ t('common.loading') }}</div>
      <div v-else-if="daySchedule.length > 0" class="timetable-calendar__day-timetable">
        <div
          v-for="(item, index) in daySchedule"
          :key="item.key || index"
          :class="[
            'timetable-calendar__day-item',
            { 'timetable-calendar__day-item--lunch': item.type === 'lunch' }
          ]"
        >
          <div class="timetable-calendar__item-time">
            <div class="timetable-calendar__time-start">{{ item.startTime }}</div>
            <div class="timetable-calendar__time-end">{{ item.endTime }}</div>
          </div>
          <div v-if="item.type === 'lunch'" class="timetable-calendar__lunch-break">
            <div class="timetable-calendar__lunch-icon">🍽️</div>
            <div class="timetable-calendar__lunch-text">{{ t('components.timetableCalendar.lunchBreak') }}</div>
          </div>
          <div v-else-if="item.entry" class="timetable-calendar__entry-details">
            <div class="timetable-calendar__entry-subject">{{ item.entry.subject?.name || t('commonPhrases.na') }}</div>
            <div class="timetable-calendar__entry-info">
              <span class="timetable-calendar__entry-teacher">{{ item.entry.teacher?.full_name || t('commonPhrases.na') }}</span>
              <span v-if="item.entry.classroom" class="timetable-calendar__entry-classroom">{{ item.entry.classroom.name }}</span>
            </div>
          </div>
        </div>
      </div>
      <div v-else class="timetable-calendar__empty">
        {{ t('components.timetableCalendar.noEntries') }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useI18nStore } from '@/stores/i18n'
import api from '@/services/api'

const i18nStore = useI18nStore()
const t = i18nStore.t

interface Timetable {
  id: number
  name: string
  valid_from: string | null
  valid_to: string | null
  is_primary?: number
  substitute_for_date?: string | null
  entries?: TimetableEntry[]
}

interface TimetableEntry {
  id: number
  timetable_id: number
  class_group_id: number
  subject_id: number
  teacher_id: number
  classroom_id: number | null
  day_of_week: number
  lesson_index: number
  subject?: { id: number; name: string }
  teacher?: { id: number; full_name: string }
  classroom?: { id: number; name: string }
  class_group?: { id: number; name: string }
}

interface ClassGroup {
  id: number
  name: string
}

interface Props {
  timetables: Timetable[]
}

interface DayInfo {
  key: string
  dayNumber: number
  date: Date
  isOtherMonth: boolean
  isToday: boolean
  entriesCount: number
  entriesPreview: Array<{ subject: string; lesson: number }>
}

const props = defineProps<Props>()

const emit = defineEmits<{
  dateSelected: [date: Date]
}>()

const authStore = useAuthStore()
const viewMode = ref<'month' | 'day'>('month')
const selectedClassId = ref<number | null>(null)
const classGroups = ref<ClassGroup[]>([])
const currentDate = ref(new Date())
const selectedDayDate = ref(new Date())
const selectedDayDateInput = ref('')
const dayEntries = ref<TimetableEntry[]>([])
const loadingDayEntries = ref(false)
const schoolSettings = ref<any>(null)
const weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

interface ScheduleItem {
  key: string
  type: 'lesson' | 'lunch'
  startTime: string
  endTime: string
  entry?: TimetableEntry
  lessonIndex?: number
}

// Initialize selected day date input
selectedDayDateInput.value = selectedDayDate.value.toISOString().split('T')[0]

const currentYear = computed(() => currentDate.value.getFullYear())
const currentMonth = computed(() => currentDate.value.getMonth())
const currentMonthName = computed(() => {
  return currentDate.value.toLocaleDateString('en-US', { month: 'long' })
})

// Calculate lunch hour slots
const lunchHourSlots = computed(() => {
  if (!schoolSettings.value?.possible_lunch_hours || !schoolSettings.value?.lunch_duration_minutes || !schoolSettings.value?.class_hour_length_minutes) {
    return []
  }
  
  const lunchHoursCount = Math.ceil(schoolSettings.value.lunch_duration_minutes / schoolSettings.value.class_hour_length_minutes)
  const possibleHours = [...schoolSettings.value.possible_lunch_hours].sort((a, b) => a - b)
  
  // Find consecutive hours
  for (let i = 0; i <= possibleHours.length - lunchHoursCount; i++) {
    const consecutive = possibleHours.slice(i, i + lunchHoursCount)
    const isConsecutive = consecutive.every((hour, idx) => hour === consecutive[0] + idx)
    if (isConsecutive) {
      return consecutive
    }
  }
  
  return possibleHours.slice(0, lunchHoursCount)
})

// Calculate day schedule with times and lunch breaks
const daySchedule = computed((): ScheduleItem[] => {
  if (!dayEntries.value.length || !schoolSettings.value) {
    return []
  }
  
  const schedule: ScheduleItem[] = []
  const startTime = schoolSettings.value.start_time || '08:00'
  const classHourLength = schoolSettings.value.class_hour_length_minutes || 45
  const defaultBreakDuration = schoolSettings.value.break_duration_minutes || 10
  const breakDurations = schoolSettings.value.break_durations || null
  
  // Helper function to get break duration for a specific break index
  const getBreakDuration = (breakIndex: number): number => {
    // breakIndex 0 = break after lesson 1, breakIndex 1 = break after lesson 2, etc.
    if (breakDurations && breakDurations.length > 0) {
      if (breakIndex < breakDurations.length) {
        return breakDurations[breakIndex]
      } else {
        // Use last value as default for remaining breaks
        return breakDurations[breakDurations.length - 1]
      }
    } else {
      // Fallback to single break_duration_minutes
      return defaultBreakDuration
    }
  }
  
  // Parse start time
  const [startHours, startMinutes] = startTime.split(':').map(Number)
  let currentTime = new Date()
  currentTime.setHours(startHours, startMinutes, 0, 0)
  
  // Get all lesson indices that have entries, sorted
  const lessonIndices = [...new Set(dayEntries.value.map(e => e.lesson_index))].sort((a, b) => a - b)
  const maxLessonIndex = Math.max(...lessonIndices, 1) // Backend uses 1-based indexing
  
  // Backend generates timetables with lesson_index starting from 1
  // So we start from 1, not 0, to match the timetable generation
  for (let lessonIndex = 1; lessonIndex <= maxLessonIndex; lessonIndex++) {
    const entry = dayEntries.value.find(e => e.lesson_index === lessonIndex)
    const isLunchSlot = lunchHourSlots.value.includes(lessonIndex)
    const hasEntry = !!entry
    
    // Calculate lesson start time
    const lessonStartTime = formatTime(currentTime)
    
    // If this is a lunch slot and no entry, add lunch break
    if (isLunchSlot && !hasEntry) {
      const lunchDuration = schoolSettings.value.lunch_duration_minutes || 30
      const lunchEndTime = new Date(currentTime.getTime() + lunchDuration * 60000)
      
      schedule.push({
        key: `lunch-${lessonIndex}`,
        type: 'lunch',
        startTime: lessonStartTime,
        endTime: formatTime(lunchEndTime),
        lessonIndex
      })
      
      currentTime = lunchEndTime
    } else if (hasEntry) {
      // Add lesson entry
      const lessonEndTime = new Date(currentTime.getTime() + classHourLength * 60000)
      
      schedule.push({
        key: `lesson-${entry.id}`,
        type: 'lesson',
        startTime: lessonStartTime,
        endTime: formatTime(lessonEndTime),
        entry,
        lessonIndex
      })
      
      currentTime = lessonEndTime
      
      // Add break after lesson (except after last lesson or if next is lunch)
      const nextIndex = lessonIndex + 1
      if (nextIndex <= maxLessonIndex) {
        const nextIsLunch = lunchHourSlots.value.includes(nextIndex)
        if (!nextIsLunch) {
          // breakIndex = lessonIndex - 1 (break after lesson 1 is at index 0)
          const breakDuration = getBreakDuration(lessonIndex - 1)
          currentTime = new Date(currentTime.getTime() + breakDuration * 60000)
        }
      }
    } else {
      // Empty slot between entries - advance time but don't add to schedule
      // This handles gaps in lesson indices
      currentTime = new Date(currentTime.getTime() + classHourLength * 60000)
      const nextIndex = lessonIndex + 1
      if (nextIndex <= maxLessonIndex) {
        const nextIsLunch = lunchHourSlots.value.includes(nextIndex)
        if (!nextIsLunch) {
          // breakIndex = lessonIndex - 1 (break after lesson 1 is at index 0)
          const breakDuration = getBreakDuration(lessonIndex - 1)
          currentTime = new Date(currentTime.getTime() + breakDuration * 60000)
        }
      }
    }
  }
  
  return schedule
})

function formatTime(date: Date): string {
  const hours = date.getHours().toString().padStart(2, '0')
  const minutes = date.getMinutes().toString().padStart(2, '0')
  return `${hours}:${minutes}`
}

// Watch selected day date to update input
watch(selectedDayDate, (newDate) => {
  selectedDayDateInput.value = newDate.toISOString().split('T')[0]
  if (viewMode.value === 'day') {
    loadDayEntries()
  }
})

// Watch view mode to load entries when switching to day view
watch(viewMode, (newMode) => {
  if (newMode === 'day') {
    loadDayEntries()
  }
})

const calendarDays = computed((): DayInfo[] => {
  const year = currentYear.value
  const month = currentMonth.value
  
  // First day of the month
  const firstDay = new Date(year, month, 1)
  const firstDayOfWeek = (firstDay.getDay() + 6) % 7 // Convert Sunday=0 to Monday=0
  
  // Last day of the month
  const lastDay = new Date(year, month + 1, 0)
  const daysInMonth = lastDay.getDate()
  
  // Previous month's days to fill the first week
  const prevMonth = month === 0 ? 11 : month - 1
  const prevYear = month === 0 ? year - 1 : year
  const prevMonthLastDay = new Date(prevYear, prevMonth + 1, 0).getDate()
  
  const days: DayInfo[] = []
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  
  // Previous month days
  for (let i = firstDayOfWeek - 1; i >= 0; i--) {
    const day = prevMonthLastDay - i
    const date = new Date(prevYear, prevMonth, day)
    days.push(createDayInfo(day, date, true, today))
  }
  
  // Current month days
  for (let day = 1; day <= daysInMonth; day++) {
    const date = new Date(year, month, day)
    days.push(createDayInfo(day, date, false, today))
  }
  
  // Next month days to fill the last week
  const remainingDays = 42 - days.length // 6 weeks * 7 days
  for (let day = 1; day <= remainingDays; day++) {
    const nextMonth = month === 11 ? 0 : month + 1
    const nextYear = month === 11 ? year + 1 : year
    const date = new Date(nextYear, nextMonth, day)
    days.push(createDayInfo(day, date, true, today))
  }
  
  return days
})

function createDayInfo(dayNumber: number, date: Date, isOtherMonth: boolean, today: Date): DayInfo {
  const dateStr = date.toISOString().split('T')[0]
  const isToday = date.getTime() === today.getTime()
  const dayOfWeek = (date.getDay() + 6) % 7 // Monday = 0, Sunday = 6
  
  // Find timetable entries for this date and class
  let entries: TimetableEntry[] = []
  
  // Find valid timetable for this date
  let validTimetable: Timetable | null = null
  for (const timetable of props.timetables) {
    if (timetable.is_primary === 0) {
      // Substitute timetable
      if (timetable.substitute_for_date === dateStr) {
        validTimetable = timetable
        break
      }
    } else {
      // Primary timetable
      if (timetable.valid_from && timetable.valid_to) {
        if (dateStr >= timetable.valid_from && dateStr <= timetable.valid_to) {
          validTimetable = timetable
          // Check if there's a substitute for this date (substitute takes precedence)
          const substitute = props.timetables.find(
            t => t.is_primary === 0 && t.substitute_for_date === dateStr
          )
          if (substitute) {
            validTimetable = substitute
            break
          }
        }
      }
    }
  }
  
  if (validTimetable && validTimetable.entries) {
    // Filter by class if selected
    entries = validTimetable.entries.filter(entry => {
      if (selectedClassId.value && entry.class_group_id !== selectedClassId.value) {
        return false
      }
      // Check if entry is for this day of week (Monday = 0, Friday = 4)
      return entry.day_of_week === dayOfWeek
    })
  }
  
  // Create preview (max 3 entries)
  const entriesPreview = entries.slice(0, 3).map(entry => ({
    subject: entry.subject?.name || 'N/A',
    lesson: entry.lesson_index + 1
  }))
  
  return {
    key: `${date.getFullYear()}-${date.getMonth()}-${dayNumber}`,
    dayNumber,
    date,
    isOtherMonth,
    isToday,
    entriesCount: entries.length,
    entriesPreview
  }
}

function previousMonth() {
  currentDate.value = new Date(currentYear.value, currentMonth.value - 1, 1)
}

function nextMonth() {
  currentDate.value = new Date(currentYear.value, currentMonth.value + 1, 1)
}

function previousDay() {
  const newDate = new Date(selectedDayDate.value)
  newDate.setDate(newDate.getDate() - 1)
  selectedDayDate.value = newDate
}

function nextDay() {
  const newDate = new Date(selectedDayDate.value)
  newDate.setDate(newDate.getDate() + 1)
  selectedDayDate.value = newDate
}

function goToToday() {
  selectedDayDate.value = new Date()
}

function onDayDateChange() {
  if (selectedDayDateInput.value) {
    selectedDayDate.value = new Date(selectedDayDateInput.value)
  }
}

function selectDate(date: Date) {
  if (viewMode.value === 'month') {
    selectedDayDate.value = date
    viewMode.value = 'day'
  } else {
    emit('dateSelected', date)
  }
}

async function loadClassGroups() {
  try {
    const response = await api.get('/class-groups/')
    classGroups.value = response.data
  } catch (err: any) {
    console.error('Failed to load class groups:', err)
  }
}

async function loadDayEntries() {
  if (!selectedClassId.value) {
    dayEntries.value = []
    return
  }
  
  loadingDayEntries.value = true
  try {
    const dateStr = selectedDayDate.value.toISOString().split('T')[0]
    const dayOfWeek = (selectedDayDate.value.getDay() + 6) % 7 // Monday = 0
    
    // Find valid timetable for this date
    let validTimetable: Timetable | null = null
    for (const timetable of props.timetables) {
      if (timetable.is_primary === 0) {
        if (timetable.substitute_for_date === dateStr) {
          validTimetable = timetable
          break
        }
      } else {
        if (timetable.valid_from && timetable.valid_to) {
          if (dateStr >= timetable.valid_from && dateStr <= timetable.valid_to) {
            validTimetable = timetable
            const substitute = props.timetables.find(
              t => t.is_primary === 0 && t.substitute_for_date === dateStr
            )
            if (substitute) {
              validTimetable = substitute
              break
            }
          }
        }
      }
    }
    
    if (validTimetable) {
      // Load full timetable with entries
      const schoolId = authStore.user?.school_id
      if (schoolId) {
        const response = await api.get(`/timetables/schools/${schoolId}/timetables/${validTimetable.id}`)
        const timetable = response.data
        
        // Filter entries by class and day of week
        dayEntries.value = (timetable.entries || []).filter((entry: TimetableEntry) => {
          return entry.class_group_id === selectedClassId.value && entry.day_of_week === dayOfWeek
        }).sort((a: TimetableEntry, b: TimetableEntry) => a.lesson_index - b.lesson_index)
      }
    } else {
      dayEntries.value = []
    }
  } catch (err: any) {
    console.error('Failed to load day entries:', err)
    dayEntries.value = []
  } finally {
    loadingDayEntries.value = false
  }
}

function onClassChange() {
  if (viewMode.value === 'day') {
    loadDayEntries()
  }
}

async function loadSchoolSettings() {
  try {
    const schoolId = authStore.user?.school_id
    if (schoolId) {
      const response = await api.get(`/schools/${schoolId}/settings`)
      schoolSettings.value = response.data
    }
  } catch (err: any) {
    console.error('Failed to load school settings:', err)
  }
}

onMounted(() => {
  loadClassGroups()
  loadSchoolSettings()
})
</script>

<style lang="scss" scoped>
@import '../styles/neo.scss';

.timetable-calendar {
  @extend %neo-panel;
  padding: 1.5rem;
  position: relative;
  z-index: 1;

  &__class-selector {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 1rem;
  }

  &__label {
    font-weight: 600;
    color: $neo-text;
  }

  &__select {
    @extend %neo-input;
    flex: 1;
    max-width: 300px;
    padding: 0.75rem;
    border-radius: 12px;
    font-size: 1rem;
  }

  &__view-toggle {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 1rem;
  }

  &__toggle-button {
    @extend %neo-button;
    flex: 1;
    padding: 0.75rem;
    cursor: pointer;
    font-size: 1rem;
    font-weight: 600;

    &--active {
      @include neo-inset(12px, 0.6);
      background: $neo-bg-light;
    }
  }

  &__header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
  }

  &__nav-button {
    @extend %neo-button;
    width: 2rem;
    height: 2rem;
    border-radius: 10px;
    font-size: 1.5rem;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  &__month-year {
    margin: 0;
    font-size: 1.25rem;
    font-weight: 600;
    color: $neo-text;
  }

  &__weekdays {
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    gap: 0.5rem;
    margin-bottom: 0.5rem;
  }

  &__weekday {
    text-align: center;
    font-weight: 600;
    color: $neo-text;
    font-size: 0.875rem;
    padding: 0.5rem;
  }

  &__days {
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    gap: 0.5rem;
  }

  &__day {
    @include neo-surface(12px, 0.6);
    min-height: 100px;
    padding: 0.5rem;
    cursor: pointer;
    display: flex;
    flex-direction: column;
    position: relative;
    transition: all 0.3s ease;

    &:hover:not(&--other-month) {
      @include neo-surface(12px, 0.8);
      transform: translateY(-2px);
    }

    &--other-month {
      opacity: 0.3;
      cursor: default;
    }

    &--today {
      @include neo-surface(12px, 1);
      border: 2px solid $neo-accent;
    }

    &--has-entries {
      @include neo-surface(12px, 0.8);
    }
  }

  &__day-number {
    font-weight: 600;
    color: $neo-text;
    font-size: 0.875rem;
    margin-bottom: 0.25rem;
  }

  &__day-entries {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  &__entries-count {
    font-size: 0.75rem;
    color: $neo-text;
    font-weight: 600;
    margin-bottom: 0.25rem;
  }

  &__entries-preview {
    display: flex;
    flex-direction: column;
    gap: 0.125rem;
  }

  &__entry-preview {
    font-size: 0.625rem;
    color: $neo-text-light;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  // Day View Styles
  &__day-view {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  &__day-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  &__day-title {
    margin: 0;
    font-size: 1.5rem;
    font-weight: 600;
    color: $neo-text;
  }

  &__day-selector {
    display: flex;
    gap: 1rem;
    align-items: center;
  }

  &__date-input {
    @extend %neo-input;
    padding: 0.75rem;
    border-radius: 12px;
    font-size: 1rem;
  }

  &__today-button {
    @extend %neo-button;
    padding: 0.75rem 1.5rem;
    border-radius: 12px;
    font-size: 1rem;
    font-weight: 600;
  }

  &__day-timetable {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  &__day-item {
    @extend %neo-list-item;
    display: flex;
    gap: 1rem;
    padding: 1rem;
    border-left: 3px solid $neo-accent;
    margin-bottom: 0.5rem;

    &:hover {
      @include neo-surface(16px, 0.8);
      transform: translateX(4px);
    }

    &--lunch {
      background: lighten(#ff9800, 35%);
      border-left-color: #ff9800;
    }
  }

  &__item-time {
    min-width: 120px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    font-weight: 600;
    color: $neo-text;
  }

  &__time-start {
    font-size: 1rem;
  }

  &__time-end {
    font-size: 0.875rem;
    color: $neo-text-muted;
    font-weight: 400;
  }

  &__lunch-break {
    flex: 1;
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 0.5rem;
  }

  &__lunch-icon {
    font-size: 1.5rem;
  }

  &__lunch-text {
    font-size: 1.125rem;
    font-weight: 600;
    color: darken(#ff9800, 20%);
  }

  &__entry-details {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  &__entry-subject {
    font-size: 1.125rem;
    font-weight: 600;
    color: $neo-text;
  }

  &__entry-info {
    display: flex;
    gap: 1rem;
    font-size: 0.875rem;
    color: $neo-text-light;
  }

  &__entry-teacher {
    font-weight: 500;
  }

  &__entry-classroom {
    color: $neo-text-muted;
  }

  &__loading {
    text-align: center;
    padding: 2rem;
    color: $neo-text-light;
  }

  &__empty {
    text-align: center;
    padding: 3rem;
    color: $neo-text-muted;
    font-style: italic;
  }
}
</style>
