<template>
  <div id="app" class="app">
    <router-view />
  </div>
</template>

<script setup lang="ts">
</script>

<style lang="scss">
@import './styles/glass.scss';

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  overflow-x: hidden;
}

.app {
  min-height: 100vh;
  position: relative;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 25%, #f093fb 50%, #4facfe 75%, #00f2fe 100%);
  background-size: 400% 400%;
  animation: gradientShift 15s ease infinite;
  
  // Subtle glow blobs
  &::before,
  &::after {
    content: '';
    position: fixed;
    width: 500px;
    height: 500px;
    border-radius: 50%;
    filter: blur(80px);
    opacity: 0.3;
    pointer-events: none;
    z-index: 0;
  }
  
  &::before {
    background: radial-gradient(circle, rgba(102, 126, 234, 0.6) 0%, transparent 70%);
    top: -200px;
    left: -200px;
    animation: float 20s ease-in-out infinite;
  }
  
  &::after {
    background: radial-gradient(circle, rgba(118, 75, 162, 0.6) 0%, transparent 70%);
    bottom: -200px;
    right: -200px;
    animation: float 25s ease-in-out infinite reverse;
  }
}

@keyframes gradientShift {
  0% {
    background-position: 0% 50%;
  }
  50% {
    background-position: 100% 50%;
  }
  100% {
    background-position: 0% 50%;
  }
}

@keyframes float {
  0%, 100% {
    transform: translate(0, 0) scale(1);
  }
  50% {
    transform: translate(50px, 50px) scale(1.1);
  }
}
</style>

