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

interface Props {
  timetable: any
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
.timetable-grid {
  background: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);

  &__table {
    width: 100%;
    border-collapse: collapse;
  }

  &__header {
    background-color: #4a90e2;
    color: white;
  }

  &__cell {
    padding: 1rem;
    border: 1px solid #ddd;
    text-align: center;

    &--header {
      font-weight: 600;
    }

    &--hour {
      background-color: #f8f9fa;
      font-weight: 500;
      width: 80px;
    }

    &--lesson {
      min-width: 150px;
      min-height: 80px;
    }
  }
}
</style>

