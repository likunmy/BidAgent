<template>
  <div class="app-shell">
    <!-- Sidebar -->
    <aside class="sidebar">
      <div class="sidebar-brand">
        <span class="brand-seal"></span>
        <span class="brand-text">BidAgent</span>
      </div>
      <div class="sidebar-subtitle">标书智能助手</div>
      <n-menu
        :collapsed-width="64"
        :collapsed-icon-size="22"
        :options="menuOptions"
        :value="activeKey"
        @update:value="navigate"
      />
    </aside>

    <!-- Main area -->
    <div class="main">
      <header class="header">
        <h1 class="page-title">{{ pageTitle }}</h1>
      </header>
      <main class="content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed, h } from 'vue'
import { NIcon, NMenu } from 'naive-ui'
import { useRouter, useRoute } from 'vue-router'
import { HomeOutline, FolderOutline, DocumentOutline } from '@vicons/ionicons5'

const router = useRouter()
const route = useRoute()

const pageTitle = computed(() => {
  const map = {
    'home': '首页',
    'projects': '项目管理',
    'project-detail': '项目详情',
    'files': '文件管理',
  }
  return map[route.name] || 'BidAgent'
})

const activeKey = computed(() => route.name || 'home')

function renderIcon(icon) {
  return () => h(NIcon, null, { default: () => h(icon) })
}

const menuOptions = [
  { label: '首页', key: 'home', icon: renderIcon(HomeOutline) },
  { label: '项目管理', key: 'projects', icon: renderIcon(FolderOutline) },
  { label: '文件管理', key: 'files', icon: renderIcon(DocumentOutline) },
]

function navigate(key) {
  router.push({ name: key })
}
</script>

<style scoped>
.app-shell {
  display: flex;
  height: 100vh;
  background: var(--color-paper);
}

/* Sidebar */
.sidebar {
  width: var(--sidebar-width);
  min-width: var(--sidebar-width);
  background: var(--color-navy);
  display: flex;
  flex-direction: column;
  padding: 24px 12px 16px;
  overflow-y: auto;
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 8px;
  margin-bottom: 2px;
}

.brand-seal {
  width: 10px;
  height: 10px;
  background: var(--color-vermillion);
  border-radius: 50%;
  flex-shrink: 0;
}

.brand-text {
  font-family: 'Noto Serif SC', serif;
  font-weight: 700;
  font-size: 18px;
  color: #fff;
  letter-spacing: 0.02em;
}

.sidebar-subtitle {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.45);
  padding: 0 8px 24px 20px;
  letter-spacing: 0.05em;
}

/* Main */
.main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.header {
  height: var(--header-height);
  min-height: var(--header-height);
  background: #fff;
  border-bottom: 1px solid var(--color-border);
  display: flex;
  align-items: center;
  padding: 0 28px;
}

.page-title {
  font-family: 'Noto Serif SC', serif;
  font-weight: 600;
  font-size: 16px;
  color: var(--color-text);
}

.content {
  flex: 1;
  padding: 24px 28px;
  overflow-y: auto;
  max-width: var(--content-max-width);
  width: 100%;
}
</style>
