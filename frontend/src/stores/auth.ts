import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/services/api'

interface User {
  id: number
  email: string
  role: string
  school_id: number
  tenant_id: string
  teacher_id?: number | null
  class_group_id?: number | null
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const accessToken = ref<string | null>(localStorage.getItem('access_token'))
  const refreshToken = ref<string | null>(localStorage.getItem('refresh_token'))
  // Restore tenant and school info from localStorage on page load
  const tenantSlug = ref<string | null>(localStorage.getItem('tenant_slug'))
  const schoolId = ref<number | null>(localStorage.getItem('school_id') ? parseInt(localStorage.getItem('school_id')!) : null)
  const schoolName = ref<string | null>(localStorage.getItem('school_name'))

  const isAuthenticated = computed(() => !!accessToken.value && !!user.value)

  async function login(email: string, password: string) {
    try {
      // Login without X-Tenant header - backend will determine tenant from user email
      const response = await api.post('/auth/login', { email, password })
      
      // Store tokens
      accessToken.value = response.data.access_token
      refreshToken.value = response.data.refresh_token
      localStorage.setItem('access_token', response.data.access_token)
      localStorage.setItem('refresh_token', response.data.refresh_token)
      
      // Store tenant and school information from login response
      tenantSlug.value = response.data.tenant_slug
      schoolId.value = response.data.school_id
      schoolName.value = response.data.school_name || null
      localStorage.setItem('tenant_slug', response.data.tenant_slug)
      localStorage.setItem('school_id', response.data.school_id.toString())
      if (response.data.school_name) {
        localStorage.setItem('school_name', response.data.school_name)
      }
      
      // Get user info
      await fetchUser()
      return true
    } catch (error) {
      console.error('Login failed:', error)
      throw error
    }
  }

  async function fetchUser() {
    try {
      const response = await api.get('/auth/me')
      user.value = response.data
    } catch (error) {
      console.error('Failed to fetch user:', error)
      logout()
    }
  }

  function logout() {
    user.value = null
    accessToken.value = null
    refreshToken.value = null
    tenantSlug.value = null
    schoolId.value = null
    schoolName.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('tenant_slug')
    localStorage.removeItem('school_id')
    localStorage.removeItem('school_name')
  }

  return {
    user,
    accessToken,
    refreshToken,
    tenantSlug,
    schoolId,
    schoolName,
    isAuthenticated,
    login,
    logout,
    fetchUser
  }
})

