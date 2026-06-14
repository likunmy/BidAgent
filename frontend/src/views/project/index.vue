<template>
  <div class="project-page">
    <div class="page-bar">
      <span class="bar-info">管理您的标书项目</span>
      <n-button type="primary" icon-placement="left" @click="showCreateModal = true">
        <template #icon><n-icon><AddOutline /></n-icon></template>
        新建项目
      </n-button>
    </div>

    <!-- Empty state -->
    <div v-if="!store.loading && store.projects.length === 0" class="empty-state">
      <div class="empty-icon">
        <n-icon size="48" color="#C0BAB0"><FolderOutline /></n-icon>
      </div>
      <p class="empty-title">暂无项目</p>
      <p class="empty-desc">创建项目后，可上传项目专属文件，AI 将基于这些文件编写和审核标书</p>
      <n-button type="primary" @click="showCreateModal = true">新建项目</n-button>
    </div>

    <!-- Project list -->
    <div v-else class="project-list">
      <div
        v-for="proj in store.projects"
        :key="proj.id"
        class="project-card"
        @click="goDetail(proj.id)"
      >
        <div class="card-left">
          <div class="card-icon">
            <n-icon size="22" color="#C73B2B"><FolderOutline /></n-icon>
          </div>
          <div class="card-body">
            <div class="card-name">{{ proj.name }}</div>
            <div v-if="proj.description" class="card-desc">{{ proj.description }}</div>
          </div>
        </div>
        <div class="card-meta">
          <span class="card-date">{{ formatDate(proj.created_at) }}</span>
          <n-button text size="tiny" type="error" @click.stop="handleDelete(proj.id)">
            <template #icon><n-icon><TrashOutline /></n-icon></template>
          </n-button>
        </div>
      </div>
    </div>

    <!-- Create modal -->
    <n-modal v-model:show="showCreateModal" preset="card" title="新建项目" style="width: 480px" :mask-closable="false" :bordered="false">
      <template #header>
        <div class="modal-header">
          <span class="modal-seal"></span>
          <span>新建项目</span>
        </div>
      </template>

      <div class="create-form">
        <n-input v-model:value="form.name" placeholder="项目名称" :status="!form.name && submitted ? 'warning' : undefined" show-count :maxlength="100">
          <template #prefix><span class="field-label">名称</span></template>
        </n-input>

        <n-input v-model:value="form.description" type="textarea" placeholder="项目简介（选填）" :rows="3" show-count :maxlength="500">
          <template #prefix><span class="field-label">简介</span></template>
        </n-input>

        <div class="modal-actions">
          <n-button quaternary @click="showCreateModal = false">取消</n-button>
          <n-button type="primary" :loading="creating" @click="handleCreate">创建</n-button>
        </div>
      </div>
    </n-modal>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted } from 'vue'
import { NButton, NIcon, useMessage } from 'naive-ui'
import { AddOutline, FolderOutline, TrashOutline } from '@vicons/ionicons5'
import { useProjectStore } from '@/stores/project'
import { useRouter } from 'vue-router'

const message = useMessage()
const store = useProjectStore()
const router = useRouter()

const showCreateModal = ref(false)
const creating = ref(false)
const submitted = ref(false)
const form = reactive({ name: '', description: '' })

function formatDate(ts) {
  const d = new Date(ts)
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const hour = String(d.getHours()).padStart(2, '0')
  const min = String(d.getMinutes()).padStart(2, '0')
  return `${month}-${day} ${hour}:${min}`
}

function goDetail(id) {
  router.push({ name: 'project-detail', params: { id } })
}

async function handleCreate() {
  submitted.value = true
  if (!form.name) {
    message.warning('请填写项目名称')
    return
  }
  creating.value = true
  try {
    await store.createProject(form.name, form.description)
    message.success('项目创建成功')
    showCreateModal.value = false
    form.name = ''
    form.description = ''
    submitted.value = false
  } catch (e) {
    message.error('创建失败: ' + (e?.response?.data?.detail || e?.message || '未知错误'))
  } finally {
    creating.value = false
  }
}

async function handleDelete(id) {
  try {
    await store.deleteProject(id)
    message.success('已删除')
  } catch (e) {
    message.error('删除失败')
  }
}

onMounted(() => {
  store.fetchProjects()
})
</script>

<style scoped>
.project-page { display: flex; flex-direction: column; gap: 16px; }

.page-bar { display: flex; align-items: center; justify-content: space-between; }
.bar-info { font-size: 13px; color: var(--color-text-secondary); }

/* Empty state */
.empty-state {
  background: #fff; border-radius: var(--card-radius); padding: 60px 20px;
  display: flex; flex-direction: column; align-items: center; gap: 8px; text-align: center;
}
.empty-icon { margin-bottom: 4px; }
.empty-title { font-size: 15px; font-weight: 600; color: var(--color-text); }
.empty-desc { font-size: 13px; color: var(--color-text-secondary); margin-bottom: 8px; }

/* Project list */
.project-list { display: flex; flex-direction: column; gap: 8px; }

.project-card {
  background: #fff; border-radius: var(--card-radius); padding: 16px 20px;
  display: flex; align-items: center; justify-content: space-between;
  cursor: pointer; transition: box-shadow 0.15s;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.project-card:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.08); }

.card-left { display: flex; align-items: center; gap: 12px; min-width: 0; flex: 1; }
.card-icon {
  width: 36px; height: 36px; background: var(--color-vermillion-light);
  border-radius: 8px; display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.card-body { min-width: 0; }
.card-name { font-weight: 600; font-size: 14px; color: var(--color-text); }
.card-desc { font-size: 12px; color: var(--color-text-secondary); margin-top: 2px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 400px; }

.card-meta { display: flex; align-items: center; gap: 12px; flex-shrink: 0; }
.card-date { font-size: 12px; color: var(--color-text-tertiary); }

/* Modal */
.modal-header { display: flex; align-items: center; gap: 10px; }
.modal-seal { width: 8px; height: 8px; background: var(--color-vermillion); border-radius: 50%; }

.create-form { display: flex; flex-direction: column; gap: 16px; }

.field-label { font-weight: 500; color: var(--color-text-secondary); font-size: 13px; }

.modal-actions { display: flex; justify-content: flex-end; gap: 8px; padding-top: 4px; }
</style>
