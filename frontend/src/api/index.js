import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 15000,
})

api.interceptors.request.use(
  config => config,
  error => Promise.reject(error)
)

api.interceptors.response.use(
  response => response,
  error => {
    console.error('API Error:', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

// ============ 消息规则 API ============
export const fetchRules = () => api.get('/config/rules')
export const fetchRule = (id) => api.get(`/config/rules/${id}`)
export const createRule = (data) => api.post('/config/rules', data)
export const updateRule = (id, data) => api.put(`/config/rules/${id}`, data)
export const deleteRule = (id) => api.delete(`/config/rules/${id}`)

// ============ 渠道配置 API ============
export const fetchChannels = () => api.get('/config/channels')
export const createChannel = (data) => api.post('/config/channels', data)
export const updateChannel = (name, data) => api.put(`/config/channels/${name}`, data)
export const deleteChannel = (name) => api.delete(`/config/channels/${name}`)

// ============ 推送测试 API ============
export const testPush = (ruleId, data = {}) =>
  api.post('/push/test', { rule_id: ruleId, data })

// ============ 配置管理 API ============
export const reloadConfig = () => api.post('/config/reload')

// ============ 推送计划预览 API ============
export const previewDailyPlan = async (date) => {
  const params = date ? `?target_date=${date}` : ''
  const res = await api.get(`/planner/daily${params}`)
  return res.data // 直接返回后端 JSON
}

// ============ 每日计划汇总 API ============
export const getDailyPlanConfig = () => api.get('/daily-plan/config')
export const updateDailyPlanConfig = (data) => api.put('/daily-plan/config', data)
export const testDailyPlan = () => api.post('/daily-plan/test')

export default api