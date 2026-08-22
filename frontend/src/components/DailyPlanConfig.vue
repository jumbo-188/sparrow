<template>
  <div>
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
      <h3 style="margin: 0;">📅 每日计划汇总</h3>
      <n-button size="small" @click="fetchConfig" :loading="loading">🔄 刷新</n-button>
    </div>

    <n-card>
      <n-form :model="form" label-placement="left" label-width="120px">
        <n-form-item label="状态">
          <n-tag :type="form.enabled ? 'success' : 'default'">
            {{ form.enabled ? '已启用' : '未启用' }}
          </n-tag>
          <span style="font-size: 12px; color: #888; margin-left: 8px;">
            {{ form.enabled ? '每天 ' + form.time + ' 自动推送明日计划' : '功能未启用，请检查 config.yaml' }}
          </span>
        </n-form-item>

        <n-form-item label="发送时间">
          <n-time-picker
            v-model:value="form.timeValue"
            format="HH:mm"
            size="small"
            style="width: 140px;"
          />
          <span style="font-size: 12px; color: #888; margin-left: 8px;">
            每天固定时间发送
          </span>
        </n-form-item>

        <n-form-item label="目标渠道">
          <n-select
            v-model:value="form.channels"
            :options="channelOptions"
            multiple
            size="small"
            style="width: 300px;"
            placeholder="选择推送渠道"
          />
          <span style="font-size: 12px; color: #888; margin-left: 8px;">
            选择要接收计划汇总的渠道
          </span>
        </n-form-item>

        <n-form-item label=" ">
          <n-space>
            <n-button type="primary" @click="saveConfig" :loading="saving">
              保存配置
            </n-button>
            <n-button type="info" @click="testSend" :loading="testing">
              📨 立即测试
            </n-button>
          </n-space>
        </n-form-item>
      </n-form>
    </n-card>

    <n-alert type="info" style="margin-top: 12px;">
      <template #header>💡 说明</template>
      每日计划汇总会在每天指定时间自动推送第二天的消息清单。
      点击「立即测试」可立即发送一份预览，验证配置是否正确。
    </n-alert>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useMessage, useDialog } from 'naive-ui'
import { getDailyPlanConfig, updateDailyPlanConfig, testDailyPlan } from '../api'
import { useRulesStore } from '../stores/rules'

const message = useMessage()
const store = useRulesStore()

const loading = ref(false)
const saving = ref(false)
const testing = ref(false)

const form = ref({
  time: '20:00',
  timeValue: null,
  channels: [],
  enabled: false
})

const channelOptions = computed(() =>
  store.channels.map(ch => ({ label: ch.name, value: ch.name }))
)

const fetchConfig = async () => {
  loading.value = true
  try {
    const res = await getDailyPlanConfig()
    if (res.data.code === 0) {
      const data = res.data.data
      form.value.time = data.time || '20:00'
      form.value.timeValue = parseTime(data.time || '20:00')
      form.value.channels = data.channels || ['bark']
      form.value.enabled = data.enabled !== false
    } else {
      message.error(res.data.msg || '获取配置失败')
    }
  } catch (err) {
    console.error('获取配置失败:', err)
    message.error('获取配置失败，请检查后端服务')
  } finally {
    loading.value = false
  }
}

const parseTime = (timeStr) => {
  const parts = timeStr.split(':')
  if (parts.length === 2) {
    const date = new Date()
    date.setHours(parseInt(parts[0]), parseInt(parts[1]), 0, 0)
    return date
  }
  return null
}

// ✅ 修复：增强健壮性，处理非 Date 对象
const formatTime = (date) => {
  if (!date) return '20:00'
  const d = date instanceof Date ? date : new Date(date)
  if (isNaN(d.getTime())) return '20:00'
  const hours = String(d.getHours()).padStart(2, '0')
  const minutes = String(d.getMinutes()).padStart(2, '0')
  return `${hours}:${minutes}`
}

const saveConfig = async () => {
  saving.value = true
  try {
    const timeValue = formatTime(form.value.timeValue)
    console.log('📤 保存配置:', { time: timeValue, channels: form.value.channels })
    const payload = {
      time: timeValue,
      channels: form.value.channels
    }
    const res = await updateDailyPlanConfig(payload)
    if (res.data.code === 0) {
      message.success(res.data.msg || '配置已保存')
    } else {
      message.error(res.data.msg || '保存失败')
    }
  } catch (err) {
    console.error('❌ 保存失败:', err)
    message.error('保存失败，请检查控制台错误')
  } finally {
    saving.value = false
  }
}

const dialog = useDialog()  // ✅ 新增

const testSend = async () => {
  const channels = form.value.channels?.join(', ') || '未知渠道'

  // ✅ 二次确认弹窗
  dialog.warning({
    title: '确认测试推送',
    content: `确定要向「${channels}」发送明日计划汇总测试消息吗？\n这将立即推送一份明日计划预览。`,
    positiveText: '确认发送',
    negativeText: '取消',
    onPositiveClick: async () => {
      testing.value = true
      try {
        const res = await testDailyPlan()
        if (res.data.code === 0) {
          message.success(res.data.msg || '测试推送已发送')
        } else {
          message.error(res.data.msg || '测试失败')
        }
      } catch (err) {
        console.error('测试失败:', err)
        message.error('测试失败，请检查后端服务')
      } finally {
        testing.value = false
      }
    }
  })
}

onMounted(() => {
  fetchConfig()
  store.fetchChannels()
})
</script>