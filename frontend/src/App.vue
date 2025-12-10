<template>
  <div id="app" class="app">
    <router-view />
    <AlertPopup />
  </div>
</template>

<script setup lang="ts">
import AlertPopup from '@/components/AlertPopup.vue'
</script>

<style lang="scss">
@import './styles/neo.scss';

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  overflow-x: hidden;
  color: $neo-text;
}

.app {
  min-height: 100vh;
  position: relative;
  background: linear-gradient(135deg, #e6e9ef 0%, #f0f3f7 50%, #f3f6fb 100%);
  background-attachment: fixed;
}
</style>

