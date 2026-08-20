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
          <div style="margin-bottom: 16px; display: flex; justify-content: space-between; align-items: center;">
            <div style="display: flex; gap: 8px;">
              <n-button type="primary" @click="openEditor()">+ 新增规则</n-button>
              <n-button type="info" @click="openPlanner()">📅 预览推送计划</n-button>
            </div>
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

  <!-- 推送计划预览模态框 -->
  <n-modal
    v-model:show="showPlanner"
    preset="dialog"
    title="📅 推送计划预览"
    :style="{ width: '1100px' }"
  >
    <template #header>
      <div style="display: flex; justify-content: space-between; align-items: center; width: 100%;">
        <span>📅 推送计划预览</span>
        <n-space>
          <n-date-picker
            v-model:value="plannerDate"
            type="date"
            size="small"
            @update:value="fetchPlanner"
          />
          <n-button size="small" @click="fetchPlanner">刷新</n-button>
        </n-space>
      </div>
    </template>

    <div v-if="plannerLoading" style="text-align: center; padding: 40px;">
      <n-spin size="medium" />
    </div>

    <div v-else-if="plannerData">
      <div style="margin-bottom: 12px; display: flex; gap: 20px; font-size: 14px; flex-wrap: wrap;">
        <span>📆 日期：<strong>{{ plannerData.date }}</strong></span>
        <span>📊 总计：<strong>{{ plannerData.total }}</strong> 条</span>
        <span v-for="(count, ch) in plannerData.channel_stats" :key="ch">
          📨 {{ ch }}：<strong>{{ count }}</strong> 条
        </span>
      </div>

      <n-data-table
        :columns="plannerColumns"
        :data="plannerData.events"
        :bordered="true"
        :striped="true"
        :row-height="40"
        max-height="500"
      />
    </div>

    <template #action>
      <n-button @click="showPlanner = false">关闭</n-button>
    </template>
  </n-modal>
</template>

<script setup>
import { ref, onMounted, h } from 'vue'
import {
  NButton,
  NSpace,
  NTag,
  NModal,
  NDatePicker,
  NSpin,
  useMessage
} from 'naive-ui'
import { useRulesStore } from '../stores/rules'
import { previewDailyPlan } from '../api'
import RuleEditor from '../components/RuleEditor.vue'
import ChannelConfig from '../components/ChannelConfig.vue'

const message = useMessage()
const store = useRulesStore()

const showEditor = ref(false)
const editingRule = ref(null)

// ============ 推送计划预览 ============
const showPlanner = ref(false)
const plannerLoading = ref(false)
const plannerData = ref(null)
const plannerDate = ref(new Date())

const plannerColumns = [
  { title: '时间', key: 'time', width: 80, align: 'center' },
  { title: '规则 ID', key: 'rule_id', width: 120 },
  { title: '描述', key: 'description', width: 160, ellipsis: true },
  {
    title: '渠道',
    key: 'channels',
    width: 150,
    render(row) {
      return h(NSpace, { size: 4 }, row.channels.map(ch =>
        h(NTag, { type: 'info', size: 'small' }, ch)
      ))
    }
  },
  { title: '标题', key: 'title', width: 180, ellipsis: true },
  { title: 'Cron', key: 'cron', width: 180, ellipsis: true }
]

const openPlanner = () => {
  showPlanner.value = true
  fetchPlanner()
}

// ✅ 增强版的 fetchPlanner（核心修复）
const fetchPlanner = async () => {
  plannerLoading.value = true
  try {
    // 1. 安全获取日期值：确保是 Date 对象
    let dateObj = null
    if (plannerDate.value) {
      // 处理 n-date-picker 可能返回的各种类型
      if (plannerDate.value instanceof Date) {
        dateObj = plannerDate.value
      } else if (typeof plannerDate.value === 'number' || typeof plannerDate.value === 'string') {
        // 如果是时间戳或字符串，尝试转换为 Date
        const parsed = new Date(plannerDate.value)
        if (!isNaN(parsed.getTime())) {
          dateObj = parsed
        } else {
          console.warn('[预览计划] 无效日期值:', plannerDate.value)
        }
      } else {
        console.warn('[预览计划] 未知日期类型:', plannerDate.value)
      }
    }

    // 2. 如果日期无效，使用当前日期
    if (!dateObj || isNaN(dateObj.getTime())) {
      console.warn('[预览计划] 使用当前日期作为备用')
      dateObj = new Date()
    }

    // 3. 格式化为 YYYY-MM-DD（本地时区）
    const year = dateObj.getFullYear()
    const month = String(dateObj.getMonth() + 1).padStart(2, '0')
    const day = String(dateObj.getDate()).padStart(2, '0')
    const dateStr = `${year}-${month}-${day}`

    console.log('[预览计划] 请求日期:', dateStr)

    // 4. 调用 API
    const data = await previewDailyPlan(dateStr)
    console.log('[预览计划] API 返回:', data)

    if (data.code === 0) {
      plannerData.value = data.data
    } else {
      message.error(data.msg || '获取计划失败')
    }
  } catch (err) {
    console.error('[预览计划] 错误:', err)
    message.error('获取计划失败，请查看控制台错误')
  } finally {
    plannerLoading.value = false
  }
}

// ============ 原有逻辑 ============
const columns = [
  {
    title: 'ID',
    key: 'id',
    width: 140,
    sortable: true,
    sorter: (a, b) => a.id.localeCompare(b.id),
    defaultSortOrder: 'ascend'
  },
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
  const originalTitle = row.data?.title || 'Sparrow 通知'
  const testTitle = `🧪 测试 - ${originalTitle}`
  message.loading('正在发送测试推送...')
  try {
    const res = await store.testPush(row.id, {
      title: testTitle,
      ...row.data
    })
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