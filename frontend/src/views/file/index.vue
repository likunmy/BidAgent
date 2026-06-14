<template>
  <div class="file-page">
    <!-- Header bar -->
    <div class="page-bar">
      <div class="bar-info">
        <span class="bar-stat">共 <strong>{{ store.files.length }}</strong> 个文件</span>
        <span v-if="store.files.length" class="bar-divider">|</span>
        <span v-if="store.files.length" class="bar-stat">{{ totalSize }}</span>
      </div>
      <n-button type="primary" @click="showModal = true" icon-placement="left">
        <template #icon><n-icon><AddOutline /></n-icon></template>
        上传文件
      </n-button>
    </div>

    <!-- Empty state -->
    <div v-if="!store.loading && store.files.length === 0" class="empty-state">
      <div class="empty-icon">
        <n-icon size="48" color="#C0BAB0"><DocumentOutline /></n-icon>
      </div>
      <p class="empty-title">暂无文件</p>
      <p class="empty-desc">上传 PDF、DOCX 或 TXT 文件，系统将自动转换为 Markdown 格式</p>
      <n-button type="primary" @click="showModal = true">上传第一个文件</n-button>
    </div>

    <!-- Data table -->
    <n-card v-else :bordered="false" class="files-card" :embedded="true">
      <n-data-table
        :columns="columns"
        :data="store.files"
        :loading="store.loading"
        :bordered="false"
        :row-key="(row) => row.id"
        :size="'small'"
        :single-line="false"
        :pagination="{
          pageSize: 10,
          showSizePicker: false,
          pageSizes: [10],
          simple: true,
        }"
      />
    </n-card>

    <!-- Upload modal -->
    <n-modal v-model:show="showModal" preset="card" title="上传文件" style="width: 520px" :mask-closable="false" :bordered="false">
      <template #header>
        <div class="modal-header">
          <span class="modal-seal"></span>
          <span>上传文件</span>
        </div>
      </template>

      <div class="upload-modal">
        <n-alert type="warning" :bordered="false" class="upload-alert">
          <template #header>请认真填写文件名和简介</template>
          文件名和简介将直接影响<b>标书生成质量</b>，请确保信息准确、完整。
        </n-alert>

        <!-- File picker -->
        <div class="file-drop" @click="$refs.fileInput.click()" @dragover.prevent @drop.prevent="onDrop">
          <input ref="fileInput" type="file" accept=".pdf,.docx,.txt" style="display:none" @change="onFileSelected" />
          <div v-if="selectedFile" class="file-selected">
            <span class="file-icon">
              <n-icon size="22"><DocumentOutline /></n-icon>
            </span>
            <span class="file-name">{{ selectedFile.name }}</span>
            <n-button text size="tiny" type="error" @click.stop="clearFile">移除</n-button>
          </div>
          <div v-else class="file-prompt">
            <n-icon size="28" color="#C0BAB0"><CloudUploadOutline /></n-icon>
            <span>点击选择文件，或拖拽到此处</span>
            <span class="file-hint">支持 PDF / DOCX / TXT</span>
          </div>
        </div>

        <n-input v-model:value="form.displayName" placeholder="文件展示名，如：项目招标文件" :status="!form.displayName && submitted ? 'warning' : undefined" show-count :maxlength="100">
          <template #prefix><span class="field-label">展示名</span></template>
        </n-input>

        <n-input v-model:value="form.description" type="textarea" placeholder="文件简介，说明文件内容和用途" :rows="3" :status="!form.description && submitted ? 'warning' : undefined" show-count :maxlength="500">
          <template #prefix><span class="field-label">简介</span></template>
        </n-input>

        <div class="modal-actions">
          <n-button quaternary @click="showModal = false">取消</n-button>
          <n-button type="primary" :loading="uploading" @click="handleUpload">提交上传</n-button>
        </div>
      </div>
    </n-modal>
  </div>
</template>

<script setup>
import { computed, h, reactive, ref, onMounted } from 'vue'
import { NButton, NCard, NIcon, NPopconfirm, NTag, useMessage } from 'naive-ui'
import { AddOutline, TrashOutline, DocumentOutline, CloudUploadOutline } from '@vicons/ionicons5'
import { useFileStore } from '@/stores/file'

const message = useMessage()
const store = useFileStore()

const showModal = ref(false)
const uploading = ref(false)
const submitted = ref(false)
const fileInput = ref(null)
const selectedFile = ref(null)
const form = reactive({ displayName: '', description: '' })

const totalSize = computed(() => {
  if (!store.files.length) return ''
  const bytes = store.files.reduce((s, f) => s + f.size, 0)
  return formatSize(bytes)
})

