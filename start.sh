#!/bin/bash
# BioAgent 启动脚本 — 自动从 config.yaml 读取服务配置
# BioAgent start script — reads server config from config.yaml automatically
#
# 用法 / Usage:
#   bash start.sh
#   bash start.sh --server.port 8080   # 临时覆盖端口 / override port temporarily

set -e
cd "$(dirname "$0")"  # 确保在项目根目录执行 / ensure we run from project root

# 从 config.yaml 读取 server 配置，读取失败则使用默认值
# Read server config from config.yaml, fall back to defaults on error
_read_cfg() {
    python3 -c "
import sys, yaml
try:
    c = yaml.safe_load(open('config.yaml')) or {}
    srv = c.get('server') or {}
    print(srv.get('$1', '$2'))
except Exception:
    print('$2')
" 2>/dev/null || echo "$2"
}

PORT=$(_read_cfg port 50027)
ADDRESS=$(_read_cfg address 0.0.0.0)
MAX_UPLOAD=$(_read_cfg max_upload_mb 10240)

echo "[BioAgent] Starting on ${ADDRESS}:${PORT}  (max upload ${MAX_UPLOAD} MB)"
echo "[BioAgent] Project root: $(pwd)"

exec streamlit run ui/app_ui.py \
    --server.address   "$ADDRESS" \
    --server.port      "$PORT" \
    --server.maxUploadSize "$MAX_UPLOAD" \
    --server.headless  true \
    "$@"
