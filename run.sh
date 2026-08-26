#!/bin/bash
# ============================================================
# 每日签到启动脚本（Linux / 服务器）
# 用法：bash run.sh
# 首次运行会在当前目录生成 api.txt，编辑填入参数后再运行一次即可
# ============================================================

cd "$(dirname "$0")" || exit 1

# ---------- 1. 首次运行：自动生成配置文件 ----------
if [ ! -f api.txt ]; then
cat > api.txt <<'EOF'
# ============================================
# 签到参数配置
# 把 = 后面改成自己的值，并删除行首的 # 号
# 不用的功能保持注释状态即可
# ============================================

# ---- 游戏凭证 ----

# 森空岛 Token（序号1明日方舟、2终末地需要），多账号用英文逗号 , 分隔
# 获取方法见 README 第 2.1 节
#SKLAND_TOKEN=

# 米游社 Cookie（序号3原神、4星铁、5绝区零需要），由扫码工具获取，多账号用英文逗号 , 分隔
# 获取方法见 README 第 2.2 节（运行 mihoyo/miyoushe_qr_login.py 扫码）
#MIYOUSHE_COOKIE=

# ---- 签到选择 ----

# 要签到的游戏序号：1明日方舟 2终末地 3原神 4星铁 5绝区零
# 英文逗号分隔；留空或保持注释 = 全部签到
#SIGN_GAMES=1,2,3,4,5

# ---- 通知渠道（可选，不配就不通知）----

# 企业微信群机器人 Webhook 地址
#WECHAT_WEBHOOK_URL=

# 钉钉群机器人 Webhook 地址
#DINGTALK_WEBHOOK_URL=

# 飞书群机器人 Webhook 地址
#FEISHU_WEBHOOK_URL=

# Telegram 机器人（两个都要填）
#TELEGRAM_BOT_TOKEN=
#TELEGRAM_CHAT_ID=

# Discord 频道 Webhook 地址
#DISCORD_WEBHOOK_URL=

# Server酱 SendKey（推送到个人微信）
#SERVER_CHAN_KEY=

# 邮件通知（SMTP，465 为 SSL，587 为 STARTTLS；PASS 填授权码不是登录密码）
#SMTP_HOST=
#SMTP_PORT=465
#SMTP_USER=
#SMTP_PASS=
#SMTP_TO=
EOF

echo ""
echo "=============================================="
echo " 已在当前目录生成配置文件 api.txt"
echo " 请用编辑器打开 api.txt，按里面的注释说明"
echo " 填入你的参数（删除行首的 # 号），保存后"
echo " 再重新运行: bash run.sh"
echo "=============================================="
exit 1
fi

# ---------- 2. 导入配置 ----------
# 逐行解析而非 source：Cookie 等值可能含分号/引号，
# 直接 source 会被 shell 当作命令分隔符截断，导致"Cookie 已失效"
while IFS= read -r line || [ -n "$line" ]; do
    line=${line%$'\r'}
    case "$line" in ''|\#*) continue ;; esac
    case "$line" in *=*) ;; *) continue ;; esac
    _key=${line%%=*}
    _val=${line#*=}
    # 去掉成对的单引号或双引号（兼容手工加引号的写法）
    case "$_val" in
        \'*\') _val=${_val#\'}; _val=${_val%\'} ;;
        \"*\") _val=${_val#\"}; _val=${_val%\"} ;;
    esac
    export "$_key=$_val"
done < ./api.txt
unset _key _val line

# ---------- 3. 依赖检查（缺依赖自动安装）----------
if ! python3 -c "import requests, cryptography, qrcode" 2>/dev/null; then
    echo "首次运行：正在检查/安装依赖..."

    # 缺 pip 时先补齐（Debian/Ubuntu 精简环境常见）
    if ! python3 -m pip --version >/dev/null 2>&1 && ! command -v pip3 >/dev/null 2>&1; then
        SUDO=""; [ "$(id -u)" != "0" ] && command -v sudo >/dev/null 2>&1 && SUDO="sudo"
        if command -v apt-get >/dev/null 2>&1; then
            $SUDO apt-get update -qq 2>/dev/null
            $SUDO apt-get install -y -qq python3-pip 2>/dev/null
        fi
        python3 -m ensurepip --upgrade >/dev/null 2>&1 || true
    fi

    python3 -m pip install -r requirements.txt 2>/dev/null \
        || python3 -m pip install --user -r requirements.txt 2>/dev/null \
        || python3 -m pip install --break-system-packages --user -r requirements.txt \
        || { echo "警告：依赖自动安装失败。请手动执行："; \
             echo "  pip3 install --break-system-packages -r requirements.txt"; }
fi

# ---------- 4. 运行签到 ----------
python3 sign_all.py