function formatSize(bytes) {
  if (bytes === 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  const k = 1024
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${(bytes / Math.pow(k, i)).toFixed(i > 0 ? 1 : 0)} ${units[i]}`
}

function formatDate(ts) {
  const d = new Date(ts)
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const hour = String(d.getHours()).padStart(2, '0')
  const min = String(d.getMinutes()).padStart(2, '0')
  return `${month}-${day} ${hour}:${min}`
}

function onFileSelected(e) {
  selectedFile.value = e.target.files[0] || null
}

function onDrop(e) {
  selectedFile.value = e.dataTransfer.files[0] || null
}

function clearFile() {
  selectedFile.value = null
  if (fileInput.value) fileInput.value.value = ''
}

const columns = [
  {
    title: '展示名',
    key: 'display_name',
    width: 180,
    ellipsis: { tooltip: true },
    render(row) {
      return h('div', { style: 'font-weight:500; color:#1A1A1A' }, row.display_name)
    },
  },
  { title: '简介', key: 'description', ellipsis: { tooltip: true } },
  {
    title: '格式',
    key: 'source_format',
    width: 80,
    render(row) {
      const map = { pdf: { color: '#C73B2B', bg: '#FDE8E5' }, docx: { color: '#3B6EA5', bg: '#E8F0F8' }, txt: { color: '#6B6B6B', bg: '#F0EDE7' } }
      const s = map[row.source_format] || { color: '#6B6B6B', bg: '#F0EDE7' }
      return h('span', {
        style: `display:inline-flex;align-items:center;gap:4px;padding:2px 8px;border-radius:4px;font-size:12px;font-weight:500;color:${s.color};background:${s.bg}`,
      }, [
        row.source_format === 'pdf' ? 'PDF' : row.source_format === 'docx' ? 'DOCX' : 'TXT',
      ])
    },
  },
  { title: '大小', key: 'size', width: 90, render(row) { return h('span', { style: 'color:#6B6B6B' }, formatSize(row.size)) } },
  { title: '上传时间', key: 'created_at', width: 130, render(row) { return h('span', { style: 'color:#6B6B6B;font-size:13px' }, formatDate(row.created_at)) } },
  {
    title: '',
    key: 'actions',
    width: 50,
    render(row) {
      return h(NPopconfirm, {
        onPositiveClick: () => store.deleteFile(row.id).then(() => message.success('已删除')),
        'show-icon': false,
        placement: 'left',
      }, {
        default: () => '确认删除此文件？',
        trigger: () => h(NButton, {
          quaternary: true,
          size: 'tiny',
          renderIcon: () => h(NIcon, null, { default: () => h(TrashOutline) }),
        }),
      })
    },
  },
]

async function handleUpload() {
  submitted.value = true
  if (!form.displayName || !form.description) {
    message.warning('请填写展示名和简介')
    return
  }
  if (!selectedFile.value) {
    message.warning('请选择要上传的文件')
    return
  }
  const ext = selectedFile.value.name.split('.').pop().toLowerCase()
  if (!['pdf', 'docx', 'txt'].includes(ext)) {
    message.warning('仅支持 PDF / DOCX / TXT 格式')
    return
  }

  uploading.value = true
  try {
    await store.uploadFile(selectedFile.value, form.displayName, form.description)
    message.success('上传成功')
    showModal.value = false
    form.displayName = ''
    form.description = ''
    selectedFile.value = null
    if (fileInput.value) fileInput.value.value = ''
    submitted.value = false
  } catch (e) {
    const detail = e?.response?.data?.detail || e?.message || '未知错误'
    message.error(`上传失败: ${detail}`)
  } finally {
    uploading.value = false
  }
}

onMounted(() => {
  store.fetchFiles()
})
</script>

<style scoped>
.file-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* Page bar */
.page-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.bar-info {
  font-size: 13px;
  color: var(--color-text-secondary);
}
.bar-info strong { color: var(--color-text); }
.bar-divider { margin: 0 8px; color: var(--color-border); }

/* Empty state */
.empty-state {
  background: #fff;
  border-radius: var(--card-radius);
  padding: 60px 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  text-align: center;
}
.empty-icon { margin-bottom: 4px; }
.empty-title { font-size: 15px; font-weight: 600; color: var(--color-text); }
.empty-desc { font-size: 13px; color: var(--color-text-secondary); margin-bottom: 8px; }

/* Card */
.files-card {
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}

/* Modal */
.modal-header {
  display: flex;
  align-items: center;
  gap: 10px;
}
.modal-seal {
  width: 8px;
  height: 8px;
  background: var(--color-vermillion);
  border-radius: 50%;
}

.upload-modal {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.upload-alert {
  margin: 0;
}
.upload-alert :deep(.n-alert-body__title) {
  font-size: 14px;
}

/* File drop zone */
.file-drop {
  border: 2px dashed var(--color-border);
  border-radius: var(--card-radius);
  padding: 20px;
  text-align: center;
  cursor: pointer;
  transition: border-color 0.2s;
}
.file-drop:hover {
  border-color: var(--color-vermillion);
}

.file-prompt {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--color-text-secondary);
}
.file-hint {
  font-size: 12px;
  color: var(--color-text-tertiary);
}

.file-selected {
  display: flex;
  align-items: center;
  gap: 8px;
}
.file-icon {
  display: flex;
}
.file-name {
  flex: 1;
  text-align: left;
  font-weight: 500;
  color: var(--color-text);
  font-size: 13px;
}

/* Field label */
.field-label {
  font-weight: 500;
  color: var(--color-text-secondary);
  font-size: 13px;
}

/* Actions */
.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding-top: 4px;
}
</style>
