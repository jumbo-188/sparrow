<template>
  <n-layout style="min-height: 100vh;">
    <n-layout-header bordered style="padding: 0 24px; height: 64px; display: flex; align-items: center;">
      <div style="display: flex; align-items: center; gap: 12px;">
        <span style="font-size: 24px;">🕊️</span>
        <span style="font-weight: 600; font-size: 18px;">Sparrow 管理后台</span>
      </div>
    </n-layout-header>
    <n-layout-content style="padding: 24px;">
      <n-tabs type="line" default-value="rules">
        <!-- 规则列表 Tab -->
        <n-tab-pane name="rules" tab="📋 消息规则">
          <div style="margin-bottom: 16px; display: flex; justify-content: space-between;">
            <n-button type="primary" @click="openEditor()">+ 新增规则</n-button>
            <n-button @click="refresh" :loading="store.loading">🔄 刷新</n-button>
          </div>

          <n-data-table
            :columns="columns"
            :data="store.rules"
            :loading="store.loading"
            :bordered="true"
            :striped="true"
          />
        </n-tab-pane>

        <!-- 渠道配置 Tab -->
        <n-tab-pane name="channels" tab="📡 渠道配置">
          <ChannelConfig />
        </n-tab-pane>
      </n-tabs>
    </n-layout-content>
  </n-layout>

  <!-- 编辑弹窗 -->
  <RuleEditor
    v-model:show="showEditor"
    :rule="editingRule"
    @saved="onSaved"
  />
</template>

<script setup>
import { ref, onMounted, h } from 'vue'
import { NButton, NSpace, NTag, useMessage } from 'naive-ui'
import { useRulesStore } from '../stores/rules'
import RuleEditor from '../components/RuleEditor.vue'
import ChannelConfig from '../components/ChannelConfig.vue'

const message = useMessage()
const store = useRulesStore()

const showEditor = ref(false)
const editingRule = ref(null)

const columns = [
  { title: 'ID', key: 'id', width: 140 },
  { title: '描述', key: 'description', width: 150 },
  {
    title: '推送时间',
    key: 'display',
    width: 280,
    render(row) {
      if (!row.display) return '-'
      return h('div', { style: 'font-size: 13px;' }, [
        h('div', { style: 'color: #888;' }, `期望: ${row.display.original_display}`),
        h('div', { style: 'color: #18a058; font-weight: 500;' }, `实际: ${row.display.actual_display}`)
      ])
    }
  },
  {
    title: '渠道',
    key: 'channels',
    width: 150,
    render(row) {
      return h(NSpace, { size: 4 }, row.channels?.map(ch =>
        h(NTag, { type: 'info', size: 'small' }, ch)
      ) || [])
    }
  },
  {
    title: '状态',
    key: 'enabled',
    width: 80,
    render(row) {
      return h(NTag, { type: row.enabled ? 'success' : 'default' }, row.enabled ? '启用' : '禁用')
    }
  },
  {
    title: '操作',
    key: 'actions',
    width: 200,
    render(row) {
      return h(NSpace, { size: 8 }, [
        h(NButton, { size: 'small', type: 'primary', tertiary: true, onClick: () => openEditor(row) }, '编辑'),
        h(NButton, { size: 'small', type: 'success', tertiary: true, onClick: () => handleTest(row) }, '测试'),
        h(NButton, { size: 'small', type: 'error', tertiary: true, onClick: () => handleDelete(row) }, '删除')
      ])
    }
  }
]

const openEditor = (row = null) => {
  editingRule.value = row ? { ...row } : null
  showEditor.value = true
}

const onSaved = () => {
  showEditor.value = false
  store.fetchRules()
  message.success('规则已保存')
}

const handleTest = async (row) => {
  message.loading('正在发送测试推送...')
  try {
    const res = await store.testPush(row.id, { title: '🧪 手动测试' })
    const results = Object.entries(res.results)
      .map(([k, v]) => `${k}: ${v.success ? '✅' : '❌'}`)
      .join(' ')
    message.success(`测试完成 (${results})`)
  } catch {
    message.error('测试失败，请查看后端日志')
  }
}

const handleDelete = async (row) => {
  const confirm = window.confirm(`确定删除规则 "${row.id}" 吗？`)
  if (confirm) {
    await store.deleteRule(row.id)
    message.success('已删除')
  }
}

const refresh = () => store.fetchRules()

onMounted(() => {
  store.fetchRules()
  store.fetchChannels()
})
</script>