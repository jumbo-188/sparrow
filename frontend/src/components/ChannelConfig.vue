<template>
  <div>
    <div style="margin-bottom: 16px;">
      <n-button type="primary" @click="openEditor()">+ 新增渠道</n-button>
      <n-button style="margin-left: 8px;" @click="refresh" :loading="store.loading">🔄 刷新</n-button>
    </div>

    <n-data-table
      :columns="columns"
      :data="store.channels"
      :loading="store.loading"
      :bordered="true"
      :striped="true"
    />

    <!-- 编辑/新增弹窗 -->
    <n-modal v-model:show="showModal" preset="dialog" :title="modalTitle" :style="{ width: '750px' }">
      <n-form :model="form" label-placement="left" label-width="120px">
        <!-- 基础字段 -->
        <n-form-item label="名称" path="name">
          <n-input v-model:value="form.name" placeholder="如: bark_all_devices" :disabled="!!editingChannel" />
          <div v-if="editingChannel" style="font-size:12px;color:#888;">渠道名称不可修改，如需改名请先删除再新建</div>
        </n-form-item>

        <n-form-item label="类型" path="type">
          <n-select
            v-model:value="form.type"
            :options="typeOptions"
            :disabled="!!editingChannel"
          />
        </n-form-item>

        <!-- URL（非 bark_group 类型显示） -->
        <n-form-item v-if="form.type !== 'bark_group'" label="URL" path="url">
          <n-input v-model:value="form.url" placeholder="如: https://api.day.app/${BARK_KEY}" />
          <div style="font-size:12px;color:#888;margin-top:4px;">
            支持 ${ENV_VAR} 环境变量占位符，如 ${BARK_KEY_IPHONE}
          </div>
        </n-form-item>

        <n-form-item label="Method" path="method">
          <n-select v-model:value="form.method" :options="methodOptions" />
        </n-form-item>

        <!-- PushPlus 专属 -->
        <template v-if="form.type === 'pushplus'">
          <n-divider>PushPlus 专属配置</n-divider>
          <n-form-item label="默认渠道">
            <n-input v-model:value="form.default_channel" placeholder="wechat / mail / sms" />
            <div style="font-size:12px;color:#888;margin-top:4px;">可选: wechat, mail, sms, webhook, app</div>
          </n-form-item>
          <n-form-item label="默认模板">
            <n-select v-model:value="form.default_template" :options="templateOptions" />
          </n-form-item>
          <n-form-item label="默认Topic">
            <n-input v-model:value="form.default_topic" placeholder="群组编码（一对多推送）" />
          </n-form-item>
        </template>

        <!-- Bark 普通渠道专属 -->
        <template v-if="form.type === 'bark'">
          <n-divider>Bark 专属配置</n-divider>
          <n-form-item label="默认分组">
            <n-input v-model:value="form.default_group" placeholder="Sparrow" />
          </n-form-item>
          <n-form-item label="默认图标">
            <n-input v-model:value="form.default_icon" placeholder="https://xxx.com/icon.png" />
          </n-form-item>
        </template>

        <!-- Bark 组专属配置 -->
        <template v-if="form.type === 'bark_group'">
          <n-divider>Bark 组子终端配置</n-divider>
          <n-alert type="info" style="margin-bottom: 12px;">
            组内所有子终端将同时收到同一条消息。每个子终端的 URL 支持 ${ENV_VAR} 环境变量占位符。
          </n-alert>

          <div v-for="(child, index) in form.children" :key="index" style="margin-bottom: 12px; padding: 12px; background: #f5f7fa; border-radius: 6px; border: 1px solid #e8e8e8;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
              <span style="font-weight: 500;">子终端 {{ index + 1 }}</span>
              <n-button size="small" type="error" tertiary @click="removeChild(index)">移除</n-button>
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
              <n-input v-model:value="child.name" placeholder="名称（如 iPhone）" size="small" />
              <n-input v-model:value="child.url" placeholder="URL（如 https://api.day.app/${BARK_KEY_IPHONE}）" size="small" />
              <n-input v-model:value="child.default_group" placeholder="默认分组（可选）" size="small" />
              <n-input v-model:value="child.default_icon" placeholder="默认图标（可选）" size="small" />
            </div>
          </div>

          <n-button size="small" type="primary" tertiary @click="addChild">+ 添加子终端</n-button>
        </template>
      </n-form>

      <template #action>
        <n-button @click="showModal = false">取消</n-button>
        <n-button type="primary" @click="save" :loading="saving">保存</n-button>
      </template>
    </n-modal>

    <!-- 删除确认弹窗 -->
    <n-modal v-model:show="showDeleteConfirm" preset="dialog" title="确认删除">
      <div>
        <p>确定要删除渠道 <strong>{{ deleteTarget?.name }}</strong> 吗？</p>
        <n-alert type="warning" style="margin-top: 12px;">
          <template #header>⚠️ 注意</template>
          删除渠道后，<strong>不会自动清理</strong>消息规则中对该渠道的引用。
          请手动编辑相关规则，移除该渠道，否则推送会失败。
        </n-alert>
      </div>
      <template #action>
        <n-button @click="showDeleteConfirm = false">取消</n-button>
        <n-button type="error" @click="confirmDelete" :loading="deleting">确认删除</n-button>
      </template>
    </n-modal>
  </div>
