#  AI Industry Daily Brief

每天自动收集最近 24 小时的全球 AI 新闻，使用 DeepSeek 完成筛选、分类和中文总结，并在北京时间早上 9 点推送到飞书/Lark 手机端。


每天收到一份结构化中文 AI 日报，覆盖：

-  模型与技术
-  商业动态
-  政策法规
-  产品发布
-  行业应用
-  安全与治理

每条信息包含：

- 中文总结标题
- 公司或机构
- 发布时间
- 发生了什么
- 主要变化
- 新闻内容总结
- 对世界或 AI 发展的影响
- 资本市场观察
- 原始新闻链接

系统还会把每天的日报保存到仓库的 `reports/` 文件夹，方便以后查阅。

---

## 工作原理

```text
公开 RSS 新闻源
        ↓
收集最近 24 小时的 AI 新闻
        ↓
关键词评分、来源评级和初步去重
        ↓
DeepSeek 筛选、分类和中文总结
        ↓
生成 AI 行业日报
        ↓
保存到 reports/
        ↓
通过飞书 Webhook 推送到手机
```

---

# 10 分钟快速部署

开始前，请准备：

- 一个 GitHub 账号
- 一个飞书/Lark 账号
- 一个 DeepSeek API 账号
- DeepSeek 账户中的少量可用余额


---

## 第 1 步：复制这个项目

点击仓库右上方的：

```text
Fork
```

将项目复制到自己的 GitHub 账号。

复制完成后，请确认浏览器左上角显示的是：

```text
你的用户名 / daily-market-brief
```

而不是原作者的用户名。

> Fork 后，GitHub Secrets 不会被复制。你必须配置自己的 API Key 和 Webhook。

---

## 第 2 步：创建飞书/Lark 机器人

### 2.1 创建一个群聊

在飞书中创建一个群聊。群里可以只有你自己，例如：

```text
AI 行业日报
```

### 2.2 添加自定义机器人

进入群聊后，依次打开：

```text
群设置
→ 机器人
→ 添加机器人
→ 自定义机器人
```

机器人名称可以填写：

```text
AI 行业日报机器人
```

### 2.3 设置关键词

建议选择“自定义关键词”安全设置，并填写：

```text
AI资本日报
```

程序发送的消息中必须包含这个关键词，否则飞书可能拒绝推送。

### 2.4 复制 Webhook

创建完成后，飞书会生成一个 Webhook URL，形式类似：

```text
https://open.feishu.cn/open-apis/bot/v2/hook/xxxxxxxx
```

请暂时复制并安全保存。

**不要把 Webhook 发到聊天中，也不要写进代码或 README。**

### 2.5 开启手机通知

在飞书手机端打开刚才的群聊：

```text
群设置
→ 消息通知
→ 所有消息
```

同时确认：

- 群聊没有开启免打扰
- 手机系统允许飞书发送通知
- 锁屏通知和横幅通知已开启
- 勿扰模式没有屏蔽飞书

---

## 第 3 步：创建 DeepSeek API Key

登录 DeepSeek API Platform，进入 API Keys 页面，然后：

1. 点击创建新的 API Key
2. 名称可以填写 `daily-market-brief`
3. 创建后立即复制完整 Key
4. 将它临时保存在安全的位置
5. 确认 DeepSeek 账户中有少量可用余额

API Key 通常以 `sk-` 开头。

**完整 Key 通常只在创建时显示一次。**

如果忘记保存，最安全的方法是删除旧 Key，再创建一个新的。

DeepSeek API 按实际使用量计费。该项目每天通常只调用一次，但实际费用取决于候选新闻数量和日报长度。

---

## 第 4 步：配置 GitHub Secrets

进入你自己的仓库：

```text
Settings
→ Secrets and variables
→ Actions
→ New repository secret
```

依次添加两个 Secret。

### Secret 1

```text
Name: DEEPSEEK_API_KEY
Secret: 粘贴你的 DeepSeek API Key
```

### Secret 2

