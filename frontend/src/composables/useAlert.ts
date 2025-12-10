import { useAlertStore } from '@/stores/alert'

export function useAlert() {
  const alertStore = useAlertStore()

  return {
    showAlert: alertStore.showAlert,
    success: alertStore.success,
    error: alertStore.error,
    warning: alertStore.warning,
    info: alertStore.info,
    dismiss: alertStore.dismissAlert,
    clearAll: alertStore.clearAll
  }
}

