<template>
  <div class="school-settings-view">
    <header class="school-settings-view__header">
      <h1 class="school-settings-view__title">School Settings</h1>
      <router-link to="/dashboard" class="school-settings-view__back">Dashboard</router-link>
    </header>
    <main class="school-settings-view__content">
      <div class="school-settings-view__form-container">
        <div class="school-settings-view__header-section">
          <h2 class="school-settings-view__form-title">Configure School Settings</h2>
          <p class="school-settings-view__form-description">
            Manage your school's timetable configuration including class hours, breaks, and lunch periods.
          </p>
        </div>
        
        <form @submit.prevent="saveSettings" class="school-settings-view__form">
          <!-- Time Settings Section -->
          <div class="school-settings-view__section">
            <h3 class="school-settings-view__section-title">
              <span class="school-settings-view__section-icon">🕐</span>
              Time Settings
            </h3>
            <div class="school-settings-view__fields-grid">
              <div class="school-settings-view__field">
                <label class="school-settings-view__label">
                  Start Time
                  <span class="school-settings-view__required">*</span>
                </label>
                <input
                  v-model="settings.start_time"
                  type="time"
                  class="school-settings-view__input"
                  required
                />
                <small class="school-settings-view__hint">School day start time</small>
              </div>
              <div class="school-settings-view__field">
                <label class="school-settings-view__label">
                  End Time
                  <span class="school-settings-view__required">*</span>
                </label>
                <input
                  v-model="settings.end_time"
                  type="time"
                  class="school-settings-view__input"
                  required
                />
                <small class="school-settings-view__hint">School day end time</small>
              </div>
            </div>
          </div>

          <!-- Class Hour Settings Section -->
          <div class="school-settings-view__section">
            <h3 class="school-settings-view__section-title">
              <span class="school-settings-view__section-icon">📚</span>
              Class Hour Settings
            </h3>
            <div class="school-settings-view__fields-grid">
              <div class="school-settings-view__field">
                <label class="school-settings-view__label">
                  Class Hour Length (minutes)
                  <span class="school-settings-view__required">*</span>
                </label>
                <input
                  v-model.number="settings.class_hour_length_minutes"
                  type="number"
                  min="1"
                  class="school-settings-view__input"
                  required
                />
                <small class="school-settings-view__hint">Duration of each class period</small>
              </div>
            </div>
          </div>

          <!-- Break Settings Section -->
          <div class="school-settings-view__section">
            <h3 class="school-settings-view__section-title">
              <span class="school-settings-view__section-icon">☕</span>
              Break Settings
            </h3>
            <div class="school-settings-view__fields-grid">
              <div class="school-settings-view__field school-settings-view__field--full">
                <label class="school-settings-view__label">
                  Break Durations (minutes)
                </label>
                <input
                  v-model="breakDurationsInput"
                  type="text"
                  placeholder="5,20,10,10,10,10,10"
                  class="school-settings-view__input"
                />
                <small class="school-settings-view__hint">
                  Comma-separated break durations in minutes. Each value represents the break duration after that lesson (e.g., "5,20,10" means 5min after lesson 1, 20min after lesson 2, 10min after lesson 3+). If fewer values are provided, the last value is used for remaining breaks.
                </small>
              </div>
              <div class="school-settings-view__field">
                <label class="school-settings-view__label">
                  Default Break Duration (minutes)
                  <span class="school-settings-view__required">*</span>
                </label>
                <input
                  v-model.number="settings.break_duration_minutes"
                  type="number"
                  min="0"
                  class="school-settings-view__input"
                  required
                />
                <small class="school-settings-view__hint">Fallback duration if break_durations is not set</small>
              </div>
            </div>
          </div>

          <!-- Lunch Settings Section -->
          <div class="school-settings-view__section">
            <h3 class="school-settings-view__section-title">
              <span class="school-settings-view__section-icon">🍽️</span>
              Lunch Settings
            </h3>
            <div class="school-settings-view__fields-grid">
              <div class="school-settings-view__field">
                <label class="school-settings-view__label">
                  Lunch Duration (minutes)
                  <span class="school-settings-view__required">*</span>
                </label>
                <input
                  v-model.number="settings.lunch_duration_minutes"
                  type="number"
                  min="0"
                  class="school-settings-view__input"
                  required
                />
                <small class="school-settings-view__hint">Duration of lunch break</small>
              </div>
              <div class="school-settings-view__field school-settings-view__field--full">
                <label class="school-settings-view__label">
                  Possible Lunch Hours
                </label>
                <input
                  v-model="lunchHoursInput"
                  type="text"
                  placeholder="3,4,5"
                  class="school-settings-view__input"
                />
                <small class="school-settings-view__hint">
                  Comma-separated lesson indices when lunch is possible (e.g., 3,4,5). 
                  Lesson indices start from 1.
                </small>
              </div>
            </div>
          </div>

          <div class="school-settings-view__actions">
            <button type="submit" class="school-settings-view__button" :disabled="loading">
              <span v-if="loading" class="school-settings-view__button-spinner">⏳</span>
              {{ loading ? 'Saving...' : 'Save Settings' }}
            </button>
          </div>
        </form>
        
        <div v-if="error" class="school-settings-view__message school-settings-view__message--error">
          <span class="school-settings-view__message-icon">⚠️</span>
          {{ error }}
        </div>
        <div v-if="success" class="school-settings-view__message school-settings-view__message--success">
          <span class="school-settings-view__message-icon">✓</span>
          {{ success }}
        </div>
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
  break_durations: null as number[] | null,
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

