<template>
  <n-layout has-sider style="height: 100vh">
    <n-layout-sider bordered collapse-mode="width" :collapsed-width="64" :width="220" show-trigger>
      <n-menu :collapsed-width="64" :collapsed-icon-size="22" :options="menuOptions" />
    </n-layout-sider>
    <n-layout>
      <n-layout-header bordered style="height: 48px; padding: 0 16px; display: flex; align-items: center">
        <h2 style="margin: 0; font-size: 16px">BidAgent - 标书智能助手</h2>
      </n-layout-header>
      <n-layout-content style="padding: 24px">
        <router-view />
      </n-layout-content>
    </n-layout>
  </n-layout>
</template>

<script setup>
import { h } from 'vue'
import { NIcon } from 'naive-ui'
import { RouterLink } from 'vue-router'
import { HomeOutline, FolderOutline, DocumentOutline } from '@vicons/ionicons5'

function renderIcon(icon) {
  return () => h(NIcon, null, { default: () => h(icon) })
}

const menuOptions = [
  { label: () => h(RouterLink, { to: '/' }, { default: () => '首页' }), key: 'home', icon: renderIcon(HomeOutline) },
  { label: () => h(RouterLink, { to: '/projects' }, { default: () => '项目管理' }), key: 'projects', icon: renderIcon(FolderOutline) },
  { label: () => h(RouterLink, { to: '/files' }, { default: () => '文件管理' }), key: 'files', icon: renderIcon(DocumentOutline) },
]
</script>
