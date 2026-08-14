# 🕊️ Sparrow - 个人定时推送服务（NAS 版）

> 一只轻巧的数字信鸽，按你的节奏把消息送到 PushPlus（微信）和 Bark（iOS）。

Sparrow 是一个 **Python + FastAPI + APScheduler** 构建的定时推送中台。你只需在 `config.yaml` 里定义好**消息内容、发送时间、目标渠道**，它就会准时把消息推送到你的手机。所有敏感信息（Token）通过 `.env` 隔离，安全又灵活。

---

## ✨ 核心特性

- ⏰ **定时精准**：基于 APScheduler，支持完整的 Cron 表达式，精确到秒。
- 📨 **多渠道 POST**：统一使用 JSON POST 请求，同时支持 **PushPlus（微信）** 和 **Bark（iOS）**，并可扩展任何 Webhook 渠道。
- 🎨 **Bark 高级定制**：支持 `group`（消息分组）、`icon`（自定义图标）、`sound`、`badge` 等全部参数。
- 🗂️ **全配置化**：所有消息规则、模板、渠道参数都在 `config.yaml` 中声明，无需修改代码。
- 🔄 **热加载**：提供 `/api/v1/reload` 接口，修改配置后无需重启容器即可生效。
- 🐳 **NAS 原生适配**：提供 `docker-compose.yml`，一键部署在绿联 NAS（或其他 Docker 环境），开机自启。

---

## 📁 项目结构
```
sparrow/
├── config/
│ └── config.yaml # 你的消息规则（核心配置文件）
├── logs/ # 日志挂载目录
├── src/
│ ├── main.py # FastAPI 入口，启动调度器
│ ├── core/
│ │ ├── scheduler.py # APScheduler 任务管理
│ │ └── sender.py # 推送执行引擎（统一 POST JSON）
│ └── utils/
│ └── config_loader.py # 读取 YAML 并替换环境变量
├── docker-compose.yml # 绿联 NAS 专用编排
├── Dockerfile
├── .env # 存放 Token（不提交 Git）
├── requirements.txt
└── README.md
```
---

## 🚀 快速开始（绿联 NAS 部署）

### 1. 准备文件
在绿联 NAS 的 Docker 共享目录（例如 `共享文件夹/docker/sparrow/`）下，创建以下文件：

- `docker-compose.yml`
- `Dockerfile`
- `requirements.txt`
- `.env`
- 将 `src/` 和 `config/` 文件夹复制进去（按上述结构放置）。

> 如果你不想手动创建，可以直接 `git clone` 本仓库到 NAS 的 Docker 目录。

### 2. 配置环境变量（`.env`）
```env
# PushPlus 令牌（必填，如果使用 PushPlus）
PUSHPLUS_TOKEN=你的PushPlus_Token

# Bark 密钥（必填，如果使用 Bark）
BARK_KEY=你的Bark_Key

# 时区（确保定时任务使用北京时间）
TZ=Asia/Shanghai
