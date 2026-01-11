# 森空岛自动签到脚本

一个用于森空岛（Skland）平台的自动签到工具，支持通过 GitHub Actions 全自动运行，并可通过多种渠道接收通知。

## 主要功能

-   **自动签到**：利用 GitHub Actions，每天定时为你完成森空岛签到。
-   **多账号支持**：只需配置一次，即可同时为多个账号签到。
-   **多平台通知**：签到成功后，可通过微信、Telegram、Discord 等渠道接收结果通知。
-   **安全可靠**：你的账号令牌（Token）存放在 GitHub Secrets 中，不会泄露。

## 使用方法

### 1. Fork 本仓库
点击本页右上角的 `Fork` 按钮，将这个项目复制到你自己的 GitHub 账号下。

### 2. 配置账号令牌 (Token)
这是最关键的一步。你需要获取并配置你的 `SKLAND_TOKEN`。

1.  **获取 Token**:
    *   在电脑浏览器中登录 [森空岛](https://www.skland.com/)。
    *   按 `F12` 打开开发者工具，切换到 **网络 (Network)** 标签页。
    *   刷新页面，在请求列表中找到一个名称包含 `grant` 的请求。
    *   点击该请求，在右侧的 **响应 (Response)** 或 **载荷 (Payload)** 中找到 `token` 字段，复制其长字符串值（形如 `eyJ...`）。

2.  **添加 Secret**:
    *   进入你 Fork 的仓库，点击 `Settings` -> `Secrets and variables` -> `Actions`。
    *   点击 `New repository secret`。
    *   **名称** 填写 `SKLAND_TOKEN`，**值** 粘贴你刚才复制的 Token。
    *   如果你有多个账号，可以将多个 Token 用英文逗号 `,` 连接起来，作为一个值填入。

### 3. 启用 GitHub Actions
*   进入你仓库的 `Actions` 标签页。
*   点击 `I understand my workflows, go ahead and enable them`。
*   完成！脚本将在 **UTC 时间 0点（北京时间早上8点）** 自动运行。

## 配置通知（可选）

如果你希望签到后收到通知，可以按需添加以下 Secret。添加方法与添加 `SKLAND_TOKEN` 相同。

| 通知平台 | Secret 名称 | 说明 |
| :--- | :--- | :--- |
| **企业微信** | `WECHAT_WEBHOOK_URL` | 填写企业微信机器人的 Webhook 地址。 |
| **Telegram** | `TELEGRAM_BOT_TOKEN` 和 `TELEGRAM_CHAT_ID` | 需要同时填写 Bot Token 和接收消息的聊天 ID。 |
| **Discord** | `DISCORD_WEBHOOK_URL` | 填写 Discord 频道的 Webhook 地址。 |
| **Bark** | `BARK_URL` | 填写 Bark App 提供的推送 URL。 |
| **PushPlus** | `PUSHPLUS_TOKEN` | 填写 PushPlus 的令牌。 |

## 常见问题

**Q：Token 会过期吗？需要经常换吗？**
**A：** 通常不会。`SKLAND_TOKEN` 有效期很长，一般只有在你长时间未使用或修改密码后才会失效。如果脚本运行失败并提示 Token 错误，再按上述步骤重新获取一次即可。

**Q：签到失败或收不到通知怎么办？**
**A：** 请按以下步骤排查：
1.  去仓库的 `Actions` 标签页，查看最近一次运行的详细日志，通常会有明确的错误信息。
2.  检查你配置的 Secret（Token 和通知地址）是否填写正确，特别是注意不要有多余的空格。
3.  确认你配置的通知渠道（如 Telegram Bot）本身工作正常。

**Q：可以修改签到时间吗？**
**A：** 可以。编辑仓库目录下的 `.github/workflows/sign.yml` 文件，找到 `cron: ‘0 0 * * *’` 这一行。这是 UTC 时间，如果你想在北京时间早上 7 点运行，可以改为 `cron: ‘0 23 * * *’`（即 UTC 前一天的 23 点）。

## 文件说明

- `skland_github.py`：主程序脚本。
- `.github/workflows/sign.yml`：GitHub Actions 工作流配置文件。
- `requirements.txt`：Python 依赖列表。

## 最后

如果觉得这个项目有帮助，欢迎给个 Star ⭐。
祝你游戏愉快！