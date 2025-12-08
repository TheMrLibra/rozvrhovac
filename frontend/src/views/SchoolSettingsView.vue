<template>
  <div class="school-settings-view">
    <header class="school-settings-view__header">
      <h1 class="school-settings-view__title">School Settings</h1>
      <router-link to="/admin" class="school-settings-view__back">Back</router-link>
    </header>
    <main class="school-settings-view__content">
      <div class="school-settings-view__form-container">
        <h2>Configure School Settings</h2>
        <p>Settings configuration will be implemented here</p>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
</script>

<style lang="scss" scoped>
.school-settings-view {
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

  &__back {
    padding: 0.5rem 1rem;
    background-color: #6c757d;
    color: white;
    text-decoration: none;
    border-radius: 4px;

    &:hover {
      background-color: #5a6268;
    }
  }

  &__content {
    padding: 2rem;
    max-width: 1200px;
    margin: 0 auto;
  }

  &__form-container {
    background: white;
    padding: 2rem;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  }
}
</style>

