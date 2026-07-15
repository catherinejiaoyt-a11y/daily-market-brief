#  AI Industry Daily Brief

一个自动生成并推送 AI 行业日报的开源项目。

系统会每天收集最近 24 小时的全球 AI 新闻，使用 DeepSeek 完成筛选、分类和中文总结，再通过飞书/Lark 机器人推送到手机端。

## 功能

- 自动收集最近 24 小时的 AI 新闻
- 去重并筛选高价值信息
- 使用 DeepSeek 生成中文总结
- 按六个栏目整理：
  -  模型与技术
  -  商业动态
  -  政策法规
  -  产品发布
  -  行业应用
  -  安全与治理
- 每天北京时间 09:00 自动运行
- 推送到飞书/Lark
- 自动保存历史日报到 `reports/`

## 技术栈

- Python
- DeepSeek API
- RSS
- GitHub Actions
- GitHub Secrets
- Feishu/Lark Webhook

## 工作流程

```text
RSS 新闻源
→ 收集最近 24 小时新闻
→ 关键词评分和去重
→ DeepSeek 分类与总结
→ 生成中文日报
→ 保存到 GitHub
→ 推送到飞书手机端
```

## 快速开始

### 1. Fork 或复制本项目

将本仓库复制到自己的 GitHub 账号。

### 2. 创建飞书机器人

在飞书群中添加“自定义机器人”，复制 Webhook URL。

建议安全关键词设置为：

```text
AI资本日报
```

### 3. 创建 DeepSeek API Key

在 DeepSeek API Platform 创建自己的 API Key，并确保账户中有可用余额。

### 4. 配置 GitHub Secrets

进入：

```text
Settings
→ Secrets and variables
→ Actions
→ New repository secret
```

添加：

```text
DEEPSEEK_API_KEY
FEISHU_WEBHOOK_URL
```

不要把真实密钥写进代码或 README。

### 5. 手动测试

进入：

```text
Actions
→ Daily AI Market Brief
→ Run workflow
```

运行成功后，飞书会收到一份日报。

## 定时设置

`.github/workflows/daily-report.yml` 中：

```yaml
on:
  schedule:
    - cron: "0 1 * * *"

  workflow_dispatch:
```

GitHub Actions 默认使用 UTC。

```text
UTC 01:00 = 北京时间 09:00
```

## 项目结构

```text
daily-market-brief/
├── .github/workflows/daily-report.yml
├── reports/
├── main.py
└── README.md
```

## 安全提醒

- 不要公开 DeepSeek API Key
- 不要公开飞书 Webhook
- 所有密钥应保存到 GitHub Secrets
- 密钥泄露后应立即删除并重新创建
- 资本市场观察不构成投资建议

## Skills

- Python Automation
- RSS Processing
- Prompt Engineering
- DeepSeek API Integration
- GitHub Actions
- GitHub Secrets
- Webhook Integration
- Workflow Design

## License

MIT License
