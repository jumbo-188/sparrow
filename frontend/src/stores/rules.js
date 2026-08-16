import { defineStore } from 'pinia'
import api from '../api'

export const useRulesStore = defineStore('rules', {
  state: () => ({
    rules: [],
    channels: [],
    loading: false
  }),
  actions: {
    async fetchRules() {
      this.loading = true
      try {
        const res = await api.get('/config/rules')
        this.rules = res.data
      } finally {
        this.loading = false
      }
    },
    async fetchChannels() {
      const res = await api.get('/config/channels')
      this.channels = res.data
    },
    async createRule(data) {
      const res = await api.post('/config/rules', data)
      await this.fetchRules()
      return res.data
    },
    async updateRule(id, data) {
      const res = await api.put(`/config/rules/${id}`, data)
      await this.fetchRules()
      return res.data
    },
    async deleteRule(id) {
      await api.delete(`/config/rules/${id}`)
      await this.fetchRules()
    },
    async testPush(ruleId, data = {}) {
      const res = await api.post('/push/test', { rule_id: ruleId, data })
      return res.data
    }
  }
})