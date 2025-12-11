<template>
  <div class="documentation-view">
    <header class="documentation-view__header">
      <h1 class="documentation-view__title">{{ t('documentation.title') }}</h1>
      <router-link to="/dashboard" class="documentation-view__back">{{ t('documentation.back') }}</router-link>
    </header>
    <main class="documentation-view__content">
      <!-- Admin Documentation -->
      <div v-if="authStore.user?.role === 'ADMIN'" class="documentation-view__section">
        <h2 class="documentation-view__section-title">{{ t('documentation.admin.title') }}</h2>
        
        <div class="documentation-view__subsection">
          <h3 class="documentation-view__subsection-title">{{ t('documentation.admin.schoolSettings.title') }}</h3>
          <ul class="documentation-view__list">
            <li>{{ t('documentation.admin.schoolSettings.configureTimes') }}</li>
            <li>{{ t('documentation.admin.schoolSettings.configureClassHours') }}</li>
            <li>{{ t('documentation.admin.schoolSettings.configureBreaks') }}</li>
            <li>{{ t('documentation.admin.schoolSettings.configureLunch') }}</li>
          </ul>
        </div>

        <div class="documentation-view__subsection">
          <h3 class="documentation-view__subsection-title">{{ t('documentation.admin.howTo.generateTimetable.title') }}</h3>
          <ol class="documentation-view__list documentation-view__list--ordered">
            <li>{{ t('documentation.admin.howTo.generateTimetable.step1') }}</li>
            <li>{{ t('documentation.admin.howTo.generateTimetable.step2') }}</li>
            <li>{{ t('documentation.admin.howTo.generateTimetable.step3') }}</li>
            <li>{{ t('documentation.admin.howTo.generateTimetable.step4') }}</li>
            <li>{{ t('documentation.admin.howTo.generateTimetable.step5') }}</li>
          </ol>
        </div>

        <div class="documentation-view__subsection">
          <h3 class="documentation-view__subsection-title">{{ t('documentation.admin.howTo.assignPrimaryTeacher.title') }}</h3>
          <ol class="documentation-view__list documentation-view__list--ordered">
            <li>{{ t('documentation.admin.howTo.assignPrimaryTeacher.step1') }}</li>
            <li>{{ t('documentation.admin.howTo.assignPrimaryTeacher.step2') }}</li>
            <li>{{ t('documentation.admin.howTo.assignPrimaryTeacher.step3') }}</li>
            <li>{{ t('documentation.admin.howTo.assignPrimaryTeacher.step4') }}</li>
          </ol>
        </div>

        <div class="documentation-view__subsection">
          <h3 class="documentation-view__subsection-title">{{ t('documentation.admin.howTo.generateSubstitute.title') }}</h3>
          <ol class="documentation-view__list documentation-view__list--ordered">
            <li>{{ t('documentation.admin.howTo.generateSubstitute.step1') }}</li>
            <li>{{ t('documentation.admin.howTo.generateSubstitute.step2') }}</li>
            <li>{{ t('documentation.admin.howTo.generateSubstitute.step3') }}</li>
            <li>{{ t('documentation.admin.howTo.generateSubstitute.step4') }}</li>
          </ol>
        </div>

        <div class="documentation-view__subsection">
          <h3 class="documentation-view__subsection-title">{{ t('documentation.admin.classes.title') }}</h3>
          <ul class="documentation-view__list">
            <li>{{ t('documentation.admin.classes.viewTimetables') }}</li>
            <li>{{ t('documentation.admin.classes.manageSubjects') }}</li>
            <li>{{ t('documentation.admin.classes.assignPrimaryTeachers') }}</li>
            <li>{{ t('documentation.admin.classes.setStudentCount') }}</li>
          </ul>
        </div>

        <div class="documentation-view__subsection">
          <h3 class="documentation-view__subsection-title">{{ t('documentation.admin.teachers.title') }}</h3>
          <ul class="documentation-view__list">
            <li>{{ t('documentation.admin.teachers.addEditTeachers') }}</li>
            <li>{{ t('documentation.admin.teachers.manageCapabilities') }}</li>
            <li>{{ t('documentation.admin.teachers.viewAbsences') }}</li>
            <li>{{ t('documentation.admin.teachers.viewTimetables') }}</li>
          </ul>
        </div>

        <div class="documentation-view__subsection">
          <h3 class="documentation-view__subsection-title">{{ t('documentation.admin.subjects.title') }}</h3>
          <ul class="documentation-view__list">
            <li>{{ t('documentation.admin.subjects.addEditSubjects') }}</li>
            <li>{{ t('documentation.admin.subjects.configureConstraints') }}</li>
            <li>{{ t('documentation.admin.subjects.manageAllocations') }}</li>
          </ul>
        </div>

        <div class="documentation-view__subsection">
          <h3 class="documentation-view__subsection-title">{{ t('documentation.admin.classrooms.title') }}</h3>
          <ul class="documentation-view__list">
            <li>{{ t('documentation.admin.classrooms.addEditClassrooms') }}</li>
            <li>{{ t('documentation.admin.classrooms.setCapacity') }}</li>
            <li>{{ t('documentation.admin.classrooms.assignSpecializations') }}</li>
          </ul>
        </div>

        <div class="documentation-view__subsection">
          <h3 class="documentation-view__subsection-title">{{ t('documentation.admin.timetables.title') }}</h3>
          <ul class="documentation-view__list">
            <li>{{ t('documentation.admin.timetables.generateFixed') }}</li>
            <li>{{ t('documentation.admin.timetables.generateSubstitute') }}</li>
            <li>{{ t('documentation.admin.timetables.validateTimetables') }}</li>
            <li>{{ t('documentation.admin.timetables.viewCalendar') }}</li>
            <li>{{ t('documentation.admin.timetables.deleteTimetables') }}</li>
          </ul>
        </div>

        <div class="documentation-view__subsection">
          <h3 class="documentation-view__subsection-title">{{ t('documentation.admin.dashboard.title') }}</h3>
          <ul class="documentation-view__list">
            <li>{{ t('documentation.admin.dashboard.viewRunningLessons') }}</li>
            <li>{{ t('documentation.admin.dashboard.viewAbsentTeachers') }}</li>
          </ul>
        </div>
      </div>

      <!-- Teacher Documentation -->
      <div v-if="authStore.user?.role === 'TEACHER'" class="documentation-view__section">
        <h2 class="documentation-view__section-title">{{ t('documentation.teacher.title') }}</h2>
        
        <div class="documentation-view__subsection">
          <h3 class="documentation-view__subsection-title">{{ t('documentation.teacher.timetable.title') }}</h3>
          <ul class="documentation-view__list">
            <li>{{ t('documentation.teacher.timetable.viewDailyTimetable') }}</li>
            <li>{{ t('documentation.teacher.timetable.viewWeeklySchedule') }}</li>
          </ul>
        </div>

        <div class="documentation-view__subsection">
          <h3 class="documentation-view__subsection-title">{{ t('documentation.teacher.absences.title') }}</h3>
          <ul class="documentation-view__list">
            <li>{{ t('documentation.teacher.absences.reportAbsence') }}</li>
            <li>{{ t('documentation.teacher.absences.viewAbsences') }}</li>
          </ul>
        </div>

        <div class="documentation-view__subsection">
          <h3 class="documentation-view__subsection-title">{{ t('documentation.teacher.dashboard.title') }}</h3>
          <ul class="documentation-view__list">
            <li>{{ t('documentation.teacher.dashboard.viewTodaysSchedule') }}</li>
            <li>{{ t('documentation.teacher.dashboard.quickActions') }}</li>
          </ul>
        </div>

        <div class="documentation-view__subsection">
          <h3 class="documentation-view__subsection-title">{{ t('documentation.teacher.howTo.viewTimetable.title') }}</h3>
          <ol class="documentation-view__list documentation-view__list--ordered">
            <li>{{ t('documentation.teacher.howTo.viewTimetable.step1') }}</li>
            <li>{{ t('documentation.teacher.howTo.viewTimetable.step2') }}</li>
            <li>{{ t('documentation.teacher.howTo.viewTimetable.step3') }}</li>
          </ol>
        </div>

        <div class="documentation-view__subsection">
          <h3 class="documentation-view__subsection-title">{{ t('documentation.teacher.howTo.reportAbsence.title') }}</h3>
          <ol class="documentation-view__list documentation-view__list--ordered">
            <li>{{ t('documentation.teacher.howTo.reportAbsence.step1') }}</li>
            <li>{{ t('documentation.teacher.howTo.reportAbsence.step2') }}</li>
            <li>{{ t('documentation.teacher.howTo.reportAbsence.step3') }}</li>
            <li>{{ t('documentation.teacher.howTo.reportAbsence.step4') }}</li>
          </ol>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { useAuthStore } from '@/stores/auth'
