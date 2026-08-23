# sign-myself

> **声明：本项目仅供学习与交流使用。**
>
> 本项目代码由 AI 生成，使用者应自行审查代码内容并承担一切使用风险（包括但不限于账号封禁、数据丢失等）。请勿将本脚本用于任何商业或盈利目的。如相关平台或服务提供商认为本工具侵犯了您的权益，请联系作者删除。

一个用于自动签到的工具，支持通过 GitHub Actions 全自动运行，并可通过多种渠道接收通知。

## 主要功能

-   **明日方舟签到**：利用 GitHub Actions，每天定时为你完成森空岛签到。
-   **终末地签到**：自动完成《明日方舟：终末地》的每日签到，领取奖励。
-   **Bilibili 每日登录**：自动登录 B 站领取每日登录硬币。
-   **多账号支持**：只需配置一次，即可同时为多个账号签到。
-   **多平台通知**：签到完成后，可通过微信、Telegram、Discord 等渠道接收结果通知。
-   **安全可靠**：你的账号凭证存放在 GitHub Secrets 中，不会泄露。

## 使用方法

### 1. Fork 本仓库
点击本页右上角的 `Fork` 按钮，将这个项目复制到你自己的 GitHub 账号下。

### 2. 配置森空岛 Token（明日方舟 + 终末地）

你需要获取并配置你的 `SKLAND_TOKEN`，明日方舟和终末地签到共用此 Token。

