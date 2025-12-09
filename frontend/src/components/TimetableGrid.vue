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
              :lunch-hours="props.lunchHours"
            />
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup lang="ts">
import TimetableCell from './TimetableCell.vue'

interface Props {
  timetable: any
  lunchHours?: number[]
}

const props = defineProps<Props>()

const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
const hours = [1, 2, 3, 4, 5, 6, 7, 8]

function getEntry(dayOfWeek: number, lessonIndex: number) {
  if (!props.timetable?.entries) return null
  return props.timetable.entries.find(
    (e: any) => e.day_of_week === dayOfWeek && e.lesson_index === lessonIndex
  )
}
</script>

<style lang="scss" scoped>
@import '../styles/glass.scss';

.timetable-grid {
  @extend %glass-panel;
  overflow: hidden;
  position: relative;
  z-index: 1;

  &__table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
  }

  &__header {
    background: rgba(74, 144, 226, 0.3);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  }

  &__cell {
    padding: 1rem;
    border: 1px solid rgba(255, 255, 255, 0.1);
    text-align: center;
    background: rgba(255, 255, 255, 0.05);
    transition: all 0.2s ease;

    &--header {
      font-weight: 600;
      color: rgba(255, 255, 255, 0.95);
      text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
    }

    &--hour {
      background: rgba(255, 255, 255, 0.08);
      backdrop-filter: blur(8px);
      -webkit-backdrop-filter: blur(8px);
      font-weight: 500;
      width: 80px;
      color: rgba(255, 255, 255, 0.9);
      text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
    }

    &--lesson {
      min-width: 150px;
      min-height: 80px;
      background: rgba(255, 255, 255, 0.05);

      &:hover {
        background: rgba(255, 255, 255, 0.1);
      }
    }
  }
}
</style>

