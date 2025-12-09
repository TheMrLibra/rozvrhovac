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
              <div class="school-settings-view__field">
                <label class="school-settings-view__label">
                  Break Duration (minutes)
                  <span class="school-settings-view__required">*</span>
                </label>
                <input
                  v-model.number="settings.break_duration_minutes"
                  type="number"
                  min="0"
                  class="school-settings-view__input"
                  required
                />
                <small class="school-settings-view__hint">Duration of breaks between lessons</small>
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
@import '../styles/glass.scss';

.school-settings-view {
  min-height: 100vh;
  position: relative;
  z-index: 1;

  &__header {
    @extend %glass-header;
    padding: 1.5rem 2rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    position: sticky;
    top: 0;
    z-index: 100;
  }

  &__title {
    color: rgba(255, 255, 255, 0.95);
    margin: 0;
    font-size: 1.75rem;
    font-weight: 700;
    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  }

  &__back {
    padding: 0.75rem 1.5rem;
    background: rgba(108, 117, 125, 0.3);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.2);
    color: rgba(255, 255, 255, 0.95);
    text-decoration: none;
    border-radius: 12px;
    font-weight: 500;
    transition: all 0.3s ease;

    &:hover {
      background: rgba(108, 117, 125, 0.4);
      border-color: rgba(255, 255, 255, 0.3);
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    }
  }

  &__content {
    padding: 2rem;
    max-width: 900px;
    margin: 0 auto;
    position: relative;
    z-index: 1;
  }

  &__form-container {
    @extend %glass-panel;
    padding: 2.5rem;
  }

  &__header-section {
    margin-bottom: 2rem;
    padding-bottom: 1.5rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.15);
  }

  &__form-title {
    color: rgba(255, 255, 255, 0.95);
    margin: 0 0 0.5rem 0;
    font-size: 1.75rem;
    font-weight: 700;
    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  }

  &__form-description {
    color: rgba(255, 255, 255, 0.8);
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
    @include glass-effect(0.1, 16px);
    padding: 1.5rem;
    border-radius: 16px;
  }

  &__section-title {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin: 0 0 1.25rem 0;
    color: rgba(255, 255, 255, 0.95);
    font-size: 1.25rem;
    font-weight: 600;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
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
    color: rgba(255, 255, 255, 0.95);
    font-size: 0.95rem;
    display: flex;
    align-items: center;
    gap: 0.25rem;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
  }

  &__required {
    color: rgba(255, 100, 100, 0.9);
    font-weight: 700;
  }

  &__input {
    @extend %glass-input;
    padding: 0.875rem;
    border-radius: 12px;
    font-size: 1rem;
    transition: all 0.3s ease;
  }

  &__hint {
    color: rgba(255, 255, 255, 0.7);
    font-size: 0.875rem;
    margin-top: 0.25rem;
    line-height: 1.4;
  }

  &__actions {
    display: flex;
    justify-content: flex-end;
    padding-top: 1rem;
    border-top: 1px solid rgba(255, 255, 255, 0.15);
  }

  &__button {
    @extend %glass-button;
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
    margin-top: 1.5rem;
    padding: 1rem 1.25rem;
    border-radius: 12px;
    display: flex;
    align-items: center;
    gap: 0.75rem;
    font-weight: 500;
    animation: slideIn 0.3s ease-out;
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);

    &--error {
      background: rgba(220, 53, 69, 0.2);
      color: rgba(255, 200, 200, 0.95);
      border: 1px solid rgba(220, 53, 69, 0.3);
    }

    &--success {
      background: rgba(40, 167, 69, 0.2);
      color: rgba(200, 255, 200, 0.95);
      border: 1px solid rgba(40, 167, 69, 0.3);
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
