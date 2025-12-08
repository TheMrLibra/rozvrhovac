<template>
  <div class="timetable-cell">
    <div v-if="entry" class="timetable-cell__content">
      <div class="timetable-cell__subject">{{ entry.subject?.name || 'Subject' }}</div>
      <div class="timetable-cell__teacher">{{ entry.teacher?.full_name || 'Teacher' }}</div>
      <div v-if="entry.classroom" class="timetable-cell__classroom">{{ entry.classroom?.name }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  entry: any
  day: number
  hour: number
}

defineProps<Props>()
</script>

<style lang="scss" scoped>
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
    color: #333;
    margin-bottom: 0.25rem;
  }

  &__teacher {
    font-size: 0.875rem;
    color: #666;
    margin-bottom: 0.25rem;
  }

  &__classroom {
    font-size: 0.75rem;
    color: #999;
  }
}
</style>

