<template>
  <div class="subject-allocations-view">
    <header class="subject-allocations-view__header">
      <h1 class="subject-allocations-view__title">Manage Subject Allocations</h1>
      <router-link to="/admin" class="subject-allocations-view__back">Back</router-link>
    </header>
    <main class="subject-allocations-view__content">
      <div class="subject-allocations-view__section">
        <h2>Add Subject Allocation</h2>
        <form @submit.prevent="createAllocation" class="subject-allocations-view__form">
          <select
            v-model="newAllocation.class_group_id"
            class="subject-allocations-view__input"
            required
          >
            <option value="">Select Class</option>
            <option
              v-for="classGroup in classes"
              :key="classGroup.id"
              :value="classGroup.id"
            >
              {{ classGroup.name }}
            </option>
          </select>
          <select
            v-model="newAllocation.subject_id"
            class="subject-allocations-view__input"
            required
          >
            <option value="">Select Subject</option>
            <option
              v-for="subject in subjects"
              :key="subject.id"
              :value="subject.id"
            >
              {{ subject.name }}
            </option>
          </select>
          <input
            v-model.number="newAllocation.weekly_hours"
            type="number"
            placeholder="Weekly Hours"
            min="1"
            class="subject-allocations-view__input"
            required
          />
          <button type="submit" class="subject-allocations-view__button" :disabled="loading">
            Add Allocation
          </button>
        </form>
      </div>

      <div class="subject-allocations-view__section">
        <h2>Subject Allocations</h2>
        <div v-if="allocations.length > 0" class="subject-allocations-view__list">
          <div
            v-for="allocation in allocations"
            :key="allocation.id"
            class="subject-allocations-view__item"
          >
            <div class="subject-allocations-view__item-info">
              <span class="subject-allocations-view__item-class">
                {{ getClassName(allocation.class_group_id) }}
              </span>
              <span class="subject-allocations-view__item-subject">
                {{ getSubjectName(allocation.subject_id) }}
              </span>
              <span class="subject-allocations-view__item-hours">
                {{ allocation.weekly_hours }} hours/week
              </span>
            </div>
            <div class="subject-allocations-view__item-actions">
              <button
                @click="editAllocation(allocation)"
                class="subject-allocations-view__edit"
                :disabled="loading"
              >
                Edit
              </button>
              <button
                @click="deleteAllocation(allocation.id)"
                class="subject-allocations-view__delete"
                :disabled="loading"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
        <div v-else class="subject-allocations-view__empty">No allocations yet</div>
      </div>

      <!-- Edit Modal -->
      <div v-if="editingAllocation" class="subject-allocations-view__modal">
        <div class="subject-allocations-view__modal-content">
          <h3>Edit Allocation</h3>
          <form @submit.prevent="updateAllocation" class="subject-allocations-view__form">
            <input
              v-model.number="editingAllocation.weekly_hours"
              type="number"
              placeholder="Weekly Hours"
              min="1"
              class="subject-allocations-view__input"
              required
            />
            <div class="subject-allocations-view__modal-actions">
              <button type="submit" class="subject-allocations-view__button" :disabled="loading">
                Save
              </button>
              <button
                type="button"
                @click="editingAllocation = null"
                class="subject-allocations-view__button subject-allocations-view__button--secondary"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      </div>

      <div v-if="error" class="subject-allocations-view__error">{{ error }}</div>
      <div v-if="success" class="subject-allocations-view__success">{{ success }}</div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '@/services/api'

interface ClassGroup {
  id: number
  name: string
}

interface Subject {
  id: number
  name: string
}

interface Allocation {
  id: number
  class_group_id: number
  subject_id: number
  weekly_hours: number
}

const allocations = ref<Allocation[]>([])
const classes = ref<ClassGroup[]>([])
const subjects = ref<Subject[]>([])
const loading = ref(false)
const error = ref('')
const success = ref('')
const editingAllocation = ref<Allocation | null>(null)

const newAllocation = ref({
  class_group_id: null as number | null,
  subject_id: null as number | null,
  weekly_hours: 1
})

function getClassName(classGroupId: number): string {
  const classGroup = classes.value.find(c => c.id === classGroupId)
  return classGroup ? classGroup.name : 'Unknown'
}

function getSubjectName(subjectId: number): string {
  const subject = subjects.value.find(s => s.id === subjectId)
  return subject ? subject.name : 'Unknown'
}

async function loadClasses() {
  try {
    const response = await api.get('/class-groups/')
    classes.value = response.data
  } catch (err: any) {
    console.error('Failed to load classes:', err)
  }
}

