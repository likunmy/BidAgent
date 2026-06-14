<template>
  <div class="project-detail-page">
    <!-- Loading state -->
    <div v-if="!project" class="loading-state">
      <n-spin size="medium" />
    </div>

    <template v-else>
      <!-- Header -->
      <div class="detail-header">
        <n-button text @click="$router.push({ name: 'projects' })" class="back-btn">
          <template #icon><n-icon><ArrowBackOutline /></n-icon></template>
          返回
        </n-button>
        <div class="header-info">
          <div class="header-top">
            <h2 class="project-title">{{ project.name }}</h2>
            <span v-if="isStreaming" class="header-badge badge-active">生成中</span>
            <span v-else-if="generationComplete" class="header-badge badge-done">已完成</span>
          </div>
          <p v-if="project.description" class="project-desc">{{ project.description }}</p>
        </div>
      </div>

      <!-- Two-column body -->
      <div class="detail-body">
        <!-- Left column -->
        <div class="timeline-column">

          <!-- ========== 1. Tender Document ========== -->
          <div class="card-section tender-section" :class="{ 'has-file': !!tenderFile }">
            <div class="section-head">
              <div class="section-head-left">
                <span class="section-seal"></span>
                <span class="section-title">招标文件</span>
                <span v-if="tenderFile" class="section-tender-status">已上传</span>
              </div>
              <n-button
                size="small"
                :type="tenderFile ? 'default' : 'primary'"
                @click="showTenderModal = true"
              >
                {{ tenderFile ? '更换文件' : '上传招标文件' }}
              </n-button>
            </div>

            <!-- Tender: empty -->
            <div v-if="!tenderFile" class="tender-empty">
              <div class="tender-empty-icon">
                <n-icon size="28" color="#C0BAB0"><DocumentOutline /></n-icon>
              </div>
              <span class="tender-empty-text">尚未上传招标文件</span>
              <span class="tender-empty-hint">招标文件是标书编制的核心依据，请优先上传</span>
            </div>

            <!-- Tender: uploaded -->
            <div v-else class="tender-card">
              <div class="tender-format" :class="'fmt-' + tenderFile.source_format">
                {{ tenderFile.source_format === 'pdf' ? 'PDF' : tenderFile.source_format === 'docx' ? 'DOCX' : 'TXT' }}
              </div>
              <div class="tender-body">
                <div class="tender-name">{{ tenderFile.display_name }}</div>
                <div class="tender-meta">
                  {{ formatSize(tenderFile.size) }}
                  <span class="tender-meta-dot">·</span>
                  {{ formatDate(tenderFile.created_at) }}
                </div>
                <div v-if="tenderFile.description" class="tender-desc">{{ tenderFile.description }}</div>
              </div>
            </div>
          </div>

          <!-- ========== 2. Missing Info Checklist ========== -->
          <div class="card-section requirements-section">
            <div class="section-head">
              <div class="section-head-left">
                <span class="section-title">缺失信息清单</span>
                <span class="section-count">{{ missingItems.length }}</span>
              </div>
            </div>

            <div v-if="missingItems.length === 0" class="req-empty">
              <n-icon size="24" color="#22A67E"><CheckmarkCircle /></n-icon>
              <span>暂无缺失信息</span>
            </div>

            <div v-else class="req-list">
              <div
                v-for="item in missingItems"
                :key="item.id"
                class="req-item"
              >
                <div class="req-status-icon">
                  <n-icon size="16" color="#E68A2E"><AlertCircle /></n-icon>
                </div>
                <div class="req-body">
                  <span class="req-name">{{ item.name }}</span>
                  <span class="req-desc">{{ item.description }}</span>
                </div>
                <span class="req-badge badge-missing">缺失</span>
              </div>
            </div>
          </div>

          <!-- ========== 3. Timeline ========== -->
          <div class="card-section">
            <div class="section-head">
              <div class="section-head-left">
                <span class="section-title">标书生成进度</span>
                <span v-if="steps.length" class="section-count">{{ progressText }}</span>
              </div>
              <n-button
                v-if="canGenerate"
                type="primary"
                size="small"
                :loading="isStreaming"
                :disabled="isStreaming"
                @click="startGeneration"
              >
                {{ generationComplete ? '重新生成' : '生成标书' }}
              </n-button>
            </div>

            <!-- Timeline empty: no tender document -->
            <div v-if="!tenderFile" class="section-empty">
              <div class="empty-icon"><n-icon size="36" color="#C0BAB0"><DocumentOutline /></n-icon></div>
              <p class="empty-title">招标文件未上传</p>
              <p class="empty-desc">请先上传招标文件，AI 才能基于此文件编写标书</p>
              <n-button size="small" @click="showTenderModal = true">上传招标文件</n-button>
            </div>

            <!-- Timeline empty: ready but never generated -->
            <div v-else-if="steps.length === 0 && !isStreaming" class="section-empty">
              <div class="empty-icon"><n-icon size="36" color="#C0BAB0"><TimeOutline /></n-icon></div>
              <p class="empty-title">尚未生成标书</p>
              <p class="empty-desc">招标文件已就绪，点击上方按钮开始生成</p>
            </div>

            <!-- Timeline steps -->
            <div v-else class="timeline-list">
              <div
                v-for="(step, idx) in steps"
                :key="step.id"
                class="timeline-step"
                :class="'step-' + step.status"
              >
                <div class="step-line"></div>
                <div class="step-node">
                  <template v-if="step.status === 'completed'">
                    <div class="node-dot node-completed"><n-icon size="14"><CheckmarkOutline /></n-icon></div>
                  </template>
                  <template v-else-if="step.status === 'failed'">
                    <div class="node-dot node-failed"><n-icon size="14"><CloseOutline /></n-icon></div>
                  </template>
                  <template v-else-if="step.status === 'in_progress'">
                    <div class="node-dot node-active"></div>
                  </template>
                  <template v-else>
                    <div class="node-dot node-pending"></div>
                  </template>
                </div>
                <div class="step-card">
                  <div class="step-header">
                    <span class="step-name">{{ step.name }}</span>
                    <span class="step-status" :class="'status-' + step.status">
                      {{ step.status === 'completed' ? '已完成' : step.status === 'in_progress' ? '进行中' : step.status === 'failed' ? '失败' : '等待中' }}
                    </span>
                  </div>
                  <p class="step-desc">{{ step.description }}</p>
                  <div class="step-meta">
                    <span v-if="step.timestamp" class="step-time">{{ step.timestamp }}</span>
                    <span v-if="step.duration" class="step-duration">{{ step.duration }}</span>
                    <span v-if="step.status === 'pending' && idx === firstPendingIndex" class="step-hint">等待上一环节完成</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Right: Files -->
        <div class="files-column">
          <div class="section-head">
            <span class="section-title">项目文件</span>
            <n-button text size="tiny" @click="showUploadModal = true" icon-placement="left">
              <template #icon><n-icon><AddOutline /></n-icon></template>
              上传
            </n-button>
          </div>

          <div v-if="!filesLoading && files.length === 0" class="files-empty">
            <n-icon size="28" color="#C0BAB0"><CloudUploadOutline /></n-icon>
            <span>暂无文件</span>
          </div>

          <div v-else-if="filesLoading" class="files-empty">
            <n-spin size="small" />
          </div>

          <div v-else class="file-list">
            <div
              v-for="f in files"
              :key="f.id"
              class="file-item"
              @click="handleFileClick(f)"
            >
              <div class="file-format" :class="'fmt-' + f.source_format">
                {{ f.source_format === 'pdf' ? 'PDF' : f.source_format === 'docx' ? 'DOCX' : 'TXT' }}
              </div>
              <div class="file-body">
                <div class="file-name" :title="f.display_name">{{ f.display_name }}</div>
                <div class="file-meta">{{ formatSize(f.size) }} · {{ formatDate(f.created_at) }}</div>
              </div>
              <n-button text size="tiny" type="error" class="file-delete" @click.stop="handleDeleteFile(f)">
                <template #icon><n-icon size="14"><TrashOutline /></n-icon></template>
              </n-button>
            </div>
          </div>

          <div class="files-count">
            <span>共 {{ files.length }} 个文件</span>
          </div>
        </div>
      </div>
    </template>

    <!-- Upload modal: Project files -->
    <n-modal v-model:show="showUploadModal" preset="card" title="上传项目文件" style="width: 520px" :mask-closable="false" :bordered="false">
      <template #header>
        <div class="modal-header">
          <span class="modal-seal"></span>
          <span>上传项目文件</span>
        </div>
      </template>
      <div class="upload-modal">
        <n-alert type="warning" :bordered="false" class="upload-alert">
          <template #header>请认真填写文件名和简介</template>
          文件名和简介将直接影响<b>标书生成质量</b>，请确保信息准确、完整。
        </n-alert>
        <div class="file-drop" @click="$refs.fileInput.click()" @dragover.prevent @drop.prevent="onDrop">
          <input ref="fileInput" type="file" accept=".pdf,.docx,.txt" style="display:none" @change="onFileSelected" />
          <div v-if="selectedFile" class="file-selected">
            <span class="file-icon"><n-icon size="22"><DocumentOutline /></n-icon></span>
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
          <n-button quaternary @click="showUploadModal = false">取消</n-button>
          <n-button type="primary" :loading="uploading" @click="handleUpload">提交上传</n-button>
        </div>
      </div>
    </n-modal>

    <!-- Upload modal: Tender document -->
    <n-modal v-model:show="showTenderModal" preset="card" title="上传招标文件" style="width: 480px" :mask-closable="false" :bordered="false">
      <template #header>
        <div class="modal-header">
          <span class="modal-seal"></span>
          <span>上传招标文件</span>
        </div>
      </template>
      <div class="upload-modal">
        <n-alert type="warning" :bordered="false" class="upload-alert">
          <template #header>招标文件是标书编制的核心依据</template>
          请上传本次项目的招标文件或采购公告，AI 将基于此文件编写完整标书。
        </n-alert>
        <div class="file-drop" @click="$refs.tenderInput.click()" @dragover.prevent @drop.prevent="onTenderDrop">
          <input ref="tenderInput" type="file" accept=".pdf,.docx,.txt" style="display:none" @change="onTenderSelected" />
          <div v-if="tenderFileSelected" class="file-selected">
            <span class="file-icon"><n-icon size="22"><DocumentOutline /></n-icon></span>
            <span class="file-name">{{ tenderFileSelected.name }}</span>
            <n-button text size="tiny" type="error" @click.stop="clearTenderFile">移除</n-button>
          </div>
          <div v-else class="file-prompt">
            <n-icon size="28" color="#C0BAB0"><CloudUploadOutline /></n-icon>
            <span>点击选择招标文件，或拖拽到此处</span>
            <span class="file-hint">支持 PDF / DOCX / TXT</span>
          </div>
        </div>
        <div class="modal-actions">
          <n-button quaternary @click="showTenderModal = false">取消</n-button>
          <n-button type="primary" :loading="tenderUploading" @click="handleTenderUpload">上传</n-button>
        </div>
      </div>
    </n-modal>
  </div>
