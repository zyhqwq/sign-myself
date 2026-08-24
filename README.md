# sign-myself

> **⚠️ 免责声明（请务必阅读）**
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
> **关于 GitHub Actions**：仓库内的工作流文件仅作参考示例。作者**不支持也不推荐**使用 GitHub Actions 来每日自动执行——Fork 仓库的 Actions 用量会归属到上游存储库，滥用可能导致上游仓库被停用。与 Actions 运行相关的 Issue 恕不处理。

一个用于自动签到的工具，支持多账号与多种通知渠道。

<a id="main-features"></a>
## 目录

- [主要功能](#main-features)
- [使用方法](#usage)
  - [1. Fork 本仓库](#step-1-fork)
  - [2. 配置森空岛 Token](#step-2-skland)
  - [3. 配置 Bilibili Cookie](#step-3-bilibili)
  - [4. 配置米游社 Cookie](#step-4-mihoyo)
  - [5. 选择要签到的游戏](#step-5-games)
  - [6.1 方式一：Linux 本地 / 服务器运行](#step-6-linux)
  - [6.2 方式二：GitHub Actions](#step-6-actions)
- [配置通知（可选）](#notify-config)
  - [Telegram 机器人创建步骤](#telegram-steps)
  - [钉钉机器人创建步骤](#dingtalk-steps)
- [常见问题](#faq)
- [文件说明](#files)
- [致谢与参考](#credits)

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

<a id="step-1-fork"></a>
### 1. Fork 本仓库
点击本页右上角的 `Fork` 按钮，将这个项目复制到你自己的 GitHub 账号下。

<a id="step-2-skland"></a>
### 2. 配置森空岛 Token（明日方舟 + 终末地）

你需要获取并配置你的 `SKLAND_TOKEN`，明日方舟和终末地签到共用此 Token。

1.  **获取 Token**:
    *   在电脑浏览器中登录 [森空岛](https://www.skland.com/)。
    *   登录后进入 https://web-api.skland.com/account/info/hg
    *   格式如下：`{"code":0,"data":{"content":"****"},"msg":"..."}`
    *   找到 `{"content":"****"}`，复制 `****` 中的内容，并保存。

2.  **添加 Secret**:
    *   进入你 Fork 的仓库，点击 `Settings` -> `Secrets and variables` -> `Actions`。
    *   点击 `New repository secret`，添加以下 Secret：

    | Name | Secret | 说明 |
    | :--- | :--- | :--- |
    | `SKLAND_TOKEN` | 森空岛 Token | 明日方舟和终末地签到共用，多账号用英文逗号 `,` 分隔 |

<a id="step-3-bilibili"></a>
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

    | Name | Secret | 说明 |
    | :--- | :--- | :--- |
    | `BILI_SESSDATA` | `SESSDATA` | B 站登录凭证（必需） |
    | `BILI_DEDEUSERID` | `DedeUserID` | B 站用户 ID（必需） |
    | `BILI_JCT` | `bili_jct` | CSRF Token（可选） |

    支持多账号：多个账号的值用英文逗号 `,` 分隔填入同一个 Secret，按位置一一对应。

<a id="step-4-mihoyo"></a>
### 4. 配置米游社 Cookie

米游社签到需要 `MIYOUSHE_COOKIE`，用于自动完成原神、崩坏:星穹铁道、绝区零的每日签到（领原石、燃料、丁尼等）。脚本会自动检测账号绑定的角色，只签有角色的游戏。

> 注：米游社社区板块签到（米游币）已被官方限制第三方调用，故本项目只做游戏签到。

与上面手动抓 Cookie 不同，Cookie 通过扫码工具获取（Actions 里不执行登录），推荐网页版：

#### 方式一：网页扫码（推荐）

[![扫码获取 Cookie](https://img.shields.io/badge/点击扫码-获取Cookie-00c3cc?style=for-the-badge)](https://zyhqwq.github.io/sign-myself/)

1.  **扫码**：点击上方按钮打开网页，用**米游社 App** 扫描页面上的二维码，在手机上确认登录。
2.  **复制 Cookie**：页面会生成可复制的 Cookie，多账号可连续扫码添加（自动用英文逗号连接）。
3.  **添加 Secret**：复制整段内容，添加到 Secret `MIYOUSHE_COOKIE`。

> 页面默认使用仓库提供的公共代理 `mhy.zyhh.qzz.io` 转发接口请求。Cookie 只在你的浏览器内组装，代理无日志无存储；如需完全自托管，可按 [`docs/proxy.js`](docs/proxy.js) 顶部说明部署自己的 Cloudflare Worker，并在页面底部「代理设置」中替换地址。

#### 方式二：本地脚本

```bash
pip install -r requirements.txt
python mihoyo/miyoushe_qr_login.py
```

终端会打印二维码，米游社 App 扫码确认后输出 Cookie，同样填入 Secret 即可。

| Name | Secret | 说明 |
| :--- | :--- | :--- |
| `MIYOUSHE_COOKIE` | 扫码得到的完整 Cookie | 含 `stoken` 等字段，多账号自动以英文逗号分隔 |

> Cookie 中的 `stoken` 长期有效，只有在修改密码、退出登录等情况下才会失效。失效后重新运行扫码工具获取即可。

<a id="step-5-games"></a>
### 5. 选择要签到的游戏（可选）

通过 Secret `SIGN_GAMES` 控制每天运行哪些任务（英文逗号分隔序号，不配置则默认全部 `1,2,3,4,5`）：

| 序号 | 游戏 | 所属平台 | 依赖的 Secret |
| :---: | :--- | :--- | :--- |
| `1` | 明日方舟 | 森空岛 | `SKLAND_TOKEN` |
| `2` | 终末地 | 森空岛 | `SKLAND_TOKEN` |
| `3` | 原神 | 米游社 | `MIYOUSHE_COOKIE` |
| `4` | 崩坏:星穹铁道 | 米游社 | `MIYOUSHE_COOKIE` |
| `5` | 绝区零 | 米游社 | `MIYOUSHE_COOKIE` |

例如只想签明日方舟和原神：添加 Secret `SIGN_GAMES`，值为 `1,3`。

<a id="step-6-actions"></a>
<a id="step-6-linux"></a>
<a id="step-6-actions"></a>
### 6. 运行方式

#### 6.1 方式一：Linux / 服务器运行（推荐）

全程只需 4 条命令，凭证保存在你自己电脑上，不需要懂编程。

**第 1 步：下载项目**

```bash
git clone https://github.com/zyhqwq/sign-myself.git
cd sign-myself
```

**第 2 步：第一次运行（自动生成配置文件）**

```bash
bash run.sh
```

运行后会提示"已在当前目录生成配置文件 api.txt"。

**第 3 步：填写 api.txt**

用记事本或任意编辑器打开 `api.txt`，把 `=` 后面改成自己的值，并删掉行首的 `#` 号。例如：

```text
SKLAND_TOKEN=你的森空岛Token
MIYOUSHE_COOKIE=你的米游社Cookie
SIGN_GAMES=1,2,3,4,5
WECHAT_WEBHOOK_URL=你的企业微信机器人地址
```

> - 每一项的作用文件里都有中文注释说明，不需要的保持 `#` 注释状态即可
> - 多账号用英文逗号分隔；获取方法见上文第 2、4 节

**第 4 步：再次运行测试**

```bash
bash run.sh
```

看到各游戏签到结果即为成功。

**第 5 步：加入定时任务（每天北京时间凌晨 3:25 自动签到）**

```bash
crontab -e
```

添加一行（换成你自己的真实路径，[可修改时间](#modify-time)）：

```text
25 3 * * * cd /home/你的用户名/sign-myself && bash run.sh >> sign.log 2>&1
```

保存退出即可，之后每天自动签到，结果可在 `sign.log` 查看。

> 💡 小贴士：
>
> - 全程**不需要 root 权限**；pip 没有写入权限时会自动改用 `--user` 安装到你的用户目录
> - 若系统还没装 Python：`sudo apt install python3 python3-pip`（仅这一步需要管理员）
> - 系统时区不是北京时间时先执行 `timedatectl set-timezone Asia/Shanghai`
> - 建议把分钟数改成随机值，避免长期固定整点请求

#### 6.2 方式二：GitHub Actions（仅供参考，不推荐）

> ⚠️ 再次提示：仓库内的工作流文件**仅作参考示例**，作者**不支持也不推荐**使用 GitHub Actions 来每日自动执行，相关风险请自行评估（详见顶部免责声明）。

*   进入你仓库的 `Actions` 标签页。
*   点击 `I understand my workflows, go ahead and enable them`。
*   完成！各脚本将按照以下时间自动运行：

| 任务 | [运行时间（北京时间）可修改](#modify-time) | 工作流文件 |
| :--- | :--- | :--- |
| 每日签到（按 `SIGN_GAMES` 选择） | 每天 03:25 | `daily-sign.yml` |
| Bilibili 登录 | 每天 03:00 | `bilibili-login.yml` |

你也可以在 Actions 页面手动触发任意工作流。

<a id="notify-config"></a>
## 配置通知（可选）

如果你希望签到后收到通知，可以按需添加以下 Secret。进入仓库 `Settings` -> `Secrets and variables` -> `Actions` -> `New repository secret` 添加。所有脚本共享同一套通知配置。

**国外平台**

| 通知平台 | Name | Secret | 已测试 |
| :--- | :--- | :--- | :--- |
| [**Discord**](https://discord.com/) | `DISCORD_WEBHOOK_URL` | 填写 Discord 频道设置的 Webhook 地址。 | ✓ |
| [**Telegram**](https://telegram.org/) | `TELEGRAM_BOT_TOKEN` 和 `TELEGRAM_CHAT_ID` | 需要通过 `@BotFather` 创建机器人来获取 Token 和 Chat ID。[详见下方步骤。](#telegram-steps) | ✓ |

**国内平台**

| 通知平台 | Name | Secret | 已测试 |
| :--- | :--- | :--- | :--- |
| [**企业微信**](https://work.weixin.qq.com/) | `WECHAT_WEBHOOK_URL` | 填写企业微信群机器人的 Webhook 地址。 | ✓ |
| [**飞书**](https://www.feishu.cn/) | `FEISHU_WEBHOOK_URL` | 填写飞书群自定义机器人的 Webhook 地址。 | ✓ |
| [**钉钉**](https://www.dingtalk.com/) | `DINGTALK_WEBHOOK_URL`<br>`DINGTALK_SECRET`（可选） | 填写钉钉群自定义机器人的 Webhook 地址。若安全设置选择"加签"，需额外填写 `DINGTALK_SECRET`。<br>若选择"自定义关键词"，建议设置 `通知`（所有消息均包含此关键词）。[详见下方步骤。](#dingtalk-steps) | ✓ |
| [**Server酱**](https://sct.ftqq.com/) | `SERVER_CHAN_KEY` | 在 Server酱官网申请 SendKey。<br>关注 Server酱官方微信服务号，可推送到个人微信，每天免费 5 条消息。 | ✓ |
| [**Bark**](https://github.com/Finb/Bark) | `BARK_URL` | 填写 Bark App 为你生成的推送 URL。 | 正在测试 |
| [**PushPlus**](https://www.pushplus.plus/) | `PUSHPLUS_TOKEN` | 在 PushPlus 官网申请 Token。关注 PushPlus 微信服务号后，通知会推送到个人微信。<br>**注意：** PushPlus 于 2024 年 8 月 1 日起实行网站实名制，需完成实名认证后才能发送消息。认证时手机号与身份证信息须保持一致（需支付认证费用）。 | 正在测试 |

**通用**

| 通知平台 | Name | Secret |
| :--- | :--- | :--- |
| **自定义 Webhook** | `CUSTOM_WEBHOOK_URL` | 填写任意支持 POST JSON 的 Webhook 地址，如 `https://example.com/webhook`。脚本会发送包含 `title`、`message`、`timestamp` 等字段的 JSON 请求体。 |

<a id="telegram-steps"></a>
### Telegram 机器人创建步骤

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

<a id="dingtalk-steps"></a>
### 钉钉机器人创建步骤

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

> **说明**：代码会自动检测是否配置了 `DINGTALK_SECRET`，如果配置了则使用加签模式，否则使用普通模式（配合自定义关键词）。所有钉钉通知消息格式为 `【通知】标题 + 正文`，因此设置关键词 `通知` 即可匹配所有消息。详细文档参考 [钉钉自定义机器人接入](https://open.dingtalk.com/document/orgapp/custom-robots-send-group-messages)。

<a id="faq"></a>
## 常见问题

**Q：Token 会过期吗？需要经常换吗？**

**A：** 通常不会。`SKLAND_TOKEN` 有效期很长，一般只有在你长时间未使用或修改密码后才会失效。如果脚本运行失败并提示 Token 错误，再按上述步骤重新获取一次即可。B 站的 `SESSDATA` 同理，过期后重新从浏览器获取即可。米游社的 `MIYOUSHE_COOKIE` 中的 `stoken` 同样长期有效，失效后（签到通知提示 Cookie 已失效）重新运行扫码工具获取即可。

**Q：签到失败或收不到通知怎么办？**

**A：** 请按以下步骤排查：
1.  去仓库的 `Actions` 标签页，查看最近一次运行的详细日志，通常会有明确的错误信息。
2.  检查你配置的 Secret（Token 和通知地址）是否填写正确，特别是注意不要有多余的空格。
3.  确认你配置的通知渠道（如 Telegram Bot）本身工作正常。

<a id="modify-time"></a>

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
│   ├── index.html                # 网页版扫码获取 Cookie 页面（GitHub Pages）
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
