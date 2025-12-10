<template>
  <div class="school-settings-view">
    <header class="school-settings-view__header">
      <h1 class="school-settings-view__title">{{ t('schoolSettings.title') }}</h1>
      <router-link to="/dashboard" class="school-settings-view__back">{{ t('common.dashboard') }}</router-link>
    </header>
    <main class="school-settings-view__content">
      <div class="school-settings-view__form-container">
        <div class="school-settings-view__header-section">
          <h2 class="school-settings-view__form-title">{{ t('schoolSettings.configureSettings') }}</h2>
          <p class="school-settings-view__form-description">
            {{ t('schoolSettings.configureDescription') }}
          </p>
        </div>
        
        <form @submit.prevent="saveSettings" class="school-settings-view__form">
          <div class="school-settings-view__sections-grid">
            <!-- Left Column -->
            <div class="school-settings-view__column">
              <!-- Time Settings Section -->
              <div class="school-settings-view__section">
                <h3 class="school-settings-view__section-title">
                  <span class="school-settings-view__section-icon">🕐</span>
                  {{ t('schoolSettings.timeSettings') }}
                </h3>
                <div class="school-settings-view__fields-grid">
                  <div class="school-settings-view__field">
                    <label class="school-settings-view__label">
                      {{ t('schoolSettings.startTime') }}
                      <span class="school-settings-view__required">*</span>
                    </label>
                    <input
                      v-model="settings.start_time"
                      type="time"
                      class="school-settings-view__input"
                      required
                    />
                    <small class="school-settings-view__hint">{{ t('schoolSettings.schoolDayStart') }}</small>
                  </div>
                  <div class="school-settings-view__field">
                    <label class="school-settings-view__label">
                      {{ t('schoolSettings.endTime') }}
                      <span class="school-settings-view__required">*</span>
                    </label>
                    <input
                      v-model="settings.end_time"
                      type="time"
                      class="school-settings-view__input"
                      required
                    />
                    <small class="school-settings-view__hint">{{ t('schoolSettings.schoolDayEnd') }}</small>
                  </div>
                </div>
              </div>

              <!-- Class Hour Settings Section -->
              <div class="school-settings-view__section">
                <h3 class="school-settings-view__section-title">
                  <span class="school-settings-view__section-icon">📚</span>
                  {{ t('schoolSettings.classHourSettings') }}
                </h3>
                <div class="school-settings-view__fields-grid">
                  <div class="school-settings-view__field">
                    <label class="school-settings-view__label">
                      {{ t('schoolSettings.classHourLength') }}
                      <span class="school-settings-view__required">*</span>
                    </label>
                    <input
                      v-model.number="settings.class_hour_length_minutes"
                      type="number"
                      min="1"
                      class="school-settings-view__input"
                      required
                    />
                    <small class="school-settings-view__hint">{{ t('schoolSettings.durationOfPeriod') }}</small>
                  </div>
                </div>
              </div>

                            <!-- Lunch Settings Section -->
                            <div class="school-settings-view__section">
                <h3 class="school-settings-view__section-title">
                  <span class="school-settings-view__section-icon">🍽️</span>
                  {{ t('schoolSettings.lunchSettings') }}
                </h3>
                <div class="school-settings-view__fields-grid">
                  <div class="school-settings-view__field">
                    <label class="school-settings-view__label">
                      {{ t('schoolSettings.lunchDuration') }}
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
                      {{ t('schoolSettings.possibleLunchHours') }}
                    </label>
                    <input
                      v-model="lunchHoursInput"
                      type="text"
                      placeholder="3,4,5"
                      class="school-settings-view__input"
                    />
                    <small class="school-settings-view__hint">
                      {{ t('schoolSettings.commaSeparatedHours') }}
                    </small>
                  </div>
                </div>
              </div>
            </div>

            <!-- Right Column -->
            <div class="school-settings-view__column">
              <!-- Break Settings Section -->
              <div class="school-settings-view__section">
                <h3 class="school-settings-view__section-title">
                  <span class="school-settings-view__section-icon">☕</span>
                  {{ t('schoolSettings.breakSettings') }}
                </h3>
                <div class="school-settings-view__fields-grid">
                  <div class="school-settings-view__field school-settings-view__field--full">
                    <label class="school-settings-view__label">
                      {{ t('schoolSettings.breakDurations') }}
                    </label>
                    <div class="school-settings-view__break-durations">
                      <div
                        v-for="(_, index) in breakDurationsList"
                        :key="index"
                        class="school-settings-view__break-item"
                      >
                        <div class="school-settings-view__break-label">
                          <span class="school-settings-view__break-number">{{ t('commonPhrases.back') }} {{ index + 1 }}</span>
                          <span class="school-settings-view__break-description">{{ t('schoolSettings.breakAfterLesson') }} {{ index + 1 }}</span>
                        </div>
                        <input
                          v-model.number="breakDurationsList[index]"
                          type="number"
                          min="0"
                          class="school-settings-view__input school-settings-view__input--break"
                          placeholder="10"
                          @input="updateBreakDurations"
                        />
                        <span class="school-settings-view__break-unit">min</span>
                        <button
                          v-if="breakDurationsList.length > 1"
                          type="button"
                          @click="removeBreak(index)"
                          class="school-settings-view__break-remove"
                          :title="t('schoolSettings.removeBreak')"
                        >
                          ×
                        </button>
                      </div>
                      <button
                        type="button"
                        @click="addBreak"
                        class="school-settings-view__break-add"
                      >
                        + {{ t('schoolSettings.addBreak') }}
                      </button>
                    </div>
                    <small class="school-settings-view__hint">
                      {{ t('schoolSettings.setBreakDurations') }}
                    </small>
                  </div>
                  <div class="school-settings-view__field">
                    <label class="school-settings-view__label">
                      {{ t('schoolSettings.defaultBreakDuration') }}
                      <span class="school-settings-view__required">*</span>
                    </label>
                    <input
                      v-model.number="settings.break_duration_minutes"
                      type="number"
                      min="0"
                      class="school-settings-view__input"
                      required
                    />
                    <small class="school-settings-view__hint">{{ t('schoolSettings.fallbackDuration') }}</small>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="school-settings-view__actions">
            <button type="submit" class="school-settings-view__button" :disabled="loading">
              <span v-if="loading" class="school-settings-view__button-spinner">⏳</span>
              {{ loading ? t('schoolSettings.saving') : t('schoolSettings.saveSettings') }}
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
import { useI18nStore } from '@/stores/i18n'
import api from '@/services/api'

