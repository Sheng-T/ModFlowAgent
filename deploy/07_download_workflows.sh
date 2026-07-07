#!/usr/bin/env bash
# deploy/07_download_workflows.sh — download and patch workflow files

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
source "${SCRIPT_DIR}/common.sh"

if [[ -z "${BASE_DIR:-}" ]]; then
    [[ -f "${SCRIPT_DIR}/deploy.conf" ]] && source "${SCRIPT_DIR}/deploy.conf"
    resolve_paths
fi

log_step "Step 7 — Apply workflow download and compatibility patches"

# ── Clone methylong pipeline ──────────────────────────────────────────────────
if [[ -n "${METHYLONG_PIPELINE_REPO:-}" ]]; then
    _pipeline_dest="${PIPELINE_DIR}/methylong"
    if [[ -d "${_pipeline_dest}/.git" ]]; then
        log_info "Pipeline repo exists, pulling latest..."
        git -C "${_pipeline_dest}" pull || log_warn "git pull failed, using existing code."
    else
        log_info "Cloning pipeline from ${METHYLONG_PIPELINE_REPO}..."
        _ref_arg=""
        [[ -n "${METHYLONG_PIPELINE_REF:-}" ]] && _ref_arg="--branch ${METHYLONG_PIPELINE_REF}"
        git clone ${_ref_arg} "${METHYLONG_PIPELINE_REPO}" "${_pipeline_dest}"
        log_success "Pipeline cloned to ${_pipeline_dest}"
    fi
else
    log_warn "METHYLONG_PIPELINE_REPO not set — place pipeline code manually at ${PIPELINE_DIR}/methylong/"
fi

# ── Pipeline compatibility patches ──────────────────────────────────────────────────
log_info "Applying workflow compatibility patches..."
PIPELINE_DIR="${PIPELINE_DIR:-${BASE_DIR}/agent_workflow}"
STATIC_WORKFLOWS="${PROJECT_ROOT}/static/workflows"
SINGULARITY_DIR="${SINGULARITY_DIR:-${BASE_DIR}/singularity_image}"
IMAGE_DIR="${SINGULARITY_DIR}/workflow"

patches_found=0
patches_applied=0

for workflow_dir in "${STATIC_WORKFLOWS}"/*/; do
    [[ -d "${workflow_dir}" ]] || continue
    workflow_name=$(basename "${workflow_dir}")
    patch_file="${workflow_dir}patch/patch.py"
    pipeline_target="${PIPELINE_DIR}/${workflow_name}"
    pipeline_image_dir="${IMAGE_DIR}/${workflow_name}"

    if [[ -f "${patch_file}" ]]; then
        patches_found=$((patches_found + 1))
        log_info "Found patch for workflow: ${workflow_name}"

        if [[ -d "${pipeline_target}" ]]; then
            log_info "  Applying: ${patch_file} -> ${pipeline_target}"
            init_conda
            conda_run "${AGENT_ENV}" python3 "${patch_file}" --base "${PIPELINE_DIR}" --cache-dir "${pipeline_image_dir}" && {
                patches_applied=$((patches_applied + 1))
                log_success "Patched: ${workflow_name}"
            } || {
                log_error "Failed to patch: ${workflow_name}"
            }
        else
            log_warn "Pipeline directory not found, skipping: ${pipeline_target}"
        fi
    fi
done

if [[ ${patches_found} -eq 0 ]]; then
    log_info "No workflow patches found in ${STATIC_WORKFLOWS}"
elif [[ ${patches_applied} -lt ${patches_found} ]]; then
    log_warn "${patches_applied}/${patches_found} patches applied (some skipped)"
else
    log_success "${patches_applied} workflow patch(es) applied."
fi

log_done "Workflow patching complete"


