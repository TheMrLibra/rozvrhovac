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
@import '../styles/neo.scss';

.teacher-dashboard-view {
  min-height: 100vh;
  background: transparent;

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
    margin: 0;
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

  &__section {
    @extend %neo-panel;
    padding: 2rem;
    margin-bottom: 2rem;

    h2 {
      margin-bottom: 1rem;
      color: $neo-text;
      font-weight: 700;
    }
  }

  &__actions {
    display: flex;
    gap: 1.5rem;
    flex-wrap: wrap;
  }

  &__action {
    @extend %neo-button;
    @extend %neo-button--primary;
    display: inline-block;
    padding: 1rem 2rem;
    text-decoration: none;
    border-radius: 12px;
    font-weight: 600;
  }
}
</style>

