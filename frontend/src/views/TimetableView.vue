<template>
  <div class="timetable-view">
    <header class="timetable-view__header">
      <h1 class="timetable-view__title">Timetable</h1>
      <router-link to="/dashboard" class="timetable-view__back">Back</router-link>
    </header>
    <main class="timetable-view__content">
      <TimetableGrid v-if="timetable" :timetable="timetable" />
      <div v-else class="timetable-view__loading">Loading timetable...</div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import api from '@/services/api'
import TimetableGrid from '@/components/TimetableGrid.vue'

const authStore = useAuthStore()
const timetable = ref(null)

onMounted(async () => {
  try {
    const schoolId = authStore.user?.school_id
    if (schoolId) {
      const response = await api.get(`/timetables/schools/${schoolId}/timetables`)
      if (response.data.length > 0) {
        const fullTimetable = await api.get(`/timetables/schools/${schoolId}/timetables/${response.data[0].id}`)
        timetable.value = fullTimetable.data
      }
    }
  } catch (error) {
    console.error('Failed to load timetable:', error)
  }
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
}
</style>

