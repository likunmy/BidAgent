import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useProjectStore = defineStore('project', () => {
  const projects = ref([])

  function setProjects(list) {
    projects.value = list
  }

  return { projects, setProjects }
})
