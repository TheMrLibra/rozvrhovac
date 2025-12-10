<template>
  <div class="alert-popup">
    <TransitionGroup name="alert" tag="div" class="alert-popup__container">
      <div
        v-for="alert in alerts"
        :key="alert.id"
        :class="['alert-popup__item', `alert-popup__item--${alert.type}`]"
        @click="dismissAlert(alert.id)"
      >
        <div class="alert-popup__icon">
          <span v-if="alert.type === 'success'">✓</span>
          <span v-else-if="alert.type === 'error'">✕</span>
          <span v-else-if="alert.type === 'warning'">⚠</span>
          <span v-else>ℹ</span>
        </div>
        <div class="alert-popup__message">{{ alert.message }}</div>
        <button
          class="alert-popup__close"
          @click.stop="dismissAlert(alert.id)"
          aria-label="Close"
        >
          ×
        </button>
      </div>
    </TransitionGroup>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useAlertStore } from '@/stores/alert'

const alertStore = useAlertStore()
const alerts = computed(() => alertStore.alerts)

function dismissAlert(id: string) {
  alertStore.dismissAlert(id)
}
</script>

<style lang="scss" scoped>
@import '../styles/neo.scss';

.alert-popup {
  position: fixed;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 10000;
  pointer-events: none;
  width: 100%;
  max-width: 600px;
  padding: 0 20px;

  &__container {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    pointer-events: none;
  }

  &__item {
    @extend %neo-panel;
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 1rem 1.25rem;
    width: 100%;
    cursor: pointer;
    pointer-events: auto;
    transition: all 0.3s ease;
    border-radius: 12px;

    &:hover {
      @include neo-surface(12px, 1.1);
    }

    &--success {
      background: lighten($neo-bg-light, 2%);
      border-left: 3px solid #4caf50;
    }

    &--error {
      background: lighten($neo-bg-light, 2%);
      border-left: 3px solid #f44336;
    }

    &--warning {
      background: lighten($neo-bg-light, 2%);
      border-left: 3px solid #ff9800;
    }

    &--info {
      background: lighten($neo-bg-light, 2%);
      border-left: 3px solid #2196f3;
    }
  }

  &__icon {
    flex-shrink: 0;
    width: 24px;
    height: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
    font-size: 18px;
    border-radius: 50%;
    background: rgba(0, 0, 0, 0.05);

    .alert-popup__item--success & {
      color: #4caf50;
    }

    .alert-popup__item--error & {
      color: #f44336;
    }

    .alert-popup__item--warning & {
      color: #ff9800;
    }

    .alert-popup__item--info & {
      color: #2196f3;
    }
  }

  &__message {
    flex: 1;
    color: $neo-text;
    font-size: 0.95rem;
    line-height: 1.4;
  }

  &__close {
    flex-shrink: 0;
    background: none;
    border: none;
    color: $neo-text-muted;
    font-size: 24px;
    line-height: 1;
    cursor: pointer;
    padding: 0;
    width: 24px;
    height: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: color 0.2s ease;
    border-radius: 4px;

    &:hover {
      color: $neo-text;
      background: rgba(0, 0, 0, 0.05);
    }
  }
}

// Transition animations
.alert-enter-active,
.alert-leave-active {
  transition: all 0.3s ease;
}

.alert-enter-from {
  opacity: 0;
  transform: translateY(-100%);
}

.alert-leave-to {
  opacity: 0;
  transform: translateY(-100%);
}

.alert-move {
  transition: transform 0.3s ease;
}
</style>