```text
Name: FEISHU_WEBHOOK_URL
Secret: 粘贴你的飞书 Webhook URL
```

完成后，页面应该只显示以下名称：

```text
DEEPSEEK_API_KEY
FEISHU_WEBHOOK_URL
```

GitHub 不会再次显示 Secret 的完整内容，这是正常的。

### 常见错误

下面这些名称都不正确：

```text
DEEPSEEK_API
DEEPSEEK_KEY
FEISHU_URL
```

Secret 名称必须和代码完全一致。

---

## 第 5 步：允许并运行 GitHub Actions

进入仓库顶部的：

```text
Actions
```

第一次进入时，GitHub 可能要求你确认启用工作流。

点击：

```text
I understand my workflows, go ahead and enable them
```

然后在左侧选择：

```text
Daily AI Market Brief
```

点击右上角：

```text
Run workflow
```

Branch 保持：

```text
main
```

再次点击绿色的：

```text
Run workflow
```

等待约 1～3 分钟，然后刷新页面。

### 成功标准

你应该同时看到：

- GitHub Actions 显示绿色对号 `Success`
- 飞书群收到 AI 日报
- 仓库中出现或更新 `reports/日期.md`

例如：

```text
reports/2026-07-16.md
```

> 请使用 `Run workflow` 测试最新代码。  
> `Re-run all jobs` 可能重新运行某次旧提交，不适合首次测试新版本。

---

## 第 6 步：确认每天早上 9 点运行

打开：

```text
.github/workflows/daily-report.yml
```

定时部分应为：

```yaml
on:
  schedule:
    - cron: "0 1 * * *"

  workflow_dispatch:
```

GitHub Actions 的 cron 默认使用 UTC：

```text
UTC 01:00 = 北京时间 09:00
```

因此，工作流会每天在北京时间早上 9 点左右运行。

GitHub Actions 偶尔可能因为服务器排队延迟几分钟，这属于正常情况。

---

# 📁 项目结构

```text
daily-market-brief/
├── .github/
│   └── workflows/
│       └── daily-report.yml
├── reports/
│   └── YYYY-MM-DD.md
├── main.py
└── README.md
```

| 文件 | 作用 |
|---|---|
| `main.py` | 收集新闻、筛选候选、调用 DeepSeek、生成日报并推送飞书 |
| `daily-report.yml` | 设置定时运行、读取 Secrets 并保存日报 |
| `reports/` | 保存每天生成的历史日报 |
| `README.md` | 项目说明和部署教程 |

---

#  自定义设置

## 修改每天的新闻数量

在 `.github/workflows/daily-report.yml` 的 `env` 中加入：

```yaml
FINAL_ITEM_COUNT: "18"
```

完整示例：

```yaml
- name: Generate and send daily report
  env:
    FEISHU_WEBHOOK_URL: ${{ secrets.FEISHU_WEBHOOK_URL }}
    DEEPSEEK_API_KEY: ${{ secrets.DEEPSEEK_API_KEY }}
    DEEPSEEK_MODEL: deepseek-v4-flash
    FINAL_ITEM_COUNT: "18"
  run: python main.py
```

建议设置为：

```text
8～20 条
```

数量越多，日报越长，API 使用量通常也越高。

---

## 修改推送时间

GitHub cron 使用 UTC。

| 北京时间 | cron |
|---|---|
| 08:00 | `0 0 * * *` |
| 09:00 | `0 1 * * *` |
| 12:00 | `0 4 * * *` |
| 19:00 | `0 11 * * *` |

例如每天北京时间晚上 7 点：

```yaml
on:
  schedule:
    - cron: "0 11 * * *"

  workflow_dispatch:
```

---

## 修改日报栏目

日报目前分为：

```text
模型与技术
商业动态
政策法规
产品发布
行业应用
安全与治理
```

如需修改栏目，需要同步调整 `main.py` 中的：

- 分类名称
- 搜索关键词
- DeepSeek 系统提示词
- 输出顺序

初次使用时，建议先保持默认设置。

---

# 🔐 安全提醒