1.  **获取 Token**:
    *   在电脑浏览器中登录 [森空岛](https://www.skland.com/)。
    *   登录后进入 https://web-api.skland.com/account/info/hg
    *   格式如下：`{"code":0,"data":{"content":"****"},"msg":"..."}`
    *   找到 `{"content":"****"}`，复制 `****` 中的内容，并保存。

2.  **添加 Secret**:
    *   进入你 Fork 的仓库，点击 `Settings` -> `Secrets and variables` -> `Environments`。
    *   点击 `New repository secret`。
    *   **Name** 填写 `SKLAND_TOKEN`，**Value** 粘贴你刚才复制的 Token。
    *   如果你有多个账号，可以将多个 Token 用英文逗号 `,` 连接起来，作为一个值填入。

### 3. 配置 Bilibili Cookie

1.  **获取 Cookie**:
    *   在电脑浏览器中登录 [Bilibili](https://www.bilibili.com/)。
    *   按 `F12` 打开开发者工具，进入 `Application` -> `Cookies` -> `https://www.bilibili.com`。
    *   找到以下三个值并复制：
        *   `SESSDATA`（必需）
        *   `DedeUserID`（必需）
        *   `bili_jct`（可选）

2.  **添加 Secret**:
    *   进入仓库 `Settings` -> `Environments` -> 创建或选择一个环境（如 `bilibili`）。
    *   分别添加以下三个 Secret：

    | Secret 名称 | 说明 |
    | :--- | :--- |
    | `BILI_SESSDATA` | B 站登录凭证（必需） |
    | `BILI_DEDEUSERID` | B 站用户 ID（必需） |
    | `BILI_JCT` | CSRF Token（可选） |

### 4. 启用 GitHub Actions
*   进入你仓库的 `Actions` 标签页。
*   点击 `I understand my workflows, go ahead and enable them`。
*   完成！各脚本将按照以下时间自动运行：

| 任务 | 运行时间（北京时间） | 工作流文件 |
| :--- | :--- | :--- |
| 明日方舟签到 | 每天 06:00 | `skland-sign.yml` |
| Bilibili 登录 | 每天 06:00 | `bilibili-login.yml` |
| 终末地签到 | 每天 13:00 | `endfield-sign.yml` |

你也可以在 Actions 页面手动触发任意工作流。

## 配置通知（可选）

如果你希望签到后收到通知，可以按需添加以下 Secret。添加方法与添加 `SKLAND_TOKEN` 相同。所有脚本共享同一套通知配置。

| 通知平台 | Secret 名称 | 说明与获取提示 | 已测试 |
| :--- | :--- | :--- | :--- |
| **企业微信** | `WECHAT_WEBHOOK_URL` | 填写企业微信群机器人的 Webhook 地址。 | ✓ |
| **Discord** | `DISCORD_WEBHOOK_URL` | 填写 Discord 频道设置的 Webhook 地址。 | 正在测试 |
| **Telegram** | `TELEGRAM_BOT_TOKEN` 和 `TELEGRAM_CHAT_ID` | 需要通过 `@BotFather` 创建机器人来获取 Token 和 Chat ID。 | 正在测试 |
| **飞书** | `FEISHU_WEBHOOK_URL` | 填写飞书群自定义机器人的 Webhook 地址。 | 正在测试 |
| **Bark** | `BARK_URL` | 填写 Bark App 为你生成的推送 URL。 | 正在测试 |
| **PushPlus** | `PUSHPLUS_TOKEN` | 在 PushPlus 官网申请 Token。 | 正在测试 |
| **Server酱** | `SERVER_CHAN_KEY` | 在 Server酱官网申请 SCKEY。 | 正在测试 |
| **自定义 Webhook** | `CUSTOM_WEBHOOK_URL` | 填写任意支持 POST JSON 的 Webhook 地址。 | 正在测试 |

## 常见问题

**Q：Token 会过期吗？需要经常换吗？**

**A：** 通常不会。`SKLAND_TOKEN` 有效期很长，一般只有在你长时间未使用或修改密码后才会失效。如果脚本运行失败并提示 Token 错误，再按上述步骤重新获取一次即可。B 站的 `SESSDATA` 同理，过期后重新从浏览器获取即可。

**Q：签到失败或收不到通知怎么办？**

**A：** 请按以下步骤排查：
1.  去仓库的 `Actions` 标签页，查看最近一次运行的详细日志，通常会有明确的错误信息。
2.  检查你配置的 Secret（Token 和通知地址）是否填写正确，特别是注意不要有多余的空格。
3.  确认你配置的通知渠道（如 Telegram Bot）本身工作正常。

**Q：可以修改签到时间吗？**

**A：** 可以。编辑对应的 `.github/workflows/` 下的工作流文件，找到 `cron` 配置行。cron 使用 UTC 时间，北京时间 = UTC + 8。例如北京时间 13:00 = UTC 05:00，写作 `cron: '0 5 * * *'`。

**Q：终末地签到提示"未经授权"怎么办？**

**A：** 请确认你已在森空岛 App 或网页端绑定了终末地游戏角色。未绑定角色的账号无法签到。

## 文件说明

```
├── skland_github.py              # 明日方舟签到脚本
├── endfield_github.py            # 终末地签到脚本
├── bilibili_login.py             # Bilibili 每日登录脚本
├── notify.py                     # 共享通知模块
├── requirements.txt              # Python 依赖列表
└── .github/workflows/
    ├── skland-sign.yml           # 明日方舟签到工作流
    ├── endfield-sign.yml         # 终末地签到工作流
    └── bilibili-login.yml        # Bilibili 登录工作流
```

## 致谢与参考

- 森空岛签到逻辑参考了 [skyland-auto-sign](https://gitee.com/FancyCabbage/skyland-auto-sign)
- 终末地签到逻辑参考了 [nonebot-plugin-skland](https://github.com/FrostN0v0/nonebot-plugin-skland)
- Bilibili 每日登录思路参考了 [BiliBiliToolPro](https://github.com/RayWangQvQ/BiliBiliToolPro)、[BILIBILI-HELPER](https://github.com/JunzhouLiu/BILIBILI-HELPER) 等开源项目

请勿将本脚本用于任何商业或盈利目的。

## 最后

如果觉得这个项目有帮助，欢迎给个 Star。祝你游戏愉快！
