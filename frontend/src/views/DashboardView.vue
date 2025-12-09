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
@import '../styles/glass.scss';

.dashboard-view {
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
    font-size: 1.75rem;
    font-weight: 700;
    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  }

  &__logout {
    padding: 0.75rem 1.5rem;
    background: rgba(220, 53, 69, 0.3);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.2);
    color: rgba(255, 255, 255, 0.95);
    border-radius: 12px;
    cursor: pointer;
    font-weight: 600;
    transition: all 0.3s ease;

    &:hover {
      background: rgba(220, 53, 69, 0.4);
      border-color: rgba(255, 255, 255, 0.3);
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(220, 53, 69, 0.3);
    }
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
    @extend %glass-card;
    display: inline-block;
    padding: 1.25rem 2rem;
    color: rgba(255, 255, 255, 0.95);
    text-decoration: none;
    font-weight: 600;
    transition: all 0.3s ease;
    text-align: center;
    min-width: 180px;

    &:hover {
      background: rgba(255, 255, 255, 0.25);
      border-color: rgba(255, 255, 255, 0.3);
      transform: translateY(-4px);
      box-shadow: 0 12px 24px rgba(0, 0, 0, 0.2);
    }
  }
}
</style>