</template>

<script setup>
import { ref, reactive, computed, h, onMounted } from 'vue'
import {
  NButton, NTag, NSpace, useMessage, NModal, NForm, NFormItem,
  NInput, NSelect, NAlert, NDivider, NDataTable
} from 'naive-ui'
import { useRulesStore } from '../stores/rules'
import api from '../api'

const store = useRulesStore()
const message = useMessage()

const showModal = ref(false)
const showDeleteConfirm = ref(false)
const editingChannel = ref(null)
const deleteTarget = ref(null)
const saving = ref(false)
const deleting = ref(false)

const typeOptions = [
  { label: 'PushPlus', value: 'pushplus' },
  { label: 'Bark', value: 'bark' },
  { label: 'Bark 组', value: 'bark_group' },
  { label: 'Webhook', value: 'webhook' }
]
const methodOptions = [
  { label: 'POST', value: 'POST' },
  { label: 'GET', value: 'GET' }
]
const templateOptions = [
  { label: 'Markdown', value: 'markdown' },
  { label: 'HTML', value: 'html' },
  { label: '纯文本', value: 'txt' }
]

const modalTitle = computed(() =>
  editingChannel.value ? `编辑渠道: ${editingChannel.value.name}` : '新增渠道'
)

const form = reactive({
  name: '',
  type: 'bark',
  url: '',
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  default_channel: 'wechat',
  default_template: 'markdown',
  default_topic: '',
  default_group: 'Sparrow',
  default_icon: '',
  children: []
})

const columns = [
  {
    title: '名称',
    key: 'name',
    width: 130,
    sortable: true,
    sorter: (a, b) => a.name.localeCompare(b.name),
    defaultSortOrder: 'ascend'
  },
  {
    title: '类型',
    key: 'type',
    width: 120,
    render(row) {
      if (!row.type || row.type === '') return '子终端'
      const typeMap = { 'bark': 'Bark', 'bark_group': 'Bark组', 'pushplus': 'PushPlus', 'webhook': 'Webhook' }
      return typeMap[row.type] || row.type
    }
  },
  {
    title: 'URL/子终端',
    key: 'url',
    ellipsis: true,
    render(row) {
      if (row.type === 'bark_group' && row.children) {
        const names = row.children.map(c => c.name).join(', ')
        return h('span', { style: 'font-size: 13px; color: #18a058;' }, `📱 ${row.children.length} 个终端: ${names}`)
      }
      return row.url || '-'
    }
  },
  {
    title: '默认参数',
    key: 'defaults',
    render(row) {
      const items = []
      if (row.type === 'pushplus') {
        if (row.default_channel) items.push(`channel: ${row.default_channel}`)
        if (row.default_template) items.push(`template: ${row.default_template}`)
        if (row.default_topic) items.push(`topic: ${row.default_topic}`)
      }
      if (row.type === 'bark') {
        if (row.default_group) items.push(`group: ${row.default_group}`)
        if (row.default_icon) items.push(`icon: ${row.default_icon}`)
      }
      if (row.type === 'bark_group') {
        items.push(`子终端: ${row.children?.length || 0} 个`)
      }
      return h('span', { style: 'font-size: 12px;' }, items.join(' | ') || '-')
    }
  },
  {
    title: '操作',
    key: 'actions',
    width: 160,
    render(row) {
      // 子终端：没有 type，隐藏按钮
      if (!row.type || row.type === '') {
        return h('span', { style: 'color: #ccc; font-size: 12px;' }, '—')
      }

      // Bark 组：显示编辑 + 删除按钮
      if (row.type === 'bark_group') {
        return h(NSpace, { size: 8 }, [
          h(NButton, { size: 'small', type: 'primary', tertiary: true, onClick: () => openEditor(row) }, '编辑'),
          h(NButton, { size: 'small', type: 'error', tertiary: true, onClick: () => openDelete(row) }, '删除')
        ])
      }

      // 其他渠道：显示编辑 + 删除
      return h(NSpace, { size: 8 }, [
        h(NButton, { size: 'small', type: 'primary', tertiary: true, onClick: () => openEditor(row) }, '编辑'),
        h(NButton, { size: 'small', type: 'error', tertiary: true, onClick: () => openDelete(row) }, '删除')
      ])
    }
  }
]

// ============ 以下函数保持不变 ============
const addChild = () => {
  form.children.push({
    name: '',
    url: '',
    default_group: 'Sparrow',
    default_icon: ''
  })
}

const removeChild = (index) => {
  form.children.splice(index, 1)
}

const openEditor = (row = null) => {
  editingChannel.value = row
  if (row) {
    const data = JSON.parse(JSON.stringify(row))
    if (!data.children) data.children = []
    Object.assign(form, data)
  } else {
    resetForm()
  }
  showModal.value = true
}

const openDelete = (row) => {
  deleteTarget.value = row
  showDeleteConfirm.value = true
}

const resetForm = () => {
  form.name = ''
  form.type = 'bark'
  form.url = ''
  form.method = 'POST'
  form.headers = { 'Content-Type': 'application/json' }
  form.default_channel = 'wechat'
  form.default_template = 'markdown'
  form.default_topic = ''
  form.default_group = 'Sparrow'
  form.default_icon = ''
  form.children = []
}

const save = async () => {
  saving.value = true
  try {
    const payload = { ...form }
    Object.keys(payload).forEach(k => {
      if (payload[k] === '') delete payload[k]
      if (k === 'children' && payload[k] && payload[k].length === 0) {
        delete payload[k]
      }
    })

    if (editingChannel.value) {
      await store.updateChannel(editingChannel.value.name, payload)
      message.success('渠道更新成功')
    } else {
      await store.createChannel(payload)
      message.success('渠道创建成功')
    }
    showModal.value = false
    await store.fetchChannels()
  } catch (err) {
    message.error(err.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

const confirmDelete = async () => {
  if (!deleteTarget.value) {
    message.error('没有选择要删除的渠道')
    return
  }

  deleting.value = true
  try {
    const res = await store.deleteChannel(deleteTarget.value.name)
    message.success('已删除')
    if (res.warning) {
      message.warning(res.warning, { duration: 8000 })
    }
    showDeleteConfirm.value = false
    deleteTarget.value = null
    await store.fetchChannels()
  } catch (err) {
    message.error(err.response?.data?.detail || '删除失败')
  } finally {
    deleting.value = false
  }
}

const refresh = () => {
  store.fetchChannels()
}

onMounted(() => {
  store.fetchChannels()
})
</script>