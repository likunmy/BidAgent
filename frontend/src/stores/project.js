import { defineStore } from 'pinia'
import { ref } from 'vue'
import request from '@/api'

export const useProjectStore = defineStore('project', () => {
  const projects = ref([])
  const loading = ref(false)

  async function fetchProjects() {
    loading.value = true
    try {
      const res = await request.get('/projects')
      projects.value = res.data
    } finally {
      loading.value = false
    }
  }

  async function createProject(name, description) {
    const res = await request.post('/projects', { name, description })
    projects.value.unshift(res.data)
    return res.data
  }

  async function deleteProject(id) {
    await request.delete(`/projects/${id}`)
    projects.value = projects.value.filter((p) => p.id !== id)
  }

  async function getProject(id) {
    const res = await request.get(`/projects/${id}`)
    return res.data
  }

  return { projects, loading, fetchProjects, createProject, deleteProject, getProject }
})