请务必遵守：

- 不要把 DeepSeek API Key 写进 `main.py`
- 不要把飞书 Webhook 上传到公开仓库
- 不要在 README、Issue 或 Pull Request 中公开密钥
- 不要把完整 API Key 发到聊天中
- 不要在截图中显示 API Key 或 Webhook
- 所有密钥必须保存在 GitHub Secrets
- 密钥泄露后，立即删除并重新创建

错误示例：

```text
DEEPSEEK_API_KEY=sk-真实密钥
```

正确做法：

```text
GitHub Settings
→ Secrets and variables
→ Actions
```

---

#  常见问题

## 1. Actions 显示成功，但飞书没有消息

请检查：

- 机器人是否还在目标群聊中
- `FEISHU_WEBHOOK_URL` 是否有效
- 机器人关键词是否为 `AI资本日报`
- 飞书群是否开启“所有消息通知”
- 手机系统是否允许飞书通知
- 群聊是否开启了免打扰

## 2. 提示没有读取到 `DEEPSEEK_API_KEY`

正确名称：

```text
DEEPSEEK_API_KEY
```

请进入：

```text
Settings
→ Secrets and variables
→ Actions
```

重新检查。

## 3. DeepSeek 返回 401

一般表示身份验证失败，可能原因包括：

- API Key 输入错误
- API Key 已被删除
- GitHub Secret 中只粘贴了部分 Key
- Key 前后存在多余空格

解决方法：

1. 在 DeepSeek 创建新的 API Key
2. 更新 GitHub Secret
3. 再次点击 `Run workflow`

## 4. DeepSeek 返回 402

一般表示 DeepSeek 账户余额不足。

充值后重新运行即可。

## 5. DeepSeek 返回 400 或 422

通常表示请求格式、参数或模型名称不兼容。

请检查：

```yaml
DEEPSEEK_MODEL: deepseek-v4-flash
```

如果 DeepSeek 官方更新了可用模型，请按照其最新文档修改模型名称。

## 6. 为什么收到多条飞书消息？

飞书单条文本存在长度限制。

当日报较长时，程序会自动拆分，例如：

```text
AI资本日报｜2026-07-16｜第1/4部分
AI资本日报｜2026-07-16｜第2/4部分
```

这是正常现象。

## 7. 为什么没有刚好在 09:00 收到？

GitHub Actions 定时任务可能因服务器排队延迟几分钟。

如果延迟数小时，请检查：

- cron 是否按照 UTC 设置
- 工作流是否在默认分支 `main`
- 当天的 Actions 是否运行失败
- 公共仓库是否长期没有活动，导致计划任务被自动暂停

## 8. 为什么日报条数少于设置数量？

系统优先保留高价值信息，并删除：

- 重复事件
- 营销稿
- 低价值内容
- 信息严重不足的新闻

因此，优质内容不足时，最终条数可能低于上限。

## 9. 为什么报告已推送，但 `reports/` 没有更新？

打开工作流文件，确认包含：

```yaml
permissions:
  contents: write
```

在 Actions 中依次打开：

```text
对应运行记录
→ generate-and-send
→ Save report to repository
```

查看具体日志。

---

# ⚠️ 已知限制

- 部分 RSS 只提供标题和很短的摘要
- 某些付费媒体正文无法完整读取
- 新闻链接可能经过 Google News 跳转
- DeepSeek 主要依据候选新闻标题和 RSS 摘要总结
- 自动分类和影响判断可能存在误差
- 关键数据应回到公司公告、监管文件和原始来源核验
- 所有资本市场观察均不构成投资建议

---

# 🧩 项目展示的能力

- Python Automation
- RSS Feed Processing
- Information Ranking
- News Deduplication
- Prompt Engineering
- Structured JSON Output
- DeepSeek API Integration
- GitHub Actions
- GitHub Secrets
- Webhook Integration
- Error Handling
- Fallback Design
- Technical Documentation


---

# 📄 License

MIT License

---


希望这个模板也能帮助你搭建属于自己的信息系统。
