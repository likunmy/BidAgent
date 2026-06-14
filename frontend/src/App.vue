<template>
  <n-config-provider :theme-overrides="themeOverrides" :locale="zhCN">
    <n-message-provider>
      <router-view />
    </n-message-provider>
  </n-config-provider>
</template>

<script setup>
import { NConfigProvider, zhCN } from 'naive-ui'

const themeOverrides = {
  common: {
    primaryColor: '#C73B2B',
    primaryColorHover: '#D94A3A',
    primaryColorPressed: '#A62E20',
    primaryColorSuppl: '#C73B2B',
    bodyColor: '#F5F2ED',
    cardColor: '#FFFFFF',
    modalColor: '#FFFFFF',
    tableColor: '#FFFFFF',
    textColor1: '#1A1A1A',
    textColor2: '#5C5C5C',
    textColor3: '#8C8C8C',
    borderColor: '#E5E0D8',
    dividerColor: '#E5E0D8',
    placeholderColor: '#B0A89E',
    inputColor: '#FFFFFF',
    actionColor: '#F5F2ED',
    popoverColor: '#FFFFFF',
    hoverColor: '#FDE8E5',
    closeColor: '#8C8C8C',
    closeColorHover: '#5C5C5C',
    clearColor: '#B0A89E',
    clearColorHover: '#8C8C8C',
    successColor: '#1A8C5E',
    warningColor: '#D68A2C',
    errorColor: '#C73B2B',
    infoColor: '#3B6EA5',
  },
  Card: {
    borderRadius: '8px',
    titleFontWeight: '600',
    titleTextColor: '#1A1A1A',
    borderColor: '#E5E0D8',
    paddingMedium: '24px',
    titleFontSize: '16px',
  },
  Button: {
    borderRadius: '6px',
    fontWeight: '500',
    fontSizeMedium: '14px',
    heightMedium: '36px',
    paddingMedium: '0 18px',
  },
  Menu: {
    itemHeight: '40px',
    borderRadius: '6px',
    fontSize: '14px',
    itemTextColor: 'rgba(255,255,255,0.7)',
    itemTextColorHover: 'rgba(255,255,255,0.9)',
    itemTextColorActive: '#FFFFFF',
    itemColorActive: 'rgba(199,59,43,0.2)',
    itemColorActiveHover: 'rgba(199,59,43,0.3)',
    itemIconColor: 'rgba(255,255,255,0.6)',
    itemIconColorHover: 'rgba(255,255,255,0.8)',
    itemIconColorActive: '#FFFFFF',
    arrowColor: 'rgba(255,255,255,0.5)',
  },
  DataTable: {
    tdPadding: '12px 16px',
    thPadding: '10px 16px',
    borderRadius: '8px',
    thColor: '#F8F6F2',
    thTextColor: '#5C5C5C',
    tdColor: '#FFFFFF',
    borderColor: '#EDE8E0',
    thFontWeight: '600',
    thFontSize: '13px',
  },
  Modal: {
    borderRadius: '12px',
  },
  Tag: {
    borderRadius: '4px',
    fontSizeMedium: '12px',
    heightMedium: '24px',
    padding: '0 8px',
  },
  Input: {
    borderRadius: '6px',
    heightMedium: '36px',
  },
  Alert: {
    borderRadius: '6px',
  },
  Popconfirm: {
    borderRadius: '8px',
  },
  Pagination: {
    itemBorderRadius: '4px',
  },
}
</script>
