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
    *   进入你 Fork 的仓库，点击 `Settings` -> `Secrets and variables` -> `Actions`。
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
    *   进入仓库 `Settings` -> `Secrets and variables` -> `Actions` -> `New repository secret`。
    *   分别添加以下三个 Secret：

    | Secret 名称 | 说明 |
    | :--- | :--- |
    | `BILI_SESSDATA` | B 站登录凭证（必需） |
    | `BILI_DEDEUSERID` | B 站用户 ID（必需） |
    | `BILI_JCT` | CSRF Token（可选） |

    支持多账号：多个账号的值用英文逗号 `,` 分隔填入同一个 Secret，按位置一一对应。

### 4. 启用 GitHub Actions
*   进入你仓库的 `Actions` 标签页。
*   点击 `I understand my workflows, go ahead and enable them`。
*   完成！各脚本将按照以下时间自动运行：

| 任务 | 运行时间（北京时间） | 工作流文件 |
| :--- | :--- | :--- |
| 明日方舟签到 | 每天 06:00 | `skland-sign.yml` |
| Bilibili 登录 | 每天 08:00 | `bilibili-login.yml` |
| 终末地签到 | 每天 13:00 | `endfield-sign.yml` |
| 通知测试 | 手动触发 | `test-notify.yml` |

你也可以在 Actions 页面手动触发任意工作流。

## 配置通知（可选）

如果你希望签到后收到通知，可以按需添加以下 Secret。进入仓库 `Settings` -> `Secrets and variables` -> `Actions` -> `New repository secret` 添加。所有脚本共享同一套通知配置。

| 通知平台 | Secret 名称 | 说明与获取提示 | 已测试 |
| :--- | :--- | :--- | :--- |
| **企业微信** | `WECHAT_WEBHOOK_URL` | 填写企业微信群机器人的 Webhook 地址。 | ✓ |
| **Discord** | `DISCORD_WEBHOOK_URL` | 填写 Discord 频道设置的 Webhook 地址。 | ✓ |
| **Telegram** | `TELEGRAM_BOT_TOKEN` 和 `TELEGRAM_CHAT_ID` | 需要通过 `@BotFather` 创建机器人来获取 Token 和 Chat ID。详见下方步骤。 | ✓ |
| **飞书** | `FEISHU_WEBHOOK_URL` | 填写飞书群自定义机器人的 Webhook 地址。 | 正在测试 |
| **Bark** | `BARK_URL` | 填写 Bark App 为你生成的推送 URL。 | 正在测试 |
| **PushPlus** | `PUSHPLUS_TOKEN` | 在 PushPlus 官网申请 Token。 | 正在测试 |
| **Server酱** | `SERVER_CHAN_KEY` | 在 Server酱官网申请 SCKEY。 | 正在测试 |
| **自定义 Webhook** | `CUSTOM_WEBHOOK_URL` | 填写任意支持 POST JSON 的 Webhook 地址，如 `https://example.com/webhook`。脚本会发送包含 `title`、`message`、`timestamp` 等字段的 JSON 请求体。 | 正在测试 |

### Telegram 机器人创建步骤

1.  **创建机器人，获取 Token**
    - 在 Telegram 搜索 `@BotFather`，打开对话
    - 发送 `/newbot`
    - 按提示输入机器人名称（显示名）和用户名（必须以 `bot` 结尾，如 `my_sign_notify_bot`）
    - 创建成功后会返回 Token，格式如：`7123456789:AAH1bC2dE3fG4hI5jK6lM7nO8pQ9rS0tU`

2.  **获取 Chat ID**
    - 搜索 `@userinfobot`，打开对话
    - 发送 `/start`，它会回复你的 Chat ID（一串数字，如 `123456789`）

3.  **先给你的机器人发一条消息**
    - 搜索你刚创建的机器人用户名，打开对话
    - 发送任意消息（必须发一条，否则机器人没权限给你发消息）

4.  **添加 Secret**
    - `TELEGRAM_BOT_TOKEN` → 第 1 步的 Token
    - `TELEGRAM_CHAT_ID` → 第 2 步的数字

## 常见问题

**Q：Token 会过期吗？需要经常换吗？**

**A：** 通常不会。`SKLAND_TOKEN` 有效期很长，一般只有在你长时间未使用或修改密码后才会失效。如果脚本运行失败并提示 Token 错误，再按上述步骤重新获取一次即可。B 站的 `SESSDATA` 同理，过期后重新从浏览器获取即可。

**Q：签到失败或收不到通知怎么办？**

**A：** 请按以下步骤排查：
1.  去仓库的 `Actions` 标签页，查看最近一次运行的详细日志，通常会有明确的错误信息。
2.  检查你配置的 Secret（Token 和通知地址）是否填写正确，特别是注意不要有多余的空格。
3.  确认你配置的通知渠道（如 Telegram Bot）本身工作正常。

**Q：可以修改签到时间吗？**

**A：** 可以。编辑对应的 `.github/workflows/` 下的工作流文件，找到 `cron` 配置行。cron 使用 UTC 时间，北京时间 = UTC + 8，所以 UTC = 北京时间 - 8。例如北京时间 13:00 = UTC 05:00，写作 `cron: '0 5 * * *'`。推荐使用 [crontab.guru](https://crontab.guru/) 在线生成和验证 cron 表达式。

GitHub Actions 使用标准 5 字段 POSIX cron 格式：

```
┌──────────── 分钟 (0-59)
│ ┌────────── 小时 (0-23)
│ │ ┌──────── 日 (1-31)
│ │ │ ┌────── 月 (1-12 或 JAN-DEC)
│ │ │ │ ┌──── 星期 (0-6 或 SUN-SAT，0=周日)
│ │ │ │ │
* * * * *
```

- `*` 任意值
- `1,3,5` 逗号分隔多个值
- `1-5` 范围
- `*/5` 每隔 N

注意：不支持秒字段、年字段，以及 `L`（最后一天）、`W`（工作日）、`#`（第N个星期X）等扩展语法。日和星期同时指定时取交集（标准 cron 为并集）。

**Q：终末地签到提示"未经授权"怎么办？**

**A：** 请确认你已在森空岛 App 或网页端绑定了终末地游戏角色。未绑定角色的账号无法签到。

## 文件说明

```
├── arknight_github.py             # 明日方舟签到脚本
├── endfield_github.py            # 终末地签到脚本
├── bilibili_login.py             # Bilibili 每日登录脚本
├── test_notify.py                # 通知渠道测试脚本
├── skland_common.py              # 森空岛公共模块（加密、签名、登录）
├── notify.py                     # 共享通知模块
├── requirements.txt              # Python 依赖列表
└── .github/workflows/
    ├── skland-sign.yml           # 明日方舟签到工作流
    ├── endfield-sign.yml         # 终末地签到工作流
    ├── bilibili-login.yml        # Bilibili 登录工作流
    └── test-notify.yml           # 通知测试工作流
```

## 致谢与参考

- 森空岛签到逻辑参考了 [skyland-auto-sign](https://gitee.com/FancyCabbage/skyland-auto-sign)
- 终末地签到逻辑参考了 [nonebot-plugin-skland](https://github.com/FrostN0v0/nonebot-plugin-skland)
- Bilibili 每日登录思路参考了 [BiliBiliToolPro](https://github.com/RayWangQvQ/BiliBiliToolPro)、[BILIBILI-HELPER](https://github.com/JunzhouLiu/BILIBILI-HELPER) 等开源项目

请勿将本脚本用于任何商业或盈利目的。

## 最后

如果觉得这个项目有帮助，欢迎给个 Star。祝你游戏愉快！
