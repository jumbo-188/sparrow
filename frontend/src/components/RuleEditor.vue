<template>
  <n-modal v-model:show="visible" preset="dialog" title="编辑规则" :style="{ width: '700px' }">
    <n-form :model="form" label-placement="left" label-width="120px" ref="formRef">
      <n-form-item label="规则 ID" path="id">
        <n-input v-model:value="form.id" placeholder="如: morning_greeting" :disabled="!!props.rule" />
      </n-form-item>
      <n-form-item label="描述" path="description">
        <n-input v-model:value="form.description" placeholder="描述消息用途" />
      </n-form-item>

      <n-form-item label="Cron 表达式" path="original_schedule">
        <n-input v-model:value="form.original_schedule" placeholder="如: 0 8 * * * (每天8点)" />
        <div style="font-size: 12px; color: #888; margin-top: 4px;">
          格式: 分 时 日 月 周 (例: 0 8 * * * 每天8点, */15 * * * * 每15分钟)
        </div>
      </n-form-item>

      <n-form-item label="推送渠道" path="channels">
        <n-checkbox-group v-model:value="form.channels">
          <n-checkbox v-for="ch in channelOptions" :key="ch.value" :value="ch.value">
            {{ ch.label }}
          </n-checkbox>
        </n-checkbox-group>
      </n-form-item>

      <n-form-item label="模板数据 (JSON)" path="data">
        <n-input
          v-model:value="dataJson"
          type="textarea"
          placeholder='如: {"title": "早安", "group": "Daily"}'
          :rows="2"
        />
      </n-form-item>

      <n-form-item label="模板内容" path="template">
        <n-input
          v-model:value="form.template"
          type="textarea"
          placeholder="支持 Jinja2 语法，如: 早上好 {{ date }}"
          :rows="6"
        />
      </n-form-item>

      <n-form-item label="预览">
        <n-button size="small" @click="preview">预览渲染结果</n-button>
        <n-card v-if="previewText" size="small" style="margin-top: 8px; max-height: 150px; overflow: auto;">
          <pre style="white-space: pre-wrap; margin: 0; font-size: 13px;">{{ previewText }}</pre>
        </n-card>
      </n-form-item>

      <n-form-item label="启用" path="enabled">
        <n-switch v-model:value="form.enabled" />
      </n-form-item>
    </n-form>

    <template #action>
      <n-button @click="visible = false">取消</n-button>
      <n-button type="primary" @click="save" :loading="saving">保存</n-button>
    </template>
  </n-modal>
</template>

<script setup>
import { ref, reactive, watch, computed, onMounted } from 'vue'
import { useMessage } from 'naive-ui'
import { useRulesStore } from '../stores/rules'

const props = defineProps({
  show: Boolean,
  rule: Object
})
const emit = defineEmits(['update:show', 'saved'])

const message = useMessage()
const store = useRulesStore()

const visible = ref(false)
const saving = ref(false)
const previewText = ref('')
const formRef = ref(null)

const channelOptions = computed(() =>
  store.channels.map(ch => ({ label: ch.name, value: ch.name }))
)

const form = reactive({
  id: '',
  description: '',
  original_schedule: '',
  channels: [],
  data: {},
  template: '',
  enabled: true
})

const dataJson = ref('{}')

watch(() => props.show, (val) => {
  visible.value = val
  if (val && props.rule) {
    Object.assign(form, {
      id: props.rule.id,
      description: props.rule.description || '',
      original_schedule: props.rule.original_schedule || '',
      channels: [...(props.rule.channels || [])],
      data: { ...(props.rule.data || {}) },
      template: props.rule.template || '',
      enabled: props.rule.enabled !== undefined ? props.rule.enabled : true
    })
    dataJson.value = JSON.stringify(props.rule.data || {}, null, 2)
  } else if (val) {
    resetForm()
  }
})

watch(visible, (val) => {
  if (!val) emit('update:show', false)
})

watch(dataJson, (val) => {
  try {
    form.data = JSON.parse(val)
  } catch {}
})

const resetForm = () => {
  form.id = ''
  form.description = ''
  form.original_schedule = '0 8 * * *'
  form.channels = []
  form.data = {}
  form.template = '早上好 {{ date }}'
  form.enabled = true
  dataJson.value = '{}'
  previewText.value = ''
}

const preview = () => {
  const mockData = {
    date: '2026-08-16',
    time: '14:30:00',
    now: '2026-08-16 14:30:00',
    title: '测试标题',
    content: '这是一条测试内容',
    ...form.data
  }
  try {
    let text = form.template
    Object.entries(mockData).forEach(([k, v]) => {
      text = text.replace(new RegExp(`{{ ${k} }}`, 'g'), v)
    })
    previewText.value = text
  } catch {
    previewText.value = '模板渲染错误'
  }
}

const save = async () => {
  saving.value = true
  try {
    try {
      form.data = JSON.parse(dataJson.value)
    } catch {}

    const payload = {
      id: form.id,
      description: form.description,
      original_schedule: form.original_schedule,
      channels: form.channels,
      data: form.data,
      template: form.template,
      enabled: form.enabled
    }

    if (props.rule) {
      await store.updateRule(props.rule.id, payload)
    } else {
      await store.createRule(payload)
    }
    emit('saved')
  } catch (err) {
    message.error(err.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  if (store.channels.length === 0) {
    store.fetchChannels()
  }
})
</script>