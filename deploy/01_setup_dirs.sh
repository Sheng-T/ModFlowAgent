#!/usr/bin/env bash
# deploy/01_setup_dirs.sh — create required directory structure

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/common.sh"

[[ -f "${SCRIPT_DIR}/deploy.conf" ]] && source "${SCRIPT_DIR}/deploy.conf"
resolve_paths

log_step "Step 1 — Create directories"
show_paths

_dirs=(
    # Per-tool Singularity image directories
    "${DORADO_IMAGE_DIR}"
    "${SAMTOOLS_IMAGE_DIR}"
    "${MODKIT_IMAGE_DIR}"
    "${FASTQC_IMAGE_DIR}"
    "${PBJASMINE_IMAGE_DIR}"
    "${CCSMETH_IMAGE_DIR}"
    "${FIBERTOOLS_IMAGE_DIR}"
    "${PBMM2_IMAGE_DIR}"
    "${PBCPGTOOLS_IMAGE_DIR}"
    # methylong Nextflow pipeline image cache
    "${METHYLONG_IMAGE_DIR}"
    # Data and model directories
    "${DORADO_MODEL_DIR}"
    "${PIPELINE_DIR}/methylong"
    "${AGENT_DATA_DIR}"
    "${AGENT_DATA_DIR}/nextflow_work"
    "${AGENT_DATA_DIR}/.nextflow"
)

for d in "${_dirs[@]}"; do
    if [[ -d "$d" ]]; then
        log_info "Already exists: $d"
    else
        mkdir -p "$d"
        log_success "Created: $d"
    fi
done

log_done "Directory setup complete"