async function loadSubjects() {
  try {
    const { useAuthStore } = await import('@/stores/auth')
    const authStore = useAuthStore()
    const schoolId = authStore.user?.school_id
    if (!schoolId) return
    
    const response = await api.get(`/subjects/schools/${schoolId}/subjects`)
    subjects.value = response.data
  } catch (err: any) {
    console.error('Failed to load subjects:', err)
  }
}

async function loadAllocations() {
  try {
    const response = await api.get('/subjects/class-subject-allocations')
    allocations.value = response.data
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to load allocations'
  }
}

async function createAllocation() {
  loading.value = true
  error.value = ''
  success.value = ''
  
  try {
    await api.post('/subjects/class-subject-allocations', newAllocation.value)
    success.value = 'Allocation created successfully'
    newAllocation.value = { class_group_id: null, subject_id: null, weekly_hours: 1 }
    await loadAllocations()
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to create allocation'
  } finally {
    loading.value = false
  }
}

function editAllocation(allocation: Allocation) {
  editingAllocation.value = { ...allocation }
}

async function updateAllocation() {
  if (!editingAllocation.value) return
  
  loading.value = true
  error.value = ''
  success.value = ''
  
  try {
    await api.put(`/subjects/class-subject-allocations/${editingAllocation.value.id}`, {
      weekly_hours: editingAllocation.value.weekly_hours
    })
    success.value = 'Allocation updated successfully'
    editingAllocation.value = null
    await loadAllocations()
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to update allocation'
  } finally {
    loading.value = false
  }
}

async function deleteAllocation(allocationId: number) {
  if (!confirm('Are you sure you want to delete this allocation?')) {
    return
  }
  
  loading.value = true
  error.value = ''
  success.value = ''
  
  try {
    await api.delete(`/subjects/class-subject-allocations/${allocationId}`)
    success.value = 'Allocation deleted successfully'
    await loadAllocations()
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to delete allocation'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadClasses()
  loadSubjects()
  loadAllocations()
})
</script>

<style lang="scss" scoped>
@import '../styles/neo.scss';

.subject-allocations-view {
  min-height: 100vh;
  background: transparent;

  &__header {
    background: $neo-bg-base;
    padding: 1rem 2rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  }

  &__title {
    color: $neo-text;
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

  &__section {
    background: $neo-bg-base;
    padding: 2rem;
    border-radius: 8px;
    margin-bottom: 2rem;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);

    h2 {
      margin-bottom: 1rem;
      color: $neo-text;
    }
  }

  &__form {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  &__input {
    padding: 0.75rem;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 1rem;

    &:focus {
      outline: none;
      border-color: #4a90e2;
    }
  }

  &__button {
    padding: 0.75rem 2rem;
    background-color: #4a90e2;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 1rem;
    align-self: flex-start;

    &:hover:not(:disabled) {
      background-color: #357abd;
    }

    &:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }

    &--secondary {
      background-color: #6c757d;

      &:hover {
        background-color: #5a6268;
      }
    }
  }

  &__list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  &__item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem;
    background: $neo-bg-light;
    border-radius: 4px;
    border: 1px solid #dee2e6;

    &-info {
      display: flex;
      gap: 1rem;
      align-items: center;
    }

    &-class {
      font-weight: 600;
      color: $neo-text;
    }

    &-subject {
      color: $neo-text-light;
    }

    &-hours {
      color: #4a90e2;
      font-weight: 600;
    }
  }

  &__item-actions {
    display: flex;
    gap: 0.5rem;
  }

  &__edit {
    padding: 0.5rem 1rem;
    background-color: #ffc107;
    color: $neo-text;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.875rem;

    &:hover:not(:disabled) {
      background-color: #e0a800;
    }

    &:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }
  }

  &__delete {
    padding: 0.5rem 1rem;
    background-color: #dc3545;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.875rem;

    &:hover:not(:disabled) {
      background-color: #c82333;
    }

    &:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }
  }

  &__empty {
    padding: 2rem;
    text-align: center;
    color: $neo-text-light;
    font-style: italic;
  }

  &__modal {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
  }

  &__modal-content {
    background: $neo-bg-base;
    padding: 2rem;
    border-radius: 8px;
    max-width: 500px;
    width: 90%;
  }

  &__modal-actions {
    display: flex;
    gap: 1rem;
    margin-top: 1rem;
  }

  &__error {
    color: #dc3545;
    padding: 1rem;
    background-color: #f8d7da;
    border-radius: 4px;
    margin-top: 1rem;
  }

  &__success {
    color: #28a745;
    padding: 1rem;
    background-color: #d4edda;
    border-radius: 4px;
    margin-top: 1rem;
  }
}
</style>