const authStore = useAuthStore()
const i18nStore = useI18nStore()
const t = i18nStore.t
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

const breakDurationsList = ref<number[]>([10])

function updateBreakDurations() {
  settings.value.break_durations = breakDurationsList.value.filter(d => d !== null && d !== undefined && !isNaN(d))
}

function addBreak() {
  const lastDuration = breakDurationsList.value.length > 0 
    ? breakDurationsList.value[breakDurationsList.value.length - 1] 
    : settings.value.break_duration_minutes || 10
  breakDurationsList.value.push(lastDuration)
  updateBreakDurations()
}

function removeBreak(index: number) {
  if (breakDurationsList.value.length > 1) {
    breakDurationsList.value.splice(index, 1)
    updateBreakDurations()
  }
}

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
    
    // Initialize break durations list
    if (data.break_durations && data.break_durations.length > 0) {
      breakDurationsList.value = [...data.break_durations]
    } else {
      breakDurationsList.value = [data.break_duration_minutes || 10]
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
    max-width: 1600px;
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

  &__sections-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 2rem;

    @media (max-width: 1024px) {
      grid-template-columns: 1fr;
    }
  }

  &__column {
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

  &__break-durations {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  &__break-item {
    @include neo-surface(12px, 0.6);
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 1rem;
    background: $neo-bg-light;
    transition: all 0.3s ease;

    &:hover {
      @include neo-surface(12px, 0.8);
    }
  }

  &__break-label {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    min-width: 140px;
  }

  &__break-number {
    font-weight: 600;
    color: $neo-text;
    font-size: 0.95rem;
  }

  &__break-description {
    font-size: 0.8rem;
    color: $neo-text-muted;
  }

  &__input--break {
    flex: 0 0 100px;
    text-align: center;
  }

  &__break-unit {
    color: $neo-text-light;
    font-size: 0.9rem;
    font-weight: 500;
    min-width: 35px;
  }

  &__break-remove {
    @extend %neo-button;
    @extend %neo-button--danger;
    width: 32px;
    height: 32px;
    padding: 0;
    border-radius: 50%;
    font-size: 1.5rem;
    line-height: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  &__break-add {
    @extend %neo-button;
    @extend %neo-button--secondary;
    align-self: flex-start;
    padding: 0.75rem 1.5rem;
    border-radius: 12px;
    font-weight: 600;
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