const breakDurationsInput = computed({
  get: () => settings.value.break_durations?.join(',') || '',
  set: (value: string) => {
    if (value.trim()) {
      settings.value.break_durations = value.split(',').map(v => parseInt(v.trim())).filter(v => !isNaN(v))
    } else {
      settings.value.break_durations = null
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
      break_durations: data.break_durations || null,
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
    
    // Clear success message after 3 seconds
    setTimeout(() => {
      success.value = ''
    }, 3000)
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
@import '../styles/neo.scss';

.school-settings-view {
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
    margin: 0;
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
    max-width: 900px;
    margin: 0 auto;
    position: relative;
    z-index: 1;
  }

  &__form-container {
    @extend %neo-panel;
    padding: 2.5rem;
  }

  &__header-section {
    margin-bottom: 2rem;
    padding-bottom: 1.5rem;
    border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  }

  &__form-title {
    color: $neo-text;
    margin: 0 0 0.5rem 0;
    font-size: 1.75rem;
    font-weight: 700;
  }

  &__form-description {
    color: $neo-text-light;
    margin: 0;
    font-size: 1rem;
    line-height: 1.6;
  }

  &__form {
    display: flex;
    flex-direction: column;
    gap: 2rem;
  }

  &__section {
    @include neo-surface(16px, 0.8);
    padding: 1.5rem;
    background: $neo-bg-light;
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

  &__fields-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 1.5rem;
  }

  &__field {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;

    &--full {
      grid-column: 1 / -1;
    }
  }

  &__label {
    font-weight: 600;
    color: $neo-text;
    font-size: 0.95rem;
    display: flex;
    align-items: center;
    gap: 0.25rem;
  }

  &__required {
    color: #dc3545;
    font-weight: 700;
  }

  &__input {
    @extend %neo-input;
    padding: 0.875rem;
    font-size: 1rem;
  }

  &__hint {
    color: $neo-text-muted;
    font-size: 0.875rem;
    margin-top: 0.25rem;
    line-height: 1.4;
  }

  &__actions {
    display: flex;
    justify-content: flex-end;
    padding-top: 1rem;
    border-top: 1px solid rgba(0, 0, 0, 0.05);
  }

  &__button {
    @extend %neo-button;
    @extend %neo-button--primary;
    padding: 1rem 2.5rem;
    border-radius: 12px;
    font-size: 1.1rem;
    font-weight: 600;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 0.5rem;

    &:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
  }

  &__button-spinner {
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    from {
      transform: rotate(0deg);
    }
    to {
      transform: rotate(360deg);
    }
  }

  &__message {
    @extend %neo-message;
    margin-top: 1.5rem;
    padding: 1rem 1.25rem;
    border-radius: 12px;
    display: flex;
    align-items: center;
    gap: 0.75rem;
    font-weight: 500;
    animation: slideIn 0.3s ease-out;

    &--error {
      @extend %neo-message--error;
    }

    &--success {
      @extend %neo-message--success;
    }
  }

  &__message-icon {
    font-size: 1.25rem;
  }

  @keyframes slideIn {
    from {
      opacity: 0;
      transform: translateY(-10px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
}

@media (max-width: 768px) {
  .school-settings-view {
    &__content {
      padding: 1rem;
    }

    &__form-container {
      padding: 1.5rem;
    }

    &__fields-grid {
      grid-template-columns: 1fr;
    }

    &__field--full {
      grid-column: 1;
    }
  }
}
</style>
