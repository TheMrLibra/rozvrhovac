<template>
  <div class="school-settings-view">
    <header class="school-settings-view__header">
      <h1 class="school-settings-view__title">School Settings</h1>
      <router-link to="/dashboard" class="school-settings-view__back">Dashboard</router-link>
    </header>
    <main class="school-settings-view__content">
      <div class="school-settings-view__form-container">
        <h2>Configure School Settings</h2>
        <form @submit.prevent="saveSettings" class="school-settings-view__form">
          <div class="school-settings-view__field">
            <label class="school-settings-view__label">Start Time</label>
            <input
              v-model="settings.start_time"
              type="time"
              class="school-settings-view__input"
              required
            />
          </div>
          <div class="school-settings-view__field">
            <label class="school-settings-view__label">End Time</label>
            <input
              v-model="settings.end_time"
              type="time"
              class="school-settings-view__input"
              required
            />
          </div>
          <div class="school-settings-view__field">
            <label class="school-settings-view__label">Class Hour Length (minutes)</label>
            <input
              v-model.number="settings.class_hour_length_minutes"
              type="number"
              min="1"
              class="school-settings-view__input"
              required
            />
          </div>
          <div class="school-settings-view__field">
            <label class="school-settings-view__label">Break Duration (minutes)</label>
            <input
              v-model.number="settings.break_duration_minutes"
              type="number"
              min="0"
              class="school-settings-view__input"
              required
            />
          </div>
          <div class="school-settings-view__field">
            <label class="school-settings-view__label">Lunch Duration (minutes)</label>
            <input
              v-model.number="settings.lunch_duration_minutes"
              type="number"
              min="0"
              class="school-settings-view__input"
              required
            />
          </div>
          <div class="school-settings-view__field">
            <label class="school-settings-view__label">Possible Lunch Hours (comma-separated, e.g., 3,4,5)</label>
            <input
              v-model="lunchHoursInput"
              type="text"
              placeholder="3,4,5"
              class="school-settings-view__input"
            />
            <small class="school-settings-view__hint">Lesson indices when lunch is possible</small>
          </div>
          <button type="submit" class="school-settings-view__button" :disabled="loading">
            {{ loading ? 'Saving...' : 'Save Settings' }}
          </button>
        </form>
        <div v-if="error" class="school-settings-view__error">{{ error }}</div>
        <div v-if="success" class="school-settings-view__success">{{ success }}</div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import api from '@/services/api'

const authStore = useAuthStore()
const loading = ref(false)
const error = ref('')
const success = ref('')

const settings = ref({
  start_time: '08:00',
  end_time: '16:00',
  class_hour_length_minutes: 45,
  break_duration_minutes: 10,
  lunch_duration_minutes: 30,
  possible_lunch_hours: [] as number[]
})

const lunchHoursInput = computed({
  get: () => settings.value.possible_lunch_hours?.join(',') || '',
  set: (value: string) => {
    if (value.trim()) {
      settings.value.possible_lunch_hours = value.split(',').map(v => parseInt(v.trim())).filter(v => !isNaN(v))
    } else {
      settings.value.possible_lunch_hours = []
    }
  }
})

async function loadSettings() {
  try {
    const schoolId = authStore.user?.school_id
    if (!schoolId) return
    
    const response = await api.get(`/schools/${schoolId}/settings`)
    const data = response.data
    settings.value = {
      start_time: data.start_time || '08:00',
      end_time: data.end_time || '16:00',
      class_hour_length_minutes: data.class_hour_length_minutes || 45,
      break_duration_minutes: data.break_duration_minutes || 10,
      lunch_duration_minutes: data.lunch_duration_minutes || 30,
      possible_lunch_hours: data.possible_lunch_hours || []
    }
  } catch (err: any) {
    if (err.response?.status !== 404) {
      error.value = err.response?.data?.detail || 'Failed to load settings'
    }
  }
}

async function saveSettings() {
  loading.value = true
  error.value = ''
  success.value = ''
  
  try {
    const schoolId = authStore.user?.school_id
    if (!schoolId) {
      throw new Error('School ID not found')
    }
    
    await api.put(`/schools/${schoolId}/settings`, settings.value)
    success.value = 'Settings saved successfully'
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to save settings'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadSettings()
})
</script>

<style lang="scss" scoped>
.school-settings-view {
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

  &__form-container {
    background: white;
    padding: 2rem;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  }
}
</style>

