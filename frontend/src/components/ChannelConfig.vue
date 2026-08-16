<template>
  <n-data-table
    :columns="columns"
    :data="store.channels"
    :loading="store.loading"
    :bordered="true"
  />
</template>

<script setup>
import { h } from 'vue'
import { useRulesStore } from '../stores/rules'

const store = useRulesStore()

const columns = [
  { title: '名称', key: 'name', width: 120 },
  { title: '类型', key: 'type', width: 100 },
  { title: 'URL', key: 'url', ellipsis: true },
  {
    title: '默认参数',
    key: 'defaults',
    render(row) {
      const items = []
      if (row.default_channel) items.push(`channel: ${row.default_channel}`)
      if (row.default_group) items.push(`group: ${row.default_group}`)
      if (row.default_template) items.push(`template: ${row.default_template}`)
      return h('span', { style: 'font-size: 12px;' }, items.join(' | ') || '-')
    }
  }
]
</script>