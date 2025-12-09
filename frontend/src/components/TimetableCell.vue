<template>
  <div class="timetable-cell">
    <div v-if="isLunchBreak" class="timetable-cell__lunch">
      <div class="timetable-cell__lunch-text">🍽️ Lunch Break</div>
    </div>
    <div v-else-if="entry" class="timetable-cell__content">
      <div class="timetable-cell__subject">{{ entry.subject?.name || 'Subject' }}</div>
      <div class="timetable-cell__class">{{ entry.class_group?.name || 'Class' }}</div>
      <div class="timetable-cell__teacher">{{ entry.teacher?.full_name || 'Teacher' }}</div>
      <div v-if="entry.classroom" class="timetable-cell__classroom">{{ entry.classroom?.name }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  entry: any
  day: number
  hour: number
  lunchHours?: number[]
}

const props = defineProps<Props>()

const isLunchBreak = computed(() => {
  return props.lunchHours && props.lunchHours.includes(props.hour) && !props.entry
})
</script>

<style lang="scss" scoped>
@import '../styles/neo.scss';

.timetable-cell {
  min-height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;

  &__content {
    text-align: center;
    padding: 0.5rem;
  }

  &__subject {
    font-weight: 600;
    color: $neo-text;
    margin-bottom: 0.25rem;
    
  }

  &__teacher {
    font-size: 0.875rem;
    color: $neo-text-light;
    margin-bottom: 0.25rem;
  }

  &__class {
    font-size: 0.875rem;
    color: $neo-text;
    margin-bottom: 0.25rem;
    font-weight: 500;
  }

  &__classroom {
    font-size: 0.75rem;
    color: $neo-text-muted;
  }

  &__lunch {
    @include neo-surface(12px, 0.6);
    min-height: 80px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: lighten(#ffc107, 35%);
    color: darken(#ffc107, 20%);
    font-weight: 600;
  }

  &__lunch-text {
    text-align: center;
    padding: 0.5rem;
  }
}
</style>

