#!/bin/bash
# ModFlowAgent start script — reads server config from config.yaml automatically
#
# Usage:
#   bash start.sh
#   bash start.sh --server.port 8080   #  override port temporarily

set -e
cd "$(dirname "$0")"  # ensure we run from project root

# Read server config from config.yaml then config.local.yaml (local wins)
_read_cfg() {
    python3 -c "
import yaml, os
def load(p):
    try:
        return yaml.safe_load(open(p)) or {}
    except Exception:
        return {}
def merge(base, ov):
    r = base.copy()
    for k, v in ov.items():
        r[k] = merge(r[k], v) if isinstance(r.get(k), dict) and isinstance(v, dict) else v
    return r
cfg = merge(load('config.yaml'), load('config.local.yaml') if os.path.exists('config.local.yaml') else {})
print((cfg.get('server') or {}).get('$1', '$2'))
" 2>/dev/null || echo "$2"
}

PORT=$(_read_cfg port 50027)
ADDRESS=$(_read_cfg address 0.0.0.0)
MAX_UPLOAD=$(_read_cfg max_upload_mb 10240)

echo "[ModFlowAgent] Starting on ${ADDRESS}:${PORT}  (max upload ${MAX_UPLOAD} MB)"
if [ "$ABLATION_NO_CONTROLLER" = "1" ]; then
    echo "[ModFlowAgent] Ablation mode: ABLATION_NO_CONTROLLER=1  (controller disabled)"
fi
if [ "$ABLATION_NO_VALIDATION" = "1" ]; then
    echo "[ModFlowAgent] Ablation mode: ABLATION_NO_VALIDATION=1  (validation disabled)"
fi
if [ "$ABLATION_NO_RAG" = "1" ]; then
    echo "[ModFlowAgent] Ablation mode: ABLATION_NO_RAG=1  (RAG disabled)"
fi
echo "[ModFlowAgent] Project root: $(pwd)"

exec streamlit run ui/app_ui.py \
    --server.address   "$ADDRESS" \
    --server.port      "$PORT" \
    --server.maxUploadSize "$MAX_UPLOAD" \
    --server.headless  true \
    --server.fileWatcherType none \
    "$@"
