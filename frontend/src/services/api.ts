import axios from 'axios'
import { useAuthStore } from '@/stores/auth'
import { useAlertStore } from '@/stores/alert'

const api = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json'
  }
})

api.interceptors.request.use((config) => {
  const authStore = useAuthStore()
  if (authStore.accessToken) {
    config.headers.Authorization = `Bearer ${authStore.accessToken}`
  }
  // Add X-Tenant header from localStorage (set during login)
  // Don't add for login endpoint - backend determines tenant from user email
  if (!config.url?.includes('/auth/login')) {
    const tenantSlug = authStore.tenantSlug || localStorage.getItem('tenant_slug')
    if (tenantSlug) {
      config.headers['X-Tenant'] = tenantSlug
    }
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      const authStore = useAuthStore()
      authStore.logout()
      window.location.href = '/login'
    } else if (error.response?.status && error.response.status >= 400) {
      // Show alert for API errors (except 401 which redirects)
      const alertStore = useAlertStore()
      const message = error.response?.data?.detail || error.response?.data?.message || error.message || 'An error occurred'
      alertStore.error(message)
    }
    return Promise.reject(error)
  }
)

export default api

