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
```
### 3. 编辑消息规则（config/config.yaml）
```yaml
channels:
  - name: pushplus
    url: http://www.pushplus.plus/send
    method: POST
    headers: { Content-Type: application/json }
    payload_template: |
      { "token": "${PUSHPLUS_TOKEN}", "title": "{{ title }}", "content": "{{ message }}", "template": "markdown" }

  - name: bark
    url: https://api.day.app/${BARK_KEY}
    method: POST
    headers: { Content-Type: application/json }
    payload_template: |
      {
        "title": "{{ title }}",
        "body": "{{ message }}",
        "group": "{{ group }}",
        "icon": "{{ icon }}",
        "badge": {{ badge }},
        "sound": "{{ sound }}"
      }

messages:
  - id: morning
    schedule: "0 8 * * *"           # 每天 8:00 北京时间
    channel: bark
    default_data:
      title: "🌅 早安"
      group: "Daily"
      icon: "https://example.com/sun.png"
    template: "早上好！今天 {{ date }}，加油！"

  - id: evening
    schedule: "0 22 * * *"
    channel: pushplus
    default_data:
      title: "📝 晚安"
    template: "今日总结：{{ summary }}"
```
> 更多 Bark 参数（url, automaticallyCopy 等）可直接添加到 payload_template 中。

### 4. 构建并启动
在绿联 NAS 的 Docker 应用中，进入 项目（Compose），选择该目录，点击“构建并启动”。首次会下载 Python 镜像并安装依赖（约 3 分钟）。

### 5. 验证运行
- 访问 http://你的NAS_IP:8000/health，返回 {"status":"alive"} 即成功。
- 查看容器日志，应出现 ✅ 所有定时任务已加载。
- 可手动测试：POST http://你的NAS_IP:8000/api/v1/test，参数 {"route_id": "morning"}。

## 🔌 API 接口

| 接口           | 方法 | 说明                             |
|----------------|------|----------------------------------|
| /health        | GET  | 	健康检查                         |
| /api/v1/test   | POST | 	手动触发一条消息（不依赖定时）   |
| /api/v1/reload | POST | 重新加载 config.yaml，热更新任务 |
== 测试示例 == 
```shell
curl -X POST http://nas-ip:8000/api/v1/test \
  -H "Content-Type: application/json" \
  -d '{"route_id": "morning", "data": {"group": "Test"}}'
```
## 🛠️ 自定义与扩展

- **新增渠道**：在 `config.yaml` 的 `channels` 中添加新条目，只需提供 `url` 和 `payload_template` 即可。模板使用 Jinja2 语法，可引用 `message`（渲染后的消息正文）以及所有传入的 `data` 字段（包括 `default_data` 和 API 调用时传入的覆盖值）。

- **修改定时规则**：编辑 `schedule` 字段（Cron 表达式），支持任意复杂规则。常用示例：
  - `0 8 * * *` → 每天 8:00
  - `30 9 * * 1` → 每周一 9:30
  - `*/15 * * * *` → 每 15 分钟

- **动态数据**：在 `default_data` 中预设变量，或通过 API 调用时传入覆盖。你可以在模板里用 `{{ variable_name }}` 引用它们，也可以使用 Jinja2 过滤器（如 `default`、`urlencode` 等）。

- **日志查看**：容器内日志路径 `/app/logs/sparrow.log`，也可通过 NAS Docker 界面直接查看容器的实时日志。

- **扩展其他推送服务**（如飞书、钉钉、Server酱）：
  只需仿照现有渠道，在 `channels` 中新增一条配置，定义好 `url`、`headers` 和 `payload_template`，无需修改任何 Python 代码。Sparrow 会将其视为一个标准的 Webhook 渠道。

---

## 🐳 运维小贴士

- **开机自启**：`docker-compose.yml` 已配置 `restart: always`，NAS 重启后自动运行，无需手动干预。

- **时区问题**：确保 `.env` 中 `TZ=Asia/Shanghai`，并在 `docker-compose.yml` 中挂载了 `/etc/localtime:/etc/localtime:ro`。如果推送时间仍不对，进入容器执行 `date` 检查。

- **配置热更新**：修改 `config.yaml` 后，执行 `POST /api/v1/reload`，无需重启容器，调度器会重新加载所有消息规则（新增/修改/删除的任务都会生效）。

- **备份与迁移**：只需备份 `config/` 和 `.env` 两个文件夹/文件，即可在任意 Docker 主机上恢复服务。

- **资源占用**：Sparrow 非常轻量（内存约 50~80MB），适合长期运行在 NAS 或树莓派上。

---

## 📄 许可证

MIT License — 自由使用、修改，保留版权声明即可。

---

## 🤝 致谢

- [PushPlus](http://www.pushplus.plus/) - 微信推送服务
- [Bark](https://github.com/Finb/Bark) - iOS 自定义推送 App

---

**🐦 轻如麻雀，准如时钟。愿 Sparrow 让你的通知井井有条。**
