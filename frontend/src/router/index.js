import { createRouter, createWebHistory } from 'vue-router'
import AppLayout from '@/components/layout/AppLayout.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      component: AppLayout,
      children: [
        {
          path: '',
          name: 'home',
          component: () => import('@/views/home/index.vue'),
        },
        {
          path: 'projects',
          name: 'projects',
          component: () => import('@/views/project/index.vue'),
        },
        {
          path: 'projects/:id',
          name: 'project-detail',
          component: () => import('@/views/project/detail.vue'),
        },
        {
          path: 'files',
          name: 'files',
          component: () => import('@/views/file/index.vue'),
        },
      ],
    },
  ],
})

export default router
