import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/LoginView.vue'),
      meta: { requiresAuth: false }
    },
    {
      path: '/',
      redirect: '/dashboard'
    },
    {
      path: '/dashboard',
      name: 'Dashboard',
      component: () => import('@/views/DashboardView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/teacher',
      name: 'TeacherDashboard',
      component: () => import('@/views/TeacherDashboardView.vue'),
      meta: { requiresAuth: true, requiresRole: 'TEACHER' }
    },
    {
      path: '/scholar',
      name: 'ScholarDashboard',
      component: () => import('@/views/ScholarDashboardView.vue'),
      meta: { requiresAuth: true, requiresRole: 'SCHOLAR' }
    },
    {
      path: '/timetable',
      name: 'Timetable',
      component: () => import('@/views/TimetableView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/admin',
      name: 'Admin',
      component: () => import('@/views/AdminDashboard.vue'),
      meta: { requiresAuth: true, requiresRole: 'ADMIN' }
    },
    {
      path: '/settings',
      name: 'Settings',
      component: () => import('@/views/SchoolSettingsView.vue'),
      meta: { requiresAuth: true, requiresRole: 'ADMIN' }
    },
    {
      path: '/classes',
      name: 'Classes',
      component: () => import('@/views/ClassesView.vue'),
      meta: { requiresAuth: true, requiresRole: 'ADMIN' }
    },
    {
      path: '/teachers',
      name: 'Teachers',
      component: () => import('@/views/TeachersView.vue'),
      meta: { requiresAuth: true, requiresRole: 'ADMIN' }
    },
    {
      path: '/subjects',
      name: 'Subjects',
      component: () => import('@/views/SubjectsView.vue'),
      meta: { requiresAuth: true, requiresRole: 'ADMIN' }
    },
    {
      path: '/classrooms',
      name: 'Classrooms',
      component: () => import('@/views/ClassroomsView.vue'),
      meta: { requiresAuth: true, requiresRole: 'ADMIN' }
    },
    {
      path: '/allocations',
      name: 'SubjectAllocations',
      component: () => import('@/views/SubjectAllocationsView.vue'),
      meta: { requiresAuth: true, requiresRole: 'ADMIN' }
    },
    {
      path: '/substitutions',
      name: 'Substitutions',
      component: () => import('@/views/SubstitutionsView.vue'),
      meta: { requiresAuth: true, requiresRole: 'ADMIN' }
    },
    {
      path: '/absence',
      name: 'TeacherAbsence',
      component: () => import('@/views/TeacherAbsenceView.vue'),
      meta: { requiresAuth: true, requiresRole: 'TEACHER' }
    }
  ]
})

router.beforeEach(async (to, _from, next) => {
  const authStore = useAuthStore()
  
  // If we have a token but no user, try to fetch user
  if (authStore.accessToken && !authStore.user) {
    try {
      await authStore.fetchUser()
    } catch (error) {
      // If fetch fails, user will be logged out by fetchUser
    }
  }
  
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/login')
  } else if (to.meta.requiresRole && authStore.user?.role !== to.meta.requiresRole) {
    next('/dashboard')
  } else {
    next()
  }
})

export default router

