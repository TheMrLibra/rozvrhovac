<template>
  <div class="dashboard-view">
    <header class="dashboard-view__header">
      <h1 class="dashboard-view__title">Dashboard</h1>
      <button @click="handleLogout" class="dashboard-view__logout">Logout</button>
    </header>
    <main class="dashboard-view__content">
      <div v-if="authStore.user?.role === 'ADMIN'" class="dashboard-view__admin-links">
        <router-link to="/settings" class="dashboard-view__link">School Settings</router-link>
        <router-link to="/classes" class="dashboard-view__link">Classes</router-link>
        <router-link to="/teachers" class="dashboard-view__link">Teachers</router-link>
        <router-link to="/timetables" class="dashboard-view__link">Timetables</router-link>
      </div>
      <div v-else-if="authStore.user?.role === 'TEACHER'" class="dashboard-view__teacher-links">
        <router-link to="/teacher" class="dashboard-view__link">Teacher Dashboard</router-link>
        <router-link to="/absence" class="dashboard-view__link">Report Absence</router-link>
        <router-link to="/timetable" class="dashboard-view__link">View Timetable</router-link>
      </div>
      <div v-else-if="authStore.user?.role === 'SCHOLAR'" class="dashboard-view__scholar-links">
        <router-link to="/scholar" class="dashboard-view__link">Scholar Dashboard</router-link>
        <router-link to="/timetable" class="dashboard-view__link">View Timetable</router-link>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

function handleLogout() {
  authStore.logout()
  router.push('/login')
}
</script>

<style lang="scss" scoped>
@import '../styles/neo.scss';

.dashboard-view {
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
    font-size: 1.75rem;
    font-weight: 700;
  }

  &__logout {
    @extend %neo-button;
    @extend %neo-button--danger;
    padding: 0.75rem 1.5rem;
    border-radius: 12px;
    cursor: pointer;
    font-weight: 600;
  }

  &__content {
    padding: 2rem;
    max-width: 1200px;
    margin: 0 auto;
    position: relative;
    z-index: 1;
  }

  &__admin-links,
  &__teacher-links,
  &__scholar-links {
    display: flex;
    gap: 1.5rem;
    margin-bottom: 2rem;
    flex-wrap: wrap;
  }

  &__link {
    @extend %neo-card;
    display: inline-block;
    padding: 1.25rem 2rem;
    color: $neo-text;
    text-decoration: none;
    font-weight: 600;
    transition: all 0.3s ease;
    text-align: center;
    min-width: 180px;

    &:hover {
      @include neo-surface(16px, 1.2);
      transform: translateY(-2px);
    }
    
    &:active {
      @include neo-inset(16px, 0.6);
      transform: translateY(0);
    }
  }
}
</style>

