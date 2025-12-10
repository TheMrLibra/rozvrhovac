import { defineStore } from 'pinia'
import { ref } from 'vue'

export type AlertType = 'success' | 'error' | 'warning' | 'info'

export interface Alert {
  id: string
  type: AlertType
  message: string
  duration?: number // Auto-dismiss duration in ms (0 = no auto-dismiss)
}

export const useAlertStore = defineStore('alert', () => {
  const alerts = ref<Alert[]>([])

  function showAlert(
    message: string,
    type: AlertType = 'info',
    duration: number = 5000
  ) {
    const id = `alert-${Date.now()}-${Math.random()}`
    const alert: Alert = {
      id,
      type,
      message,
      duration: duration > 0 ? duration : undefined
    }
    
    alerts.value.push(alert)

    // Auto-dismiss if duration is set
    if (duration > 0) {
      setTimeout(() => {
        dismissAlert(id)
      }, duration)
    }

    return id
  }

  function dismissAlert(id: string) {
    const index = alerts.value.findIndex(alert => alert.id === id)
    if (index > -1) {
      alerts.value.splice(index, 1)
    }
  }

  function clearAll() {
    alerts.value = []
  }

  // Convenience methods
  function success(message: string, duration?: number) {
    return showAlert(message, 'success', duration)
  }

  function error(message: string, duration?: number) {
    return showAlert(message, 'error', duration)
  }

  function warning(message: string, duration?: number) {
    return showAlert(message, 'warning', duration)
  }

  function info(message: string, duration?: number) {
    return showAlert(message, 'info', duration)
  }

  return {
    alerts,
    showAlert,
    dismissAlert,
    clearAll,
    success,
    error,
    warning,
    info
  }
})