</template>

<script setup>
import { computed, reactive, ref, onMounted, onUnmounted } from 'vue'
import { NButton, NIcon, NModal, NAlert, NInput, NSpin, useMessage } from 'naive-ui'
import {
  AddOutline, ArrowBackOutline, DocumentOutline, CloudUploadOutline, TrashOutline,
  CheckmarkOutline, CloseOutline, TimeOutline, CheckmarkCircle, AlertCircle,
} from '@vicons/ionicons5'
import { useRoute } from 'vue-router'
import { useProjectStore } from '@/stores/project'
import { useFileStore } from '@/stores/file'
import request from '@/api'

const message = useMessage()
const route = useRoute()
const projectStore = useProjectStore()
const fileStore = useFileStore()

const project = ref(null)
const files = ref([])
const filesLoading = ref(false)

// ------- Tender document -------
const tenderFile = ref(null)
const showTenderModal = ref(false)
const tenderUploading = ref(false)
const tenderInput = ref(null)
const tenderFileSelected = ref(null)

function onTenderSelected(e) {
  tenderFileSelected.value = e.target.files[0] || null
}
function onTenderDrop(e) {
  tenderFileSelected.value = e.dataTransfer.files[0] || null
}
function clearTenderFile() {
  tenderFileSelected.value = null
  if (tenderInput.value) tenderInput.value.value = ''
}

