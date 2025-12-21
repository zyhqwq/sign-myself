# 森空岛自动签到脚本 (GitHub Actions 版本)

自动执行森空岛签到任务，支持多账号和多种通知方式。

## 功能特性

- ✅ 自动签到森空岛账号
- ✅ 支持多个账号同时签到
- ✅ 动态设备ID生成（防止被封）
- ✅ 数美设备ID支持
- ✅ 企业微信通知
- ✅ GitHub Actions 摘要
- ✅ 定时执行（每天 UTC 0:10，北京时间 8:10）
- ✅ 支持手动触发

## 使用方法

### 1. Fork 本仓库

点击右上角的 Fork 按钮，将仓库复制到自己的账户下。

### 2. 配置 Secrets

在仓库的 Settings > Secrets and variables > Actions 中添加以下 Secrets：

| Secret 名称 | 说明 | 必填 |
|------------|------|------|
| `TOKEN` | 森空岛token，多个用逗号分隔 | 是 |
| `WECHAT_WEBHOOK_URL` | 企业微信Webhook地址（可选） | 否 |
| `DEVICE_MODE` | 设备ID模式：smart, random, shumei（可选） | 否 |
| `FIXED_DEVICE_ID` | 固定设备ID（可选） | 否 |

### 3. 获取森空岛 Token

1. 登录森空岛网页版
2. 打开开发者工具 (F12)
3. 访问：https://web-api.skland.com/account/info/hg
4. 复制返回的 JSON 中的 `content` 字段值

### 4. 启用 Actions

Actions 会自动启用。您也可以手动触发：
1. 进入 Actions 标签页
2. 选择 "Skland Auto Signin"
3. 点击 "Run workflow"

## 配置说明

### 设备ID模式

- `smart`: 智能模式（默认），70%随机ID，30%数美ID
- `random`: 只使用随机ID
- `shumei`: 只使用数美ID
- 固定ID：设置 `FIXED_DEVICE_ID` 环境变量

### 定时任务

默认每天 UTC 时间 0:10（北京时间 8:10）执行。修改 `.github/workflows/skland-signin.yml` 中的 cron 表达式调整时间。

## 常见问题

### Q: 如何添加多个账号？
A: 在 `TOKEN` 中用逗号分隔多个 token。

### Q: 签到失败了怎么办？
A: 检查 Actions 日志，通常是因为 token 失效或网络问题。

### Q: 可以修改签到时间吗？
A: 可以，编辑 `.github/workflows/skland-signin.yml` 中的 `cron` 表达式。

## 免责声明

本脚本仅供学习交流使用，请勿用于商业用途。使用本脚本造成的任何问题，作者不承担责任。