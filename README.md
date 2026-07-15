# 🤖 Build Your Own AI Daily Brief

一个基于 **Python、DeepSeek API、GitHub Actions 和飞书/Lark 自定义机器人** 的自动化 AI 行业日报项目。

它会每天自动收集最近 24 小时的全球 AI 新闻，完成筛选、去重、分类、中文总结和影响分析，并在北京时间早上 9 点推送到飞书手机端，同时把历史日报保存到 GitHub 仓库。

---

## 项目背景

这个项目来自一个很实际的需求：

> 我希望每天早上在手机上收到一份结构清晰、来源可靠、能快速说明“发生了什么、为什么重要”的 AI 行业日报。

但日常获取 AI 信息时，我遇到了几个问题：

- 新闻来源分散
- 重复信息较多
- 营销稿和低价值内容较多
- 技术、商业、政策和应用信息混在一起
- 很难快速判断一条新闻对 AI 行业和资本市场的影响
- 每天手动整理需要大量时间

因此，我从一个空的 GitHub 仓库开始，逐步搭建了这套自动化工作流。

---

## 最终效果

每天系统会自动生成一份中文 AI 行业日报，并推送到飞书/Lark 群聊。

日报按以下六个栏目整理：

- 🧠 模型与技术
- 💰 商业动态
- 📋 政策法规
- 🚀 产品发布
- 🏭 行业应用
- 🛡️ 安全与治理

每条新闻包含：

- 中文总结标题
- 涉及公司或机构
- 发布时间
- 发生了什么
- 相比此前有什么变化
- 新闻内容总结
- 对世界或 AI 发展的潜在影响
- 资本市场观察
- 原始标题
- 来源链接
- 信息不足时的“待确认”提示

---

## 系统工作流程

```text
公开 RSS / 新闻搜索结果
        ↓
收集最近 24 小时 AI 新闻
        ↓
来源权重与关键词评分
        ↓
标题去重与候选筛选
        ↓
DeepSeek 进行分类、筛选和中文总结
        ↓
生成结构化 AI 行业日报
        ↓
保存到 reports/ 文件夹
        ↓
通过飞书 Webhook 推送
        ↓
手机收到通知
```

---

## 技术栈

- Python
- DeepSeek API
- RSS Feed Processing
- GitHub Actions
- GitHub Secrets
- Feishu / Lark Webhook
- JSON Structured Output
- Prompt Engineering
- Workflow Automation

---

## 项目结构

```text
daily-market-brief/
├── .github/
│   └── workflows/
│       └── daily-report.yml
├── reports/
│   └── YYYY-MM-DD.md
├── screenshots/
│   └── feishu-demo.png
├── main.py
├── README.md
└── .gitignore
```

### 文件说明

| 文件 | 作用 |
|---|---|
| `main.py` | 收集新闻、筛选候选、调用 DeepSeek、生成日报并推送飞书 |
| `.github/workflows/daily-report.yml` | 设置每天自动运行的 GitHub Actions 工作流 |
| `reports/` | 保存每天生成的历史日报 |
| `screenshots/` | 存放飞书推送效果截图 |
| `README.md` | 项目说明、配置步骤和使用文档 |

---

# 🚀 快速开始

## 1. Fork 或复制项目

你可以直接 Fork 本仓库，也可以将它复制到自己的 GitHub 账号。

复制后，需要使用你自己的：

- DeepSeek API Key
- 飞书/Lark 自定义机器人 Webhook

本项目不会提供公共密钥。

---

## 2. 创建飞书/Lark 自定义机器人

### 创建一个私人群

在飞书中创建一个群聊。群里可以只有你自己。

例如：

```text
AI行业日报
```

### 添加机器人

进入：

```text
群设置
→ 机器人
→ 添加机器人
→ 自定义机器人
```

建议设置：

```text
机器人名称：AI行业日报机器人
安全关键词：AI资本日报
```

创建成功后，飞书会生成一个 Webhook URL。

示例：

```text
https://open.feishu.cn/open-apis/bot/v2/hook/xxxxxxxx
```

请不要把真实 Webhook 写进代码、README、Issue 或截图中。

---

## 3. 创建 DeepSeek API Key

1. 登录 DeepSeek API Platform
2. 进入 API Keys 页面
3. 创建新的 API Key
4. 立即复制并安全保存
5. 确认账户中有可用余额

DeepSeek API 会按实际使用量计费。

每日成本主要取决于：

- 候选新闻数量
- RSS 摘要长度
- 日报条数
- 模型输入和输出长度

---

## 4. 配置 GitHub Secrets

进入你的 GitHub 仓库：

```text
Settings
→ Secrets and variables
→ Actions
→ New repository secret
```

添加以下两个 Repository Secret：

| Secret 名称 | 内容 |
|---|---|
| `DEEPSEEK_API_KEY` | 你的 DeepSeek API Key |
| `FEISHU_WEBHOOK_URL` | 你的飞书机器人 Webhook |

保存后，GitHub 不会再次显示 Secret 的完整内容，这是正常的。

请确保名称完全一致。

正确：

```text
DEEPSEEK_API_KEY
FEISHU_WEBHOOK_URL
```

错误示例：

```text
DEEPSEEK_API
DEEPSEEK_KEY
FEISHU_URL
```

---

## 5. 配置 GitHub Actions

打开：

```text
.github/workflows/daily-report.yml
```

确保工作流将两个 Secret 传给程序：

```yaml
- name: Generate and send daily report
  env:
    FEISHU_WEBHOOK_URL: ${{ secrets.FEISHU_WEBHOOK_URL }}
    DEEPSEEK_API_KEY: ${{ secrets.DEEPSEEK_API_KEY }}
    DEEPSEEK_MODEL: deepseek-v4-flash
  run: python main.py
```

---

## 6. 设置每天早上 9 点运行

GitHub Actions 的 cron 默认使用 UTC。

北京时间 09:00 等于 UTC 01:00，因此推荐这样设置：

```yaml
on:
  schedule:
    - cron: "0 1 * * *"

  workflow_dispatch:
```

含义：

```text
每天 UTC 01:00
=
每天北京时间 09:00
```

`workflow_dispatch` 用于保留手动运行按钮。

GitHub Actions 有时会因为服务器排队延迟几分钟，这属于正常情况。

---

## 7. 手动运行测试

进入仓库：

```text
Actions
→ Daily AI Market Brief
→ Run workflow
```

Branch 保持：

```text
main
```

然后点击绿色的：

```text
Run workflow
```

成功时会显示绿色对号，并在飞书中收到日报。

---

# 📊 日报分类逻辑

## 🧠 模型与技术

关注：新模型、训练与推理、多模态、基准测试、开源模型、智能体和效率变化。

## 💰 商业动态

关注：融资、IPO、并购、投资、财报、收入、估值、订单，以及芯片、算力、云、数据中心、电力、存储和网络。

## 📋 政策法规

关注：AI 监管、出口管制、版权、反垄断、政府采购、法律与市场准入。

## 🚀 产品发布

关注：新产品、App、API、AI 助手、Copilot、智能体和开发者工具。

## 🏭 行业应用

关注：医疗、金融、制造、汽车、教育、零售、企业服务和机器人。

## 🛡️ 安全与治理

关注：AI 安全、隐私、深度伪造、红队测试、模型评测、对齐、审计和治理机制。

---

# 🧠 DeepSeek 在项目中的作用

DeepSeek 不负责直接搜索互联网，而是处理已经收集到的候选新闻：

- 判断新闻重要性
- 去除重复事件
- 按栏目分类
- 生成中文总结标题
- 提取公司、机构和时间
- 总结发生了什么
- 分析主要变化
- 说明对世界和 AI 发展的潜在影响
- 生成资本市场观察
- 对信息不足内容标注“待确认”

为了降低幻觉风险，提示词要求模型：

- 只能使用候选新闻提供的信息
- 不得新增来源链接
- 不得虚构金额、股价、交易条款或模型指标
- 信息不足时使用谨慎表达
- 区分新闻事实和影响推断
- 资本市场观察必须注明“不构成投资建议”

---

# ⚙️ 自定义设置

## 修改日报条数

在工作流环境变量中加入：

```yaml
FINAL_ITEM_COUNT: "18"
```

推荐范围：8—20 条。条数越多，API 使用量通常越高。

## 修改候选新闻数量

```yaml
MAX_CANDIDATES_FOR_AI: "45"
```

推荐范围：25—50 条。

## 修改推送时间

每天北京时间 08:00：

```yaml
schedule:
  - cron: "0 0 * * *"
```

每天北京时间 09:00：

```yaml
schedule:
  - cron: "0 1 * * *"
```

每天北京时间 19:00：

```yaml
schedule:
  - cron: "0 11 * * *"
```

---

# 📰 日报格式示例

```text
🤖 AI行业日报｜2026-07-16

今日AI行业继续围绕模型能力、商业化落地与监管治理展开。

📊 今日概览
收录资讯：18条
覆盖分类：模型与技术、商业动态、政策法规、产品发布、行业应用、安全与治理

————————————
🧠 模型与技术

1. 某公司发布新一代多模态模型，推理成本进一步下降

公司/机构：某公司
发布时间：北京时间 2026-07-16 08:10

发生了什么：
某公司发布了新一代多模态模型。

主要变化：
模型推理效率和上下文能力较此前版本有所提升。

新闻总结：
……

对世界/AI发展的影响：
模型成本下降可能降低AI应用开发门槛，并加快企业部署。

资本市场观察：
需要跟踪推理成本、API定价和开发者采用率；不构成投资建议。

来源：
https://example.com
```

---

# 🔐 安全提醒

- 不要把 DeepSeek API Key 写进 `main.py`
- 不要把飞书 Webhook 上传到公开仓库
- 不要在 README、Issue 或 Pull Request 中公开密钥
- 不要把完整 API Key 发送到聊天中
- 不要在截图中显示 API Key 或 Webhook
- 所有密钥必须存入 GitHub Actions Secrets
- 密钥泄露后，应立即删除并重新创建
- 不要随意给陌生人仓库写入权限

错误示例：

```text
DEEPSEEK_API_KEY=sk-真实密钥
```

正确示例：

```text
DEEPSEEK_API_KEY=your_deepseek_api_key
```

---

# 🛠️ 常见问题

## GitHub Actions 成功，但飞书没有收到消息

检查机器人是否仍在群里、Webhook 是否有效、关键词是否匹配，以及手机通知和群通知是否开启。

## 没有读取到 DEEPSEEK_API_KEY

确认 Secret 名称准确为：

```text
DEEPSEEK_API_KEY
```

## DeepSeek 返回 401

通常表示 API Key 错误、失效、粘贴不完整或前后存在多余空格。

## DeepSeek 返回 402

通常表示 DeepSeek 账户余额不足。

## 为什么飞书收到多条消息

飞书单条文本消息存在长度限制，日报过长时程序会自动拆分发送。

## 为什么日报不一定正好有 18 条

系统不会用低质量内容凑数，同一事件也只保留一次。

## 为什么没有刚好在 09:00 收到

GitHub Actions 可能排队延迟几分钟。若延迟数小时，请检查 cron、默认分支、Actions 状态和运行日志。

---

# ⚠️ 已知限制

1. 部分来源只提供标题，不提供完整正文
2. 付费媒体内容可能无法完整读取
3. 某些链接可能经过 Google News 跳转
4. DeepSeek 主要依据标题和 RSS 摘要进行判断
5. 自动分类可能存在误差
6. 自动影响分析不等于专业研究报告
7. 关键数据仍应通过公司公告、监管文件和原始来源核验
8. 所有资本市场观察均不构成投资建议

---

# 🧩 这个项目让我学到了什么

通过这个项目，我完成了从个人需求到自动化产品的完整过程：

1. 把模糊需求转化为明确的信息结构
2. 使用 Python 收集和处理 RSS 新闻
3. 设计来源权重和关键词评分规则
4. 使用标题相似度完成初步去重
5. 通过 DeepSeek API 生成结构化 JSON
6. 设计限制模型幻觉的 Prompt
7. 使用 GitHub Actions 实现每日自动运行
8. 使用 GitHub Secrets 管理敏感信息
9. 使用 Webhook 连接飞书手机通知
10. 设计 API 失败时的 fallback 机制
11. 自动保存历史日报
12. 编写可供其他人复现的项目文档

这个项目让我理解了：

> 一个有价值的 AI 项目，不只是调用模型，而是把数据收集、规则筛选、模型处理、自动化运行、安全管理和用户交付连接成一个完整系统。

---

# 💼 Skills Demonstrated

- Python Automation
- RSS Feed Processing
- HTTP Requests
- Information Ranking
- News Deduplication
- Prompt Engineering
- LLM Structured Output
- DeepSeek API Integration
- GitHub Actions
- GitHub Secrets
- Webhook Integration
- Workflow Design
- Error Handling
- Fallback Logic
- Technical Documentation
- Open-source Project Design

---

# 🗺️ 后续计划

- [ ] 支持 Telegram、Slack、Email 和 Discord
- [ ] 增加自定义新闻来源
- [ ] 增加公司公告和监管文件来源
- [ ] 优化相似新闻聚类
- [ ] 增加日报网页展示
- [ ] 支持英文、中文和双语输出
- [ ] 增加行业自定义配置
- [ ] 增加每周总结
- [ ] 增加热门公司和主题追踪
- [ ] 增加失败通知与运行监控

---

# 🤝 贡献

欢迎提交 Issue、Pull Request、新的新闻来源、更好的去重逻辑、新栏目和其他推送平台支持。

提交代码前，请确认没有包含 API Key、Webhook URL、密码或其他敏感信息。

---

# 📄 License

建议使用 MIT License。

---

# ⭐ Support

如果这个项目帮助你搭建了自己的 AI 日报，欢迎给仓库一个 Star，也欢迎 Fork 后根据自己的行业、地区和兴趣进行定制。
