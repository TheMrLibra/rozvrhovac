<template>
  <div class="teacher-dashboard-view">
    <header class="teacher-dashboard-view__header">
      <h1 class="teacher-dashboard-view__title">Teacher Dashboard</h1>
      <button @click="handleLogout" class="teacher-dashboard-view__logout">Logout</button>
    </header>
    <main class="teacher-dashboard-view__content">
      <div class="teacher-dashboard-view__section">
        <h2>Quick Actions</h2>
        <div class="teacher-dashboard-view__actions">
          <router-link to="/timetable" class="teacher-dashboard-view__action">
            View My Timetable
          </router-link>
          <router-link to="/absence" class="teacher-dashboard-view__action">
            Report Absence
          </router-link>
        </div>
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
.teacher-dashboard-view {
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

  &__section {
    background: white;
    padding: 2rem;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);

    h2 {
      margin-bottom: 1rem;
      color: #333;
    }
  }

  &__actions {
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
  }

  &__action {
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

