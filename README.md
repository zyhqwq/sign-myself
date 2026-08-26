# sign-myself

> [!CAUTION]
> **免责声明（请务必阅读）**
>
> 本项目仅供个人学习与交流使用，代码由 AI 生成，请自行审查后再使用。作者不承诺任何稳定性保证，接口变更导致功能失效也请理解；Issue 与 PR 欢迎提交，但可能无法及时响应。
>
> 使用自动化签到工具可能违反米游社《用户协议》并触发官方风控机制，存在账号功能受限、要求验证甚至封号的风险。使用本项目所产生的任何账号风险、数据丢失或其他后果，均由使用者自行承担。请勿将本项目用于任何商业或盈利目的；如相关平台或服务提供商认为本工具侵犯了您的权益，请联系我删除。
>
> 请合理、低频地使用，并妥善保管你的登录凭证（Cookie / stoken），切勿公开分享。
>
> - 🚫 禁止大范围宣传本项目，谢谢配合
> - 🚫 请不要发布到 B 站，谢谢
> - 🚫 请不要滥用本项目
>
> [!WARNING]
> **关于 GitHub Actions**：仓库内的工作流文件仅作参考示例。作者**不支持也不推荐**使用 GitHub Actions 来每日自动执行——Fork 仓库的 Actions 用量会归属到上游存储库，滥用可能导致上游仓库被停用。与 Actions 运行相关的 Issue 恕不处理。

一个用于自动签到的工具，支持多账号与多种通知渠道。

## 目录

