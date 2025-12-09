<template>
  <div class="dashboard-view">
    <header class="dashboard-view__header">
      <h1 class="dashboard-view__title">Dashboard</h1>
      <button @click="handleLogout" class="dashboard-view__logout">Logout</button>
    </header>
    <main class="dashboard-view__content">
      <div v-if="authStore.user?.role === 'ADMIN'" class="dashboard-view__admin-links">
        <router-link to="/admin" class="dashboard-view__link">Admin Panel</router-link>
        <router-link to="/classes" class="dashboard-view__link">Manage Classes</router-link>
        <router-link to="/teachers" class="dashboard-view__link">Manage Teachers</router-link>
        <router-link to="/subjects" class="dashboard-view__link">Manage Subjects</router-link>
        <router-link to="/classrooms" class="dashboard-view__link">Manage Classrooms</router-link>
        <router-link to="/allocations" class="dashboard-view__link">Subject Allocations</router-link>
        <router-link to="/settings" class="dashboard-view__link">School Settings</router-link>
        <router-link to="/timetables" class="dashboard-view__link">All Timetables</router-link>
        <router-link to="/substitutions" class="dashboard-view__link">Substitutions</router-link>
      </div>
      <div v-else-if="authStore.user?.role === 'TEACHER'" class="dashboard-view__teacher-links">
        <router-link to="/teacher" class="dashboard-view__link">Teacher Dashboard</router-link>
        <router-link to="/absence" class="dashboard-view__link">Report Absence</router-link>
      </div>
      <div v-else-if="authStore.user?.role === 'SCHOLAR'" class="dashboard-view__scholar-links">
        <router-link to="/scholar" class="dashboard-view__link">Scholar Dashboard</router-link>
      </div>
      <router-link to="/timetable" class="dashboard-view__link">View Timetable</router-link>
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
.dashboard-view {
  min-height: 100vh;
  background-color: #f5f5f5;

  &__header {
    background: white;
    padding: 1rem 2rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  }

  &__title {
    color: #333;
  }

  &__logout {
    padding: 0.5rem 1rem;
    background-color: #dc3545;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;

    &:hover {
      background-color: #c82333;
    }
  }

  &__content {
    padding: 2rem;
    max-width: 1200px;
    margin: 0 auto;
  }

  &__admin-links,
  &__teacher-links,
  &__scholar-links {
    display: flex;
    gap: 1rem;
    margin-bottom: 2rem;
    flex-wrap: wrap;
  }

  &__link {
    display: inline-block;
    padding: 1rem 2rem;
    background-color: #4a90e2;
    color: white;
    text-decoration: none;
    border-radius: 4px;
    transition: background-color 0.2s;

    &:hover {
      background-color: #357abd;
    }
  }
}
</style>

