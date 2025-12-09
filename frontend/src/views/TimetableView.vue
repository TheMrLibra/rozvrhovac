<template>
  <div class="timetable-view">
    <header class="timetable-view__header">
      <h1 class="timetable-view__title">Timetable</h1>
      <div class="timetable-view__controls">
        <select
          v-model="selectedClassId"
          class="timetable-view__class-select"
          @change="onClassChange"
        >
          <option :value="null">Select a class...</option>
          <option
            v-for="classGroup in classGroups"
            :key="classGroup.id"
            :value="classGroup.id"
          >
            {{ classGroup.name }}
          </option>
        </select>
        <router-link to="/timetables" class="timetable-view__back">All Timetables</router-link>
        <router-link to="/dashboard" class="timetable-view__back">Dashboard</router-link>
      </div>
    </header>
    <main class="timetable-view__content">
      <div v-if="loading" class="timetable-view__loading">Loading timetable...</div>
      <div v-else-if="!selectedClassId" class="timetable-view__empty">
        Please select a class to view its timetable
      </div>
      <TimetableGrid
        v-else-if="timetable && filteredEntries.length > 0"
        :timetable="{ ...timetable, entries: filteredEntries }"
        :lunch-hours="actualLunchHours"
      />
      <div v-else-if="timetable && filteredEntries.length === 0" class="timetable-view__empty">
        No timetable entries found for this class
      </div>
      <div v-else class="timetable-view__empty">
        No timetable available. Please generate one first.
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import api from '@/services/api'
import TimetableGrid from '@/components/TimetableGrid.vue'

interface ClassGroup {
  id: number
  name: string
}

const route = useRoute()
const authStore = useAuthStore()
const timetable = ref<any>(null)
const classGroups = ref<ClassGroup[]>([])
const selectedClassId = ref<number | null>(null)
const loading = ref(false)
const schoolSettings = ref<any>(null)

const filteredEntries = computed(() => {
  if (!timetable.value || !selectedClassId.value) return []
  return timetable.value.entries.filter(
    (entry: any) => entry.class_group_id === selectedClassId.value
  )
})

// Calculate actual lunch hour slots (consecutive hours based on duration)
const actualLunchHours = computed(() => {
  if (!schoolSettings.value?.possible_lunch_hours || !schoolSettings.value?.lunch_duration_minutes || !schoolSettings.value?.class_hour_length_minutes) {
    return []
  }
  
  // Calculate how many class hours needed (round up)
  const lunchHoursCount = Math.ceil(schoolSettings.value.lunch_duration_minutes / schoolSettings.value.class_hour_length_minutes)
  const possibleHours = [...schoolSettings.value.possible_lunch_hours].sort((a, b) => a - b)
  
  // Find consecutive hours
  for (let i = 0; i <= possibleHours.length - lunchHoursCount; i++) {
    const consecutive = possibleHours.slice(i, i + lunchHoursCount)
    // Check if they are consecutive
    const isConsecutive = consecutive.every((hour, idx) => hour === consecutive[0] + idx)
    if (isConsecutive) {
      return consecutive
    }
  }
  
  // If no consecutive hours found, use first N hours
  return possibleHours.slice(0, lunchHoursCount)
})

async function loadClassGroups() {
  try {
    const schoolId = authStore.user?.school_id
    if (schoolId) {
      const response = await api.get(`/class-groups/`)
      classGroups.value = response.data
    }
  } catch (error) {
    console.error('Failed to load class groups:', error)
  }
}

async function loadSchoolSettings() {
  try {
    const schoolId = authStore.user?.school_id
    if (schoolId) {
      const response = await api.get(`/schools/${schoolId}/settings`)
      schoolSettings.value = response.data
    }
  } catch (error) {
    console.error('Failed to load school settings:', error)
  }
}

async function loadTimetable() {
  loading.value = true
  try {
    const schoolId = authStore.user?.school_id
    if (schoolId) {
      // Get timetable ID from route params or use first available
      const timetableId = route.params.timetableId
      
      if (timetableId && typeof timetableId === 'string') {
        // Load specific timetable
        const fullTimetable = await api.get(`/timetables/schools/${schoolId}/timetables/${timetableId}`)
        timetable.value = fullTimetable.data
      } else {
        // Load first available timetable
        const response = await api.get(`/timetables/schools/${schoolId}/timetables`)
        if (response.data.length > 0) {
          const fullTimetable = await api.get(`/timetables/schools/${schoolId}/timetables/${response.data[0].id}`)
          timetable.value = fullTimetable.data
        }
      }
      
      // Auto-select first class if available
      if (classGroups.value.length > 0 && !selectedClassId.value) {
        selectedClassId.value = classGroups.value[0].id
      }
    }
  } catch (error) {
    console.error('Failed to load timetable:', error)
  } finally {
    loading.value = false
  }
}

function onClassChange() {
  // Class change handled by computed property
}

onMounted(async () => {
  await loadClassGroups()
  await loadSchoolSettings()
  await loadTimetable()
})
</script>

<style lang="scss" scoped>
.timetable-view {
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

  &__controls {
    display: flex;
    gap: 1rem;
    align-items: center;
  }

  &__class-select {
    padding: 0.5rem 1rem;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 1rem;
    background-color: white;
    cursor: pointer;

    &:hover {
      border-color: #4a90e2;
    }

    &:focus {
      outline: none;
      border-color: #4a90e2;
      box-shadow: 0 0 0 2px rgba(74, 144, 226, 0.2);
    }
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
  }

  &__loading {
    text-align: center;
    padding: 2rem;
    color: #666;
  }

  &__empty {
    text-align: center;
    padding: 3rem;
    color: #666;
    background: white;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  }
}
</style>

