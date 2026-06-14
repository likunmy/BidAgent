import { defineStore } from 'pinia'
import { ref } from 'vue'
import request from '@/api'

export const useFileStore = defineStore('file', () => {
  const files = ref([])
  const loading = ref(false)

  async function fetchFiles() {
    loading.value = true
    try {
      const res = await request.get('/files/public')
      files.value = res.data.files
    } finally {
      loading.value = false
    }
  }

  async function uploadFile(file, displayName, description) {
    const form = new FormData()
    form.append('file', file)
    form.append('display_name', displayName)
    if (description) form.append('description', description)

    const res = await request.post('/files/public', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    files.value.unshift(res.data)
    return res.data
  }

  async function deleteFile(id) {
    await request.delete(`/files/${id}`)
    files.value = files.value.filter((f) => f.id !== id)
  }

  // --- Project files ---
  async function fetchProjectFiles(projectId) {
    loading.value = true
    try {
      const res = await request.get(`/files/project/${projectId}`)
      return res.data.files
    } finally {
      loading.value = false
    }
  }

  async function uploadProjectFile(projectId, file, displayName, description) {
    const form = new FormData()
    form.append('file', file)
    form.append('display_name', displayName)
    if (description) form.append('description', description)

    const res = await request.post(`/files/project/${projectId}`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return res.data
  }

  return { files, loading, fetchFiles, uploadFile, deleteFile, fetchProjectFiles, uploadProjectFile }
})