async function handleTenderUpload() {
  if (!tenderFileSelected.value) {
    message.warning('请选择要上传的招标文件')
    return
  }
  const ext = tenderFileSelected.value.name.split('.').pop().toLowerCase()
  if (!['pdf', 'docx', 'txt'].includes(ext)) {
    message.warning('仅支持 PDF / DOCX / TXT 格式')
    return
  }

  tenderUploading.value = true
  try {
    const fd = new FormData()
    fd.append('file', tenderFileSelected.value)

    const res = await request.post(`/files/tender/${route.params.id}`, fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    tenderFile.value = res.data
    message.success('招标文件上传成功')
    showTenderModal.value = false
    tenderFileSelected.value = null
    fetchMissingInfos()
  } catch (e) {
    const detail = e?.response?.data?.detail || e?.message || '未知错误'
    message.error(`上传失败: ${detail}`)
  } finally {
    tenderUploading.value = false
  }
}

async function fetchTenderFile() {
  try {
    const res = await request.get(`/files/tender/${route.params.id}`)
    tenderFile.value = res.data
  } catch {
    tenderFile.value = null
  }
}

// ------- Missing info checklist -------
const missingItems = ref([])

async function fetchMissingInfos() {
  try {
    const res = await request.get(`/projects/${route.params.id}/missing-infos`)
    missingItems.value = res.data
  } catch {
    missingItems.value = []
  }
}

// ------- Timeline / SSE -------
const steps = ref([])
const isStreaming = ref(false)
const generationComplete = ref(false)
let eventSource = null

const canGenerate = computed(() => !!tenderFile.value)
const firstPendingIndex = computed(() => steps.value.findIndex(s => s.status === 'pending'))

const progressText = computed(() => {
  const total = steps.value.length
  if (!total) return ''
  const done = steps.value.filter(s => s.status === 'completed').length
  return `${done} / ${total}`
})

function connectStream(projectId) {
  if (eventSource) eventSource.close()
  isStreaming.value = true
  generationComplete.value = false

  eventSource = new EventSource(`/api/v1/projects/${projectId}/generate/stream`)

  eventSource.addEventListener('step', (e) => {
    try {
      const data = JSON.parse(e.data)
      steps.value = steps.value.map(s =>
        s.id === data.step_id ? { ...s, ...data } : s
      )
    } catch {}
  })

  eventSource.addEventListener('complete', () => {
    isStreaming.value = false
    generationComplete.value = true
    eventSource?.close()
    eventSource = null
    message.success('标书生成完毕')
  })

  eventSource.addEventListener('error', () => {
    if (!generationComplete.value) {
      isStreaming.value = false
      message.error('连接中断，请重新生成')
    }
    eventSource?.close()
    eventSource = null
  })
}

function disconnectStream() {
  if (eventSource) {
    eventSource.close()
    eventSource = null
  }
  isStreaming.value = false
}

function startGeneration() {
  steps.value = [
    { id: 'parse', name: '解析招标文件', description: '读取并解析招标文件，提取关键要求和评分标准', status: 'pending', timestamp: null, duration: null },
    { id: 'analyze', name: '分析资质文件', description: '提取公司资质、业绩和人员信息', status: 'pending', timestamp: null, duration: null },
    { id: 'tech', name: '编写技术方案', description: '根据招标要求编写技术方案章节', status: 'pending', timestamp: null, duration: null },
    { id: 'business', name: '审核商务标书', description: '审核商务条款、报价和资质文件', status: 'pending', timestamp: null, duration: null },
    { id: 'final', name: '生成最终标书', description: '整合所有内容，生成完整的标书文档', status: 'pending', timestamp: null, duration: null },
  ]
  connectStream(Number(route.params.id))
}

// ------- File management -------
const showUploadModal = ref(false)
const uploading = ref(false)
const submitted = ref(false)
const fileInput = ref(null)
const selectedFile = ref(null)
const form = reactive({ displayName: '', description: '' })

function formatSize(bytes) {
  if (bytes === 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  const k = 1024
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${(bytes / Math.pow(k, i)).toFixed(i > 0 ? 1 : 0)} ${units[i]}`
}

function formatDate(ts) {
  const d = new Date(ts)
  return `${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
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

function handleFileClick(f) {
  // Future: preview
}

async function handleDeleteFile(f) {
  try {
    await fileStore.deleteFile(f.id)
    files.value = files.value.filter(x => x.id !== f.id)
    message.success('已删除')
  } catch {
    message.error('删除失败')
  }
}

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
    const res = await fileStore.uploadProjectFile(route.params.id, selectedFile.value, form.displayName, form.description)
    message.success('上传成功')
    files.value.unshift(res)
    showUploadModal.value = false
    form.displayName = ''
    form.description = ''
    selectedFile.value = null
    if (fileInput.value) fileInput.value.value = ''
    submitted.value = false
    // Refresh missing info checklist
    fetchMissingInfos()
  } catch (e) {
    const detail = e?.response?.data?.detail || e?.message || '未知错误'
    message.error(`上传失败: ${detail}`)
  } finally {
    uploading.value = false
  }
}

onMounted(async () => {
  const id = Number(route.params.id)
  try {
    project.value = await projectStore.getProject(id)
  } catch {
    message.error('项目不存在')
    return
  }
  filesLoading.value = true
  try {
    files.value = await fileStore.fetchProjectFiles(id)
  } finally {
    filesLoading.value = false
  }
  fetchTenderFile()
  fetchRequirements()
})

onUnmounted(() => {
  disconnectStream()
})
</script>

<style scoped>
/* =============================================
   Layout
   ============================================= */
.project-detail-page { display: flex; flex-direction: column; gap: 16px; }

.loading-state {
  display: flex; align-items: center; justify-content: center;
  height: 200px; background: #fff; border-radius: var(--card-radius);
}

/* =============================================
   Header
   ============================================= */
.detail-header { display: flex; flex-direction: column; gap: 12px; }

.back-btn {
  align-self: flex-start;
  font-size: 13px;
  color: var(--color-text-secondary);
  transition: color 0.15s;
}
.back-btn:hover { color: var(--color-text); }

.header-info {
  background: #fff;
  border-radius: var(--card-radius);
  padding: 20px 24px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}

.header-top { display: flex; align-items: center; gap: 12px; }

.project-title {
  font-family: 'Noto Serif SC', serif;
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text);
}

.header-badge {
  display: inline-flex; align-items: center; padding: 2px 10px;
  border-radius: 10px; font-size: 12px; font-weight: 500; line-height: 1.4;
}
.badge-active { background: #FDE8E5; color: #C73B2B; }
.badge-done { background: #E8F8F2; color: #22A67E; }

.project-desc {
  font-size: 13px; color: var(--color-text-secondary); margin-top: 6px; line-height: 1.5;
}

/* =============================================
   Two-column body
   ============================================= */
.detail-body { display: flex; gap: 16px; align-items: flex-start; }

.timeline-column {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.files-column {
  width: 320px; flex-shrink: 0;
  background: #fff; border-radius: var(--card-radius); padding: 16px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  display: flex; flex-direction: column; gap: 12px;
  position: sticky; top: 0;
}

/* =============================================
   Shared card-section
   ============================================= */
.card-section {
  background: #fff; border-radius: var(--card-radius); padding: 18px 20px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}

.section-head { display: flex; align-items: center; justify-content: space-between; }
.section-head-left { display: flex; align-items: baseline; gap: 10px; }

.section-seal {
  width: 8px; height: 8px; background: var(--color-vermillion); border-radius: 50%; flex-shrink: 0;
}

.section-title {
  font-family: 'Noto Serif SC', serif; font-size: 15px; font-weight: 600; color: var(--color-text);
}

.section-count { font-size: 12px; color: var(--color-text-tertiary); }

.section-empty {
  padding: 32px 12px;
  display: flex; flex-direction: column; align-items: center; gap: 8px; text-align: center;
}
.section-empty .empty-icon { margin-bottom: 2px; }
.section-empty .empty-title { font-size: 14px; font-weight: 600; color: var(--color-text); }
.section-empty .empty-desc { font-size: 13px; color: var(--color-text-secondary); margin-bottom: 4px; }

/* =============================================
   Tender document section
   ============================================= */
.tender-section {
  border-left: 3px solid var(--color-vermillion);
}
.tender-section.has-file {
  border-left-color: #22A67E;
}

.section-tender-status {
  font-size: 11px; font-weight: 500; color: #22A67E;
  background: #E8F8F2; padding: 1px 8px; border-radius: 8px; line-height: 1.5;
}

/* Tender empty */
.tender-empty {
  display: flex; flex-direction: column; align-items: center; gap: 6px;
  padding: 28px 12px; text-align: center;
}
.tender-empty-text { font-size: 13px; font-weight: 500; color: var(--color-text-secondary); }
.tender-empty-hint { font-size: 12px; color: var(--color-text-tertiary); }

/* Tender card */
.tender-card {
  display: flex; gap: 14px; padding: 12px 0 4px; align-items: flex-start;
}

.tender-format {
  width: 48px; flex-shrink: 0;
  font-size: 11px; font-weight: 600; text-align: center;
  padding: 6px 0; border-radius: 4px; line-height: 1.2; letter-spacing: 0.02em;
}
.tender-section .fmt-pdf { background: #FDE8E5; color: #C73B2B; }
.tender-section .fmt-docx { background: #E8F0F8; color: #3B6EA5; }
.tender-section .fmt-txt { background: #F0EDE7; color: #6B6B6B; }

.tender-body { flex: 1; min-width: 0; }
.tender-name { font-weight: 600; font-size: 14px; color: var(--color-text); }
.tender-meta { font-size: 12px; color: var(--color-text-tertiary); margin-top: 3px; }
.tender-meta-dot { margin: 0 4px; }
.tender-desc { font-size: 12px; color: var(--color-text-secondary); margin-top: 4px; line-height: 1.4; }

/* =============================================
   Requirements checklist
   ============================================= */
.req-empty { display: flex; justify-content: center; align-items: center; gap: 8px; padding: 24px 0; color: var(--color-text-tertiary); font-size: 13px; }
.req-list { display: flex; flex-direction: column; margin-top: 8px; }

.req-item {
  display: flex; align-items: flex-start; gap: 10px;
  padding: 10px 0; border-bottom: 1px solid #F0EDE7;
}
.req-item:last-child { border-bottom: none; }

.req-status-icon { flex-shrink: 0; margin-top: 2px; }

.req-body { flex: 1; min-width: 0; }
.req-name { display: block; font-size: 13px; font-weight: 500; color: var(--color-text); }
.req-desc { display: block; font-size: 11px; color: var(--color-text-tertiary); margin-top: 2px; line-height: 1.3; }

.req-badge {
  flex-shrink: 0; font-size: 11px; font-weight: 500;
  padding: 2px 8px; border-radius: 8px; line-height: 1.5;
}
.badge-completed { background: #E8F8F2; color: #22A67E; }
.badge-missing { background: #FDF0E0; color: #E68A2E; }

/* =============================================
   Timeline
   ============================================= */
.timeline-list { position: relative; padding: 8px 0; }

.timeline-list::before {
  content: ''; position: absolute; left: 23px; top: 12px; bottom: 12px;
  width: 2px; background: #E8E5E0; z-index: 0;
}

.timeline-step { position: relative; padding-left: 56px; padding-bottom: 28px; }
.timeline-step:last-child { padding-bottom: 0; }

.step-line { display: none; }

.timeline-step.step-completed .step-node::after { background: #22A67E; }
.timeline-step.step-in_progress .step-node::after { background: #C73B2B; }

.step-node {
  position: absolute; left: 0; top: 2px; width: 48px;
  display: flex; flex-direction: column; align-items: center; z-index: 1;
}
.step-node::after {
  content: ''; display: block; width: 2px; height: 100%;
  margin-top: 4px; flex: 1; min-height: 8px; background: transparent; transition: background 0.3s;
}
.timeline-step:last-child .step-node::after { display: none; }

.node-dot {
  width: 28px; height: 28px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0; transition: all 0.3s;
}
.node-completed { background: #22A67E; color: #fff; }
.node-failed { background: #C73B2B; color: #fff; }
.node-active {
  width: 20px; height: 20px; background: #C73B2B;
  box-shadow: 0 0 0 6px rgba(199, 59, 43, 0.12);
  animation: timeline-pulse 1.6s ease-in-out infinite;
}
.node-pending {
  width: 18px; height: 18px; background: transparent; border: 2px solid #D0CAC0;
}

@keyframes timeline-pulse {
  0%, 100% { box-shadow: 0 0 0 4px rgba(199, 59, 43, 0.15); }
  50% { box-shadow: 0 0 0 10px rgba(199, 59, 43, 0.05); }
}

.step-card {
  background: #fff; border-radius: var(--card-radius);
  padding: 14px 18px; box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  border-left: 3px solid transparent; transition: border-color 0.3s;
}
.step-completed .step-card { border-left-color: #22A67E; }
.step-in_progress .step-card { border-left-color: #C73B2B; }
.step-failed .step-card { border-left-color: #C73B2B; }
.step-pending .step-card { border-left-color: #E8E5E0; }

.step-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px; }
.step-name { font-weight: 600; font-size: 14px; color: var(--color-text); }
.step-status { font-size: 11px; font-weight: 500; padding: 1px 8px; border-radius: 8px; line-height: 1.5; }
.status-completed { background: #E8F8F2; color: #22A67E; }
.status-in_progress { background: #FDE8E5; color: #C73B2B; }
.status-failed { background: #FDE8E5; color: #C73B2B; }
.status-pending { background: #F0EDE7; color: #9A9A9A; }

.step-desc { font-size: 13px; color: var(--color-text-secondary); line-height: 1.5; margin: 0; }
.step-meta { display: flex; align-items: center; gap: 12px; margin-top: 6px; font-size: 12px; color: var(--color-text-tertiary); }
.step-hint { color: #B0A89E; font-style: italic; }

/* =============================================
   File sidebar
   ============================================= */
.files-empty {
  display: flex; flex-direction: column; align-items: center;
  gap: 8px; padding: 32px 8px; color: var(--color-text-tertiary); font-size: 13px;
}

.file-list { display: flex; flex-direction: column; gap: 6px; max-height: 460px; overflow-y: auto; }

.file-item {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 10px; border-radius: 6px;
  cursor: pointer; transition: background 0.12s;
}
.file-item:hover { background: #F8F6F2; }
.file-item:hover .file-delete { opacity: 1; }

.file-format {
  width: 44px; flex-shrink: 0; font-size: 10px; font-weight: 600;
  text-align: center; padding: 4px 0; border-radius: 4px; line-height: 1.2; letter-spacing: 0.02em;
}
.fmt-pdf { background: #FDE8E5; color: #C73B2B; }
.fmt-docx { background: #E8F0F8; color: #3B6EA5; }
.fmt-txt { background: #F0EDE7; color: #6B6B6B; }

.file-body { flex: 1; min-width: 0; }
.file-name { font-size: 13px; font-weight: 500; color: var(--color-text); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.file-meta { font-size: 11px; color: var(--color-text-tertiary); margin-top: 1px; }

.file-delete { opacity: 0; transition: opacity 0.12s; flex-shrink: 0; }

.files-count { text-align: center; font-size: 12px; color: var(--color-text-tertiary); padding-top: 4px; border-top: 1px solid var(--color-border); }

/* =============================================
   Modals
   ============================================= */
.modal-header { display: flex; align-items: center; gap: 10px; }
.modal-seal { width: 8px; height: 8px; background: var(--color-vermillion); border-radius: 50%; }

.upload-modal { display: flex; flex-direction: column; gap: 16px; }
.upload-alert { margin: 0; }
.upload-alert :deep(.n-alert-body__title) { font-size: 14px; }

.file-drop {
  border: 2px dashed var(--color-border); border-radius: var(--card-radius);
  padding: 20px; text-align: center; cursor: pointer; transition: border-color 0.2s;
}
.file-drop:hover { border-color: var(--color-vermillion); }

.file-prompt { display: flex; flex-direction: column; align-items: center; gap: 6px; font-size: 13px; color: var(--color-text-secondary); }
.file-hint { font-size: 12px; color: var(--color-text-tertiary); }

.file-selected { display: flex; align-items: center; gap: 8px; }
.file-icon { display: flex; }
.file-selected .file-name { flex: 1; text-align: left; font-weight: 500; color: var(--color-text); font-size: 13px; }

.field-label { font-weight: 500; color: var(--color-text-secondary); font-size: 13px; }

.modal-actions { display: flex; justify-content: flex-end; gap: 8px; padding-top: 4px; }

/* =============================================
   Responsive
   ============================================= */
@media (max-width: 860px) {
  .detail-body { flex-direction: column; }
  .files-column { width: 100%; position: static; }
  .file-list { max-height: none; }
}

@media (max-width: 480px) {
  .timeline-step { padding-left: 44px; }
  .timeline-list::before { left: 17px; }
  .step-node { width: 36px; }
  .node-dot { width: 22px; height: 22px; }
  .node-active { width: 16px; height: 16px; }
  .node-pending { width: 14px; height: 14px; }
}
</style>
