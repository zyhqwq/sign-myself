# 森空岛签到 GitHub Actions 版

自动在 GitHub Actions 上运行森空岛每日签到。

## 配置步骤

### 1. Fork 本仓库

点击右上角的 Fork 按钮。

### 2. 配置 Secrets

在 Fork 的仓库中：
1. 进入 Settings → Secrets and variables → Actions
2. 点击 New repository secret
3. 添加以下 Secrets：

#### SKLAND_TOKEN
你的森空岛 token，可以设置多个（用逗号分隔）。

获取 token 的方法：
1. 登录森空岛官网
2. 按 F12 打开开发者工具
3. 进入 Application → Local Storage → https://web-api.skland.com
4. 找到 `SK_OFFICIAL_UID` 和 `SK_OFFICIAL_TOKEN`，格式如下：
{"code":0,"message":"OK","data":{"content":"你的token","uid":"你的uid"}}


#### WECHAT_WEBHOOK_URL（可选）
企业微信 Webhook URL，用于接收签到通知。

### 3. 启用 Actions

默认情况下 Actions 是启用的。如需手动启用：
1. 进入 Actions 标签页
2. 点击绿色按钮启用

### 4. 运行签到

- **自动运行**：每天北京时间早上6点自动运行
- **手动运行**：在 Actions 页面点击 "Run workflow"

## 文件说明

- `skland_github.py` - 主程序
- `requirements.txt` - Python 依赖
- `.github/workflows/skland-sign.yml` - GitHub Actions 工作流
- `token.json` - 自动生成的 token 缓存文件（可选）

## 多账号支持

在 Secrets 中设置多个 token，用英文逗号分隔：
token1,token2,token3

## 注意事项

1. GitHub Actions 有免费额度限制，每月 2000 分钟
2. 建议只在需要时启用
3. token 可能过期，需要定期更新
4. 代码仅供参考，使用风险自负