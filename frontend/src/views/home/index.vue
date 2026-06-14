<template>
  <div class="dashboard">
    <div class="stats-row">
      <div class="stat-card">
        <div class="stat-value">{{ projectCount }}</div>
        <div class="stat-label">项目总数</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ fileCount }}</div>
        <div class="stat-label">文件总数</div>
      </div>
      <div class="stat-card">
        <div class="stat-value pdf-count">{{ pdfCount }}</div>
        <div class="stat-label">PDF 文档</div>
      </div>
      <div class="stat-card">
        <div class="stat-value docx-count">{{ docxCount }}</div>
        <div class="stat-label">DOCX 文档</div>
      </div>
    </div>

    <div class="welcome-card">
      <div class="welcome-icon">
        <n-icon size="40" color="#C73B2B"><DocumentOutline /></n-icon>
      </div>
      <div class="welcome-text">
        <h2>欢迎使用 BidAgent</h2>
        <p>标书智能助手 — 上传文档、管理项目，AI 自动编写与审核标书。</p>
        <div class="welcome-actions">
          <n-button type="primary" @click="$router.push({ name: 'files' })">上传文件</n-button>
          <n-button @click="$router.push({ name: 'projects' })">管理项目</n-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { NIcon } from 'naive-ui'
import { DocumentOutline } from '@vicons/ionicons5'
import request from '@/api'

const projectCount = ref(0)
const fileCount = ref(0)
const pdfCount = ref(0)
const docxCount = ref(0)

onMounted(async () => {
  try {
    const [projRes, fileRes] = await Promise.all([
      request.get('/projects').catch(() => ({ data: [] })),
      request.get('/files').catch(() => ({ data: { files: [] } })),
    ])
    projectCount.value = projRes.data?.length || 0
    const files = fileRes.data.files || []
    fileCount.value = files.length
    pdfCount.value = files.filter(f => f.source_format === 'pdf').length
    docxCount.value = files.filter(f => f.source_format === 'docx').length
  } catch {}
})
</script>

<style scoped>
.dashboard {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.stat-card {
  background: #fff;
  border-radius: var(--card-radius);
  border-top: 3px solid var(--color-vermillion);
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}

.stat-value {
  font-family: 'Noto Serif SC', serif;
  font-size: 28px;
  font-weight: 700;
  color: var(--color-navy);
  line-height: 1.2;
}

.pdf-count { color: var(--color-vermillion); }
.docx-count { color: #3B6EA5; }

.stat-label {
  font-size: 13px;
  color: var(--color-text-secondary);
  margin-top: 4px;
}

.welcome-card {
  background: #fff;
  border-radius: var(--card-radius);
  padding: 32px;
  display: flex;
  align-items: flex-start;
  gap: 20px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}

.welcome-icon {
  width: 64px;
  height: 64px;
  background: var(--color-vermillion-light);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.welcome-text h2 {
  font-family: 'Noto Serif SC', serif;
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: 6px;
}

.welcome-text p {
  color: var(--color-text-secondary);
  line-height: 1.6;
  margin-bottom: 16px;
}

.welcome-actions {
  display: flex;
  gap: 10px;
}

@media (max-width: 640px) {
  .stats-row {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
