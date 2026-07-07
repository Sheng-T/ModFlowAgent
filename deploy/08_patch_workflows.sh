#!/usr/bin/env bash
# deploy/08_patch_workflows.sh — apply compatibility patches to installed workflows

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
source "${SCRIPT_DIR}/common.sh"

if [[ -z "${BASE_DIR:-}" ]]; then
    [[ -f "${SCRIPT_DIR}/deploy.conf" ]] && source "${SCRIPT_DIR}/deploy.conf"
    resolve_paths
fi

log_step "Step 9 — Apply workflow compatibility patches"

PIPELINE_DIR="${PIPELINE_DIR:-${BASE_DIR}/agent_workflow}"
STATIC_WORKFLOWS="${PROJECT_ROOT}/static/workflows"

patches_found=0
patches_applied=0

for workflow_dir in "${STATIC_WORKFLOWS}"/*/; do
    [[ -d "${workflow_dir}" ]] || continue
    workflow_name=$(basename "${workflow_dir}")
    patch_file="${workflow_dir}patch/patch.py"
    pipeline_target="${PIPELINE_DIR}/${workflow_name}"

    if [[ -f "${patch_file}" ]]; then
        patches_found=$((patches_found + 1))
        log_info "Found patch for workflow: ${workflow_name}"

        if [[ -d "${pipeline_target}" ]]; then
            log_info "  Applying: ${patch_file} -> ${pipeline_target}"
            init_conda
            conda_run "${AGENT_ENV}" python3 "${patch_file}" --base "${PIPELINE_DIR}" && {
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
