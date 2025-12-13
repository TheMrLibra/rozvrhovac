<template>
  <div class="timetable-grid">
    <table class="timetable-grid__table">
      <thead class="timetable-grid__header">
        <tr>
          <th class="timetable-grid__cell timetable-grid__cell--header"></th>
          <th
            v-for="day in days"
            :key="day"
            class="timetable-grid__cell timetable-grid__cell--header"
          >
            {{ day }}
          </th>
        </tr>
      </thead>
      <tbody class="timetable-grid__body">
        <tr v-for="hour in hours" :key="hour">
          <td class="timetable-grid__cell timetable-grid__cell--hour">{{ hour }}</td>
          <td
            v-for="day in 5"
            :key="day"
            class="timetable-grid__cell timetable-grid__cell--lesson"
          >
            <TimetableCell
              :entry="getEntry(day - 1, hour)"
              :day="day - 1"
              :hour="hour"
              :lunch-hours="props.lunchHours?.[day - 1] || []"
            />
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import TimetableCell from './TimetableCell.vue'
import { useI18nStore } from '@/stores/i18n'

interface Props {
  timetable: any
  lunchHours?: { [day: number]: number[] }  // day (0-4) -> list of lunch hour lesson indices
}

const props = defineProps<Props>()

const i18nStore = useI18nStore()
const t = i18nStore.t

const days = computed(() => [
  t('components.timetableGrid.monday'),
  t('components.timetableGrid.tuesday'),
  t('components.timetableGrid.wednesday'),
  t('components.timetableGrid.thursday'),
  t('components.timetableGrid.friday')
])
const hours = [1, 2, 3, 4, 5, 6, 7, 8]

function getEntry(dayOfWeek: number, lessonIndex: number) {
  if (!props.timetable?.entries) return null
  return props.timetable.entries.find(
    (e: any) => e.day_of_week === dayOfWeek && e.lesson_index === lessonIndex
  )
}
</script>

<style lang="scss" scoped>
@import '../styles/neo.scss';

.timetable-grid {
  @extend %neo-panel;
  overflow: hidden;
  position: relative;
  z-index: 1;

  &__table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
  }

  &__header {
    background: $neo-bg-light;
    border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  }

  &__cell {
    padding: 1rem;
    border: 1px solid rgba(0, 0, 0, 0.03);
    text-align: center;
    background: $neo-bg-base;
    transition: all 0.2s ease;

    &--header {
      font-weight: 600;
      color: $neo-text;
      background: $neo-bg-light;
    }

    &--hour {
      @include neo-inset(0, 0.4);
      background: $neo-bg-light;
      font-weight: 500;
      width: 80px;
      color: $neo-text;
    }

    &--lesson {
      min-width: 150px;
      min-height: 80px;
      background: $neo-bg-base;

      &:hover {
        @include neo-surface(0, 0.3);
        background: $neo-bg-light;
      }
    }
  }
}
</style>