import { useI18nStore } from '@/stores/i18n'

const authStore = useAuthStore()
const i18nStore = useI18nStore()
const t = i18nStore.t
</script>

<style lang="scss" scoped>
@import '../styles/neo.scss';

.documentation-view {
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
    margin: 0;
    color: $neo-text;
    font-size: 2rem;
    font-weight: 700;
  }

  &__back {
    @extend %neo-button;
    @extend %neo-button--secondary;
    padding: 0.5rem 1rem;
    text-decoration: none;
    border-radius: 12px;
    font-weight: 500;
  }

  &__content {
    padding: 2rem;
    max-width: 1200px;
    margin: 0 auto;
    position: relative;
    z-index: 1;
  }

  &__section {
    @extend %neo-card;
    padding: 2rem;
    margin-bottom: 2rem;
  }

  &__section-title {
    margin: 0 0 1.5rem 0;
    color: $neo-text;
    font-size: 1.75rem;
    font-weight: 700;
    padding-bottom: 1rem;
    border-bottom: 2px solid rgba(0, 0, 0, 0.1);
  }

  &__subsection {
    margin-bottom: 2rem;

    &:last-child {
      margin-bottom: 0;
    }
  }

  &__subsection-title {
    margin: 0 0 1rem 0;
    color: $neo-text;
    font-size: 1.25rem;
    font-weight: 600;
  }

  &__list {
    margin: 0;
    padding-left: 1.5rem;
    color: $neo-text-light;
    line-height: 1.8;

    li {
      margin-bottom: 0.5rem;

      &:last-child {
        margin-bottom: 0;
      }
    }

    &--ordered {
      list-style-type: decimal;
      padding-left: 2rem;
    }
  }
}
</style>