- [主要功能](#main-features)
- [使用方法](#usage)
  - [1. 运行方式](#step-1-run)
    - [1.1 Linux 本地 / 服务器运行（推荐）](#step-1-linux)
    - [1.2 GitHub Actions（仅供参考，极不推荐，懒得修）](#step-1-actions)
      - [步骤 1：Fork 本仓库](#actions-fork)
      - [步骤 2：配置森空岛 Token](#actions-skland)
      - [步骤 3：配置米游社 Cookie](#actions-mihoyo)
      - [步骤 4：配置 Bilibili Cookie（可选）](#actions-bilibili)
      - [步骤 5：启用并运行](#actions-run)
  - [2. 凭证获取](#cred)
    - [2.1 森空岛凭证获取](#cred-skland)
    - [2.2 米游社Cookie获取](#cred-mihoyo)
    - [2.3 Bilibili Cookie 获取](#cred-bilibili)
  - [3. 选择要签到的游戏（可选）](#step-3-games)
- [配置通知（可选）](#notify-config)
  - [Telegram 机器人创建步骤](#telegram-steps)
  - [钉钉机器人创建步骤](#dingtalk-steps)
- [常见问题](#faq)
- [文件说明](#files)
- [致谢与参考](#credits)

<a id="main-features"></a>
## 主要功能

一个用于自动签到的工具，支持多账号与多种通知渠道。按平台分为两组：

**森空岛**（共用 `SKLAND_TOKEN`）
- **明日方舟签到**
- **终末地签到**

**米游社**（共用 `MIYOUSHE_COOKIE`）
- **原神签到**
- **崩坏:星穹铁道签到**
- **绝区零签到**

另外还有 **Bilibili 每日登录**（独立运行）。

-   **多账号支持**：只需配置一次，即可同时为多个账号签到。
-   **按序号选择游戏**：通过 Secret 选择要签到的游戏，不必全部都跑。
-   **多平台通知**：签到完成后，可通过微信、Telegram、Discord 等渠道接收结果通知。
-   **安全可靠**：你的账号凭证存放在 GitHub Secrets 中，不会泄露。

<a id="usage"></a>
## 使用方法

<a id="step-1-run"></a>
### 1. 运行方式

<a id="step-1-linux"></a>
#### 1.1 Linux 本地 / 服务器运行（推荐）

只需一条命令，跟着向导走完即可，不需要懂编程。

1. **下载项目**

   ```bash
   git clone https://github.com/zyhqwq/sign-myself.git
   cd sign-myself
   ```

2. **运行配置向导**

   ```bash
   python3 setup_sign.py
   ```

向导会自动完成所有事：

- 检查 Python 版本与依赖，缺失时自动尝试多种方式安装（优先用户目录，多数环境无需 root；极简系统若连 pip 都没有，补装时需要管理员权限）
- 询问是否有森空岛 [Token](#cred-skland) / 米游社 [Cookie](#cred-mihoyo)，有就填入，也可以当场扫码获取（获取方法统一见下文 [2 凭证获取](#cred)）
- 选择通知渠道：Discord / Telegram / 企业微信 / 飞书 / 钉钉(支持加签) / Server酱 / 自定义 Webhook / 邮件(SMTP)
- **当场实测**凭证和通知是否能用：通知发送后会询问是否收到，未收到可当场重新设置渠道；失败可以马上重填
- 设置每天的自动签到时间（全部回车 = 每天 03:25，北京时间），并写入系统定时任务

完成后：

| 项目 | 说明 |
| :--- | :--- |
| 参数文件 | `api.txt`（权限 600，含凭证，**请勿外传**；重跑向导会覆盖，旧文件备份为 `api.txt.bak`） |
| 日志 | `sign.log`（持续追加，可随时删除，不影响运行） |
| 手动测试 | `bash run.sh` |
| 修改配置 | 重新运行 `python3 setup_sign.py` 即可 |

<details>
<summary><b>不用向导？手动编辑配置</b></summary>

```bash
bash run.sh          # 首次运行会生成带中文注释的 api.txt 模板并提示
nano api.txt         # 按 nano 提示编辑：Ctrl+O 回车保存，Ctrl+X 退出（vim 用户自行 i/:wq）
bash run.sh          # 再次运行生效
```

定时任务也可手动添加到 `crontab -e`：

```text
25 3 * * * cd /home/你的用户名/sign-myself && bash run.sh >> sign.log 2>&1
```

</details>

> [!TIP]
> 全程无需 root 权限；建议把定时时间的分钟数改成随机值，避免固定整点请求。

<a id="step-1-actions"></a>
#### 1.2 GitHub Actions（仅供参考，极不推荐，懒得修）

<details>
<summary><b>点击展开：Fork 仓库、配置 Secrets 并使用 Actions 每日自动签到</b></summary>

> ⚠️ **再次提示**：仓库内的工作流文件**仅作参考示例**，作者**不支持也不推荐**使用 GitHub Actions 来每日自动执行，相关风险请自行评估（详见顶部免责声明）。

<a id="actions-fork"></a>
#### 步骤 1：Fork 本仓库

点击本页右上角的 `Fork` 按钮，将这个项目复制到你自己的 GitHub 账号下。

<a id="actions-skland"></a>
#### 步骤 2：配置森空岛 Token（明日方舟 + 终末地）

你需要获取并配置你的 `SKLAND_TOKEN`，明日方舟和终末地签到共用此 Token。

1.  **获取 Token**：步骤见 [2.1 森空岛凭证获取](#cred-skland)。
2.  **添加 Secret**:
    *   进入你 Fork 的仓库，点击 `Settings` -> `Secrets and variables` -> `Actions`。
    *   点击 `New repository secret`，添加以下 Secret：

    | Name | Secret | 说明 |
    | :--- | :--- | :--- |
    | `SKLAND_TOKEN` | 森空岛 Token | 明日方舟和终末地签到共用，多账号用英文逗号 `,` 分隔 |

<a id="actions-mihoyo"></a>
#### 步骤 3：配置米游社 Cookie

米游社签到需要 `MIYOUSHE_COOKIE`，用于自动完成原神、崩坏:星穹铁道、绝区零的每日签到（领原石、燃料、丁尼等）。脚本会自动检测账号绑定的角色，只签有角色的游戏。

> 📝 **注意**：米游社社区板块签到（米游币）已被官方限制第三方调用，故本项目只做游戏签到。

Cookie 通过扫码工具获取（无需手动抓包，Actions 里不执行登录），获取方式见 [2.2 米游社Cookie获取](#cred-mihoyo)。

**添加 Secret**：扫码成功后复制整段 Cookie，进入仓库 `Settings` -> `Secrets and variables` -> `Actions` -> `New repository secret`，添加以下 Secret：

| Name | Secret | 说明 |
| :--- | :--- | :--- |
| `MIYOUSHE_COOKIE` | 扫码得到的完整 Cookie | 含 `stoken` 等字段，多账号自动以英文逗号分隔 |

<a id="actions-bilibili"></a>
#### 步骤 4：配置 Bilibili Cookie（可选）

> 💡 **此步骤可选**：不需要 B 站登录功能可直接跳过，不影响其他游戏签到。

1.  **获取 Cookie**：步骤见 [2.3 Bilibili Cookie 获取](#cred-bilibili)。
2.  **添加 Secret**:
    *   进入仓库 `Settings` -> `Secrets and variables` -> `Actions` -> `New repository secret`。
    *   分别添加以下三个 Secret：

    | Name | Secret | 说明 |
    | :--- | :--- | :--- |
    | `BILI_SESSDATA` | `SESSDATA` | B 站登录凭证（必需） |
    | `BILI_DEDEUSERID` | `DedeUserID` | B 站用户 ID（必需） |
    | `BILI_JCT` | `bili_jct` | CSRF Token（可选） |

    支持多账号：多个账号的值用英文逗号 `,` 分隔填入同一个 Secret，按位置一一对应。

<a id="actions-run"></a>
#### 步骤 5：启用并运行

*   进入你仓库的 `Actions` 标签页。
*   点击 `I understand my workflows, go ahead and enable them`。
*   完成！各脚本将按照以下时间自动运行：

| 任务 | [运行时间（北京时间）可修改](#modify-time) | 工作流文件 |
| :--- | :--- | :--- |
| 每日签到（按 `SIGN_GAMES` 选择） | 每天 03:25 | `daily-sign.yml` |
| Bilibili 登录 | 每天 03:00 | `bilibili-login.yml` |

你也可以在 Actions 页面手动触发任意工作流。

</details>

<a id="cred"></a>
### 2. 凭证获取

各平台凭证的获取方法汇总（与运行方式无关，本地运行用户同样按此获取后填入 `api.txt`）。

<a id="cred-skland"></a>
#### 2.1 森空岛凭证获取

**网页扫码（推荐）**

[![一键获取 Token](https://img.shields.io/badge/点击扫码-获取Token-00c3cc?style=for-the-badge)](https://zyhqwq.github.io/sign-myself/skland.html)

1.  **扫码**：点击上方按钮打开网页，用**森空岛 App** 扫描页面上的二维码，在手机上确认登录。
2.  **复制 Token**：页面会生成可复制的 Token，多账号可连续扫码添加（自动用英文逗号连接），填入 Secret 或 `api.txt` 即可。

> [!NOTE]
> 页面默认使用仓库提供的公共代理 `proxy.zyhh.qzz.io` 转发接口请求。Token 只在你的浏览器内组装，代理无日志无存储；如需完全自托管，可按 [`docs/proxy.js`](docs/proxy.js) 顶部说明部署自己的 Cloudflare Worker，并在页面「代理设置」中替换地址。

<details>
<summary><b>书签栏一键获取（无需扫码）</b></summary>

1.  **添加书签**：打开[同一页面](https://zyhqwq.github.io/sign-myself/skland.html)，把「方式二」中的「📋 获取森空岛Token」按钮按住拖到浏览器书签栏（书签栏没显示可按 `Ctrl+Shift+B`）。
2.  **一键获取**：在已登录 [森空岛网页版](https://www.skland.com/) 的标签页里点击该书签，Token 会自动弹出并复制。多账号用无痕窗口分别获取后用英文逗号连接。

> [!NOTE]
> 书签方式全程在你的浏览器内完成、不经过任何服务器：它只会在你已登录的森空岛/鹰角通行证页面里读取 Token 并复制到剪贴板。

</details>

<details>
<summary><b>手动获取</b></summary>

1.  在电脑浏览器中登录 [森空岛](https://www.skland.com/)。
2.  登录后进入 https://web-api.skland.com/account/info/hg
3.  返回内容格式如下：`{"code":0,"data":{"content":"****"},"msg":"..."}`
4.  找到 `{"content":"****"}`，复制 `****` 中的内容，即为 Token。

</details>

<a id="cred-mihoyo"></a>
#### 2.2 米游社Cookie获取

**网页扫码（推荐）**

[![扫码获取 Cookie](https://img.shields.io/badge/点击扫码-获取Cookie-00c3cc?style=for-the-badge)](https://zyhqwq.github.io/sign-myself/)

1.  **扫码**：点击上方按钮打开网页，用**米游社 App** 扫描页面上的二维码，在手机上确认登录。
2.  **复制 Cookie**：页面会生成可复制的 Cookie，多账号可连续扫码添加（自动用英文逗号连接）。

> [!NOTE]
> 页面默认使用仓库提供的公共代理 `proxy.zyhh.qzz.io` 转发接口请求。Cookie 只在你的浏览器内组装，代理无日志无存储；如需完全自托管，可按 [`docs/proxy.js`](docs/proxy.js) 顶部说明部署自己的 Cloudflare Worker，并在页面底部「代理设置」中替换地址。

<details>
<summary><b>本地脚本</b></summary>

```bash
pip install -r requirements.txt
python mihoyo/miyoushe_qr_login.py
```

终端会打印二维码，米游社 App 扫码确认后输出 Cookie。

</details>

> [!NOTE]
> Cookie 中的 `stoken` 长期有效，只有在修改密码、退出登录等情况下才会失效。失效后重新运行扫码工具获取即可。

<a id="cred-bilibili"></a>
#### 2.3 Bilibili Cookie 获取

**网页扫码（推荐）**

[![扫码获取 Cookie](https://img.shields.io/badge/点击扫码-获取Cookie-fb7299?style=for-the-badge)](https://zyhqwq.github.io/sign-myself/bilibili.html)

1.  **扫码**：点击上方按钮打开网页，用**哔哩哔哩 App** 扫描页面上的二维码，在手机上确认登录。
2.  **复制 Cookie**：页面会分别生成 `SESSDATA`、`DedeUserID`、`bili_jct` 三个值，逐个复制填入对应 Secret；多账号可连续扫码添加（各字段自动用英文逗号连接、按位置一一对应）。

> [!NOTE]
> 与米游社/森空岛页共用同一代理（默认 `proxy.zyhh.qzz.io`），自托管方法相同。Cookie 只在你的浏览器内解析，代理无日志无存储。

**手动获取**

<details>
<summary><b>不用网页？从浏览器手动获取</b></summary>

1.  在电脑浏览器中登录 [Bilibili](https://www.bilibili.com/)。
2.  按 `F12` 打开开发者工具，进入 `Application` -> `Cookies` -> `https://www.bilibili.com`。
3.  找到以下三个值并复制：
    *   `SESSDATA`（必需）
    *   `DedeUserID`（必需）
    *   `bili_jct`（可选）

</details>

<a id="step-3-games"></a>
### 3. 选择要签到的游戏（可选）

通过 `SIGN_GAMES` 控制每天运行哪些任务（英文逗号分隔序号，不配置则默认全部 `1,2,3,4,5`）：

- **本地运行用户**：编辑 `api.txt` 中的 `SIGN_GAMES=` 行，去掉行首 `#` 并填入序号
- **GitHub Actions 用户**：添加 Secret `SIGN_GAMES`

| 序号 | 游戏 | 所属平台 | 对应变量 |
| :---: | :--- | :--- | :--- |
| `1` | 明日方舟 | 森空岛 | `SKLAND_TOKEN` |
| `2` | 终末地 | 森空岛 | `SKLAND_TOKEN` |
| `3` | 原神 | 米游社 | `MIYOUSHE_COOKIE` |
| `4` | 崩坏:星穹铁道 | 米游社 | `MIYOUSHE_COOKIE` |
| `5` | 绝区零 | 米游社 | `MIYOUSHE_COOKIE` |

例如只想签明日方舟和原神：
- 本地运行：把 `api.txt` 中该行改为 `SIGN_GAMES=1,3`
- GitHub Actions：添加 Secret `SIGN_GAMES`，值为 `1,3`

<a id="notify-config"></a>
## 配置通知（可选）

如果你希望签到后收到通知，可以按需配置以下通知渠道，所有脚本共享同一套通知配置：

- **本地运行用户**：把对应的变量名和值写入项目根目录的 `api.txt`（配置向导中也可直接选择配置）。
- **GitHub Actions 用户**：进入仓库 `Settings` -> `Secrets and variables` -> `Actions` -> `New repository secret`，按下方「名称 / 值」对应添加 Secret。

**国外平台**

| 通知平台 | 名称 | 值 | 已测试 |
| :--- | :--- | :--- | :--- |
| [**Discord**](https://discord.com/) | `DISCORD_WEBHOOK_URL` | 填写 Discord 频道设置的 Webhook 地址。 | ✓ |
| [**Telegram**](https://telegram.org/) | `TELEGRAM_BOT_TOKEN` 和 `TELEGRAM_CHAT_ID` | 需要通过 `@BotFather` 创建机器人来获取 Token 和 Chat ID。[详见下方步骤。](#telegram-steps) | ✓ |

**国内平台**

| 通知平台 | 名称 | 值 | 已测试 |
| :--- | :--- | :--- | :--- |
| [**企业微信**](https://work.weixin.qq.com/) | `WECHAT_WEBHOOK_URL` | 填写企业微信群机器人的 Webhook 地址。 | ✓ |
| [**飞书**](https://www.feishu.cn/) | `FEISHU_WEBHOOK_URL` | 填写飞书群自定义机器人的 Webhook 地址。 | ✓ |
| [**钉钉**](https://www.dingtalk.com/) | `DINGTALK_WEBHOOK_URL`<br>`DINGTALK_SECRET`（可选） | 填写钉钉群自定义机器人的 Webhook 地址。若安全设置选择"加签"，需额外填写 `DINGTALK_SECRET`。<br>若选择"自定义关键词"，建议设置 `通知`（所有消息均包含此关键词）。[详见下方步骤。](#dingtalk-steps) | ✓ |
| [**Server酱**](https://sct.ftqq.com/) | `SERVER_CHAN_KEY` | 在 Server酱官网申请 SendKey。<br>关注 Server酱官方微信服务号，可推送到个人微信，每天免费 5 条消息。 | ✓ |
| [**Bark**](https://github.com/Finb/Bark) | `BARK_URL` | 填写 Bark App 为你生成的推送 URL。 | 正在测试 |
| [**PushPlus**](https://www.pushplus.plus/) | `PUSHPLUS_TOKEN` | 在 PushPlus 官网申请 Token。关注 PushPlus 微信服务号后，通知会推送到个人微信。<br>**注意：** PushPlus 于 2024 年 8 月 1 日起实行网站实名制，需完成实名认证后才能发送消息。认证时手机号与身份证信息须保持一致（需支付认证费用）。 | 正在测试 |

**通用**

| 通知平台 | 名称 | 值 |
| :--- | :--- | :--- |
| **邮件 (SMTP)** | `SMTP_HOST`<br>`SMTP_PORT`<br>`SMTP_USER`<br>`SMTP_PASS`<br>`SMTP_TO` | `SMTP_HOST`/`SMTP_PORT` 为邮箱服务商的 SMTP 地址与端口（`465` 为 SSL，`587` 为 STARTTLS）。`SMTP_USER` 为发件邮箱，`SMTP_PASS` 填授权码（QQ、163 等需先在邮箱设置中开启 SMTP 并生成授权码），`SMTP_TO` 为收件邮箱，多个用英文逗号分隔。 |
| **自定义 Webhook** | `CUSTOM_WEBHOOK_URL` | 填写任意支持 POST JSON 的 Webhook 地址，如 `https://example.com/webhook`。脚本会发送包含 `title`、`message`、`timestamp` 等字段的 JSON 请求体。 |

<a id="telegram-steps"></a>
### Telegram 机器人创建步骤

<details>
<summary><b>点击展开详细步骤</b></summary>

1.  **创建机器人，获取 Token**
    - 在 Telegram 搜索 `@BotFather`，打开对话
    - 发送 `/newbot`
    - 按提示输入机器人名称（显示名）和用户名（必须以 `bot` 结尾，如 `my_sign_notify_bot`）
    - 创建成功后会返回 Token，格式如：`5892341765:ABCxY9zW8vU7tS6rQ5pO4nM3lK2jI1hG0f`

2.  **获取 Chat ID**
    - 搜索 `@userinfobot`，打开对话
    - 发送 `/start`，它会回复你的 Chat ID（一串数字，如 `123456789`）

3.  **先给你的机器人发一条消息**
    - 搜索你刚创建的机器人用户名，打开对话
    - 发送任意消息（必须发一条，否则机器人没权限给你发消息）

4.  **添加 Secret**
    - `TELEGRAM_BOT_TOKEN` → 第 1 步的 Token
    - `TELEGRAM_CHAT_ID` → 第 2 步的 Chat ID（数字）

</details>

<a id="dingtalk-steps"></a>
### 钉钉机器人创建步骤

<details>
<summary><b>点击展开详细步骤</b></summary>

1.  **创建机器人**
    - 登录钉钉客户端，进入想接收通知的**群聊**
    - 点击右上角 **群设置** → **机器人** → **添加机器人**
    - 选择 **自定义（通过 Webhook 接入自定义服务）**，点击 **添加**
    - 配置机器人信息：
      - **机器人名字**：填写名称（如"签到通知"）
      - **安全设置**（二选一）：
        - **自定义关键词**：填写 `通知`（所有消息均包含此关键词）
        - **加签**：使用签名加密，安全性更高。选择后会生成一个 `SEC` 开头的密钥，复制保存
    - 勾选服务条款，点击 **完成**
    - 复制生成的 Webhook 地址，格式如：
      ```
      https://oapi.dingtalk.com/robot/send?access_token=xxxxxxxxxxxxxxxx
      ```

2.  **添加 Secret**
    - 到 GitHub 仓库 `Settings` → `Secrets and variables` → `Actions` → `New repository secret`
    - 添加 Webhook 地址：
      - Name: `DINGTALK_WEBHOOK_URL`
      - Value: 粘贴上面的 Webhook 地址
    - 如果安全设置选择了"加签"，还需额外添加：
      - Name: `DINGTALK_SECRET`
      - Value: 粘贴 `SEC` 开头的密钥

</details>

> [!NOTE]
> 代码会自动检测是否配置了 `DINGTALK_SECRET`，如果配置了则使用加签模式，否则使用普通模式（配合自定义关键词）。所有钉钉通知消息格式为 `【通知】标题 + 正文`，因此设置关键词 `通知` 即可匹配所有消息。详细文档参考 [钉钉自定义机器人接入](https://open.dingtalk.com/document/orgapp/custom-robots-send-group-messages)。

<a id="faq"></a>
## 常见问题

<details>
<summary><b>Token 会过期吗？需要经常换吗？</b></summary>

通常不会。`SKLAND_TOKEN` 有效期很长，一般只有在你长时间未使用或修改密码后才会失效。如果脚本运行失败并提示 Token 错误，再按上述步骤重新获取一次即可。B 站的 `SESSDATA` 同理，过期后重新从浏览器获取即可。米游社的 `MIYOUSHE_COOKIE` 中的 `stoken` 同样长期有效，失效后（签到通知提示 Cookie 已失效）重新运行扫码工具获取即可。

</details>

<details>
<summary><b>签到失败或收不到通知怎么办？</b></summary>

请按以下步骤排查：
1.  查看签到日志或 Actions 运行日志，通常会有明确的错误信息。
2.  检查你配置的凭证和通知地址是否填写正确，特别是注意不要有多余的空格。
3.  确认你配置的通知渠道（如 Telegram Bot）本身工作正常。

</details>

<a id="modify-time"></a>
<details>
<summary><b>可以修改签到时间吗？</b></summary>

可以。本地运行直接修改 crontab 里的执行时间即可；GitHub Actions 则编辑 `.github/workflows/` 下对应工作流文件，找到 `cron` 配置行。cron 使用 UTC 时间，北京时间 = UTC + 8，所以 UTC = 北京时间 - 8。例如北京时间 13:00 = UTC 05:00，写作 `cron: '0 5 * * *'`。推荐使用功能更成熟的 [crontab.guru](https://crontab.guru/) 在线生成和验证 cron 表达式（[https://cron.zyhh.qzz.io/](https://cron.zyhh.qzz.io/) 为自制的cron生成网页也许可能大概也能用）。

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

</details>

<details>
<summary><b>终末地签到提示"未经授权"怎么办？</b></summary>

请确认你已在森空岛 App 或网页端绑定了终末地游戏角色。未绑定角色的账号无法签到。

</details>

<a id="files"></a>
## 文件说明

```
├── sign_all.py                   # 每日签到统一入口（按 SIGN_GAMES 序号调度）
├── bilibili_login.py             # Bilibili 每日登录脚本
├── test_notify.py                # 通知渠道测试脚本
├── notify.py                     # 共享通知模块（含统一通知格式）
├── requirements.txt              # Python 依赖列表
├── skland/                       # 森空岛平台
│   ├── arknight_github.py        # 明日方舟签到脚本
│   ├── endfield_github.py        # 终末地签到脚本
│   └── skland_common.py          # 公共模块（加密、签名、登录）
├── mihoyo/                       # 米游社平台
│   ├── miyoushe_sign.py          # 游戏签到脚本（原神/星铁/绝区零）
│   ├── miyoushe_qr_login.py      # 扫码登录工具（本地运行获取 Cookie）
│   └── miyoushe_debug.py         # Cookie 诊断工具
├── docs/
│   ├── index.html                # 网页版扫码获取米游社 Cookie 页面（GitHub Pages）
│   ├── skland.html               # 扫码 / 书签栏获取森空岛 Token 页面（GitHub Pages）
│   ├── bilibili.html             # 网页版扫码获取 Bilibili Cookie 页面（GitHub Pages）
│   └── proxy.js                  # Cloudflare Worker CORS 代理（配合网页使用）
└── .github/workflows/
    ├── daily-sign.yml            # 每日签到工作流（森空岛 + 米游社，按序号选择）
    ├── bilibili-login.yml        # Bilibili 登录工作流
    ├── miyoushe-debug.yml        # 米游社 Cookie 诊断工作流（手动触发）
    └── test-notify.yml           # 通知测试工作流
```

<a id="credits"></a>
## 致谢与参考

- 森空岛签到逻辑参考了 [skyland-auto-sign](https://gitee.com/FancyCabbage/skyland-auto-sign)
- 终末地签到逻辑参考了 [nonebot-plugin-skland](https://github.com/FrostN0v0/nonebot-plugin-skland)
- Bilibili 每日登录思路参考了 [BiliBiliToolPro](https://github.com/RayWangQvQ/BiliBiliToolPro)、[BILIBILI-HELPER](https://gitee.com/iamhoney/BILIBILI-HELPER)（原作者仓库已删除，此为镜像）
- 米游社扫码登录流程参考了 [TRSS-Plugin](https://github.com/TimeRainStarSky/TRSS-Plugin)
- 米游社游戏签到接口、请求头与 act_id 参考了 [MihoyoBBSTools](https://github.com/Womsxd/MihoyoBBSTools)、[astrbot_plugin_miyoqian](https://github.com/QzKevin/astrbot_plugin_miyoqian)、[sign-task](https://github.com/starudream/sign-task)
- 米哈游 API 盐值与签名算法参考了 [mihoyo-api-collect](https://github.com/UIGF-org/mihoyo-api-collect)

感谢以上项目的作者们的无私付出。

请勿将本脚本用于任何商业或盈利目的。

<a id="ending"></a>
## 最后

如果觉得这个项目有帮助，欢迎给个 Star。祝你游戏愉快！
