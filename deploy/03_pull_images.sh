#!/usr/bin/env bash
# deploy/03_pull_images.sh — pull Singularity images for EpiAgent
#
# Layout after this step:
#   singularity_image/
#   ├── dorado/
#   │   └── dorado.img                              ← standalone tool
#   ├── fastqc/
#   │   └── fastqc.img                              ← standalone tool
#   ├── modkit/
#   │   └── modkit.img                              ← standalone tool
#   ├── samtools/
#   │   └── samtools.img                            ← standalone tool (v1.22.1)
#   └── workflow/
#       └── methylong/
#           ├── docker.io-nanoporetech-dorado-*.img  → ../../dorado/dorado.img (symlink)
#           ├── depot.*.fastqc-*.img                 → ../../fastqc/fastqc.img (symlink)
#           ├── depot.*.samtools-1.22.1-*.img        ← real file (same version; symlink also fine)
#           ├── depot.*.ont-modkit-*_2.img           ← real file (pipeline uses this newer version)
#           └── ... other methylong-only images

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/common.sh"

if [[ -z "${BASE_DIR:-}" ]]; then
    [[ -f "${SCRIPT_DIR}/deploy.conf" ]] && source "${SCRIPT_DIR}/deploy.conf"
    resolve_paths
fi

log_step "Step 3 — Pull Singularity images"

init_conda

_sng=""
for _c in singularity apptainer; do
    if conda_run "${SIN_ENV}" which "$_c" &>/dev/null; then
        _sng="conda_run ${SIN_ENV} ${_c}"; break
    elif command -v "$_c" &>/dev/null; then
        _sng="$_c"; break
    fi
done
[[ -z "${_sng}" ]] && die "Singularity/Apptainer not found. Run 02_setup_sin_env.sh first."

_total=0; _skipped=0; _ok=0; _failed=0
_failed_list=()

# Download via wget (Depot Galaxy images)
_wget_image() {
    local url="$1" dest="$2"
    local filename; filename="$(basename "${dest}")"
    (( _total++ )) || true
    if [[ -f "${dest}" ]]; then
        log_info "Skip (exists): ${filename}"; (( _skipped++ )) || true; return 0
    fi
    log_info "Downloading: ${filename}"
    local tmp="${dest}.tmp"
    if wget -q --show-progress -O "${tmp}" "${url}"; then
        mv "${tmp}" "${dest}"
        log_success "Done: ${filename}  ($(du -sh "${dest}" | cut -f1))"
        (( _ok++ )) || true
    else
        rm -f "${tmp}"
        log_error "Failed: ${filename}"
        _failed_list+=("${filename}"); (( _failed++ )) || true; return 1
    fi
}

# Download via singularity pull docker://
_docker_image() {
    local url="$1" dest="$2" fallback_url="${3:-}"
    local filename; filename="$(basename "${dest}")"
    (( _total++ )) || true
    if [[ -f "${dest}" ]]; then
        log_info "Skip (exists): ${filename}"; (( _skipped++ )) || true; return 0
    fi
    log_info "Pulling: ${filename}"
    if ${_sng} pull --force "${dest}" "${url}" 2>&1; then
        if [[ -f "${dest}" ]]; then
            log_success "Done: ${filename}  ($(du -sh "${dest}" | cut -f1))"
            (( _ok++ )) || true; return 0
        fi
    fi
    if [[ -n "${fallback_url}" ]]; then
        log_warn "Primary source failed, trying fallback: ${fallback_url}"
        if ${_sng} pull --force "${dest}" "${fallback_url}" 2>&1 && [[ -f "${dest}" ]]; then
            log_success "Done (fallback): ${filename}  ($(du -sh "${dest}" | cut -f1))"
            (( _ok++ )) || true; return 0
        fi
    fi
    log_error "Failed: ${filename}"
    _failed_list+=("${filename}"); (( _failed++ )) || true; return 1
}

# ── Single-tool images (simple filenames, used by env_wrapper._resolve_image_path) ──
log_info "--- Single-tool images ---"

# dorado — simple name; symlinked into methylong as the full hash-named file
_docker_image \
    "docker://nanoporetech/dorado:shae423e761540b9d08b526a1eb32faf498f32e8f22" \
    "${DORADO_IMAGE_DIR}/dorado.img" \
    "docker://docker.1ms.run/nanoporetech/dorado:shae423e761540b9d08b526a1eb32faf498f32e8f22"

# fastqc — simple name; symlinked into methylong
_wget_image \
    "https://depot.galaxyproject.org/singularity/fastqc:0.12.1--hdfd78af_0" \
    "${FASTQC_IMAGE_DIR}/fastqc.img"

# modkit — standalone version; methylong uses a different (newer) build pulled separately below
_wget_image \
    "https://depot.galaxyproject.org/singularity/ont-modkit:0.5.0--hcdda2d0_2" \
    "${MODKIT_IMAGE_DIR}/modkit.img"

# samtools — same version for both standalone and methylong (v1.22.1)
# Standalone image lives here; methylong image is a symlink to this file.
_wget_image \
    "https://depot.galaxyproject.org/singularity/samtools:1.22.1--h96c455f_0" \
    "${SAMTOOLS_IMAGE_DIR}/samtools.img"

# ── methylong pipeline images ────────────────────────────────────────────────
log_info "--- methylong pipeline images ---"

_wget_image \
    "https://depot.galaxyproject.org/singularity/clair3:1.1.1--py310h779eee5_0" \
    "${METHYLONG_IMAGE_DIR}/depot.galaxyproject.org-singularity-clair3-1.1.1--py310h779eee5_0.img"

_wget_image \
    "https://depot.galaxyproject.org/singularity/gawk:5.3.0" \
    "${METHYLONG_IMAGE_DIR}/depot.galaxyproject.org-singularity-gawk-5.3.0.img"

_wget_image \
    "https://depot.galaxyproject.org/singularity/pigz:2.8" \
    "${METHYLONG_IMAGE_DIR}/depot.galaxyproject.org-singularity-pigz-2.8.img"

_wget_image \
    "https://depot.galaxyproject.org/singularity/ccsmeth:0.5.0--pyhdfd78af_0" \
    "${METHYLONG_IMAGE_DIR}/depot.galaxyproject.org-singularity-ccsmeth-0.5.0--pyhdfd78af_0.img"

_wget_image \
    "https://depot.galaxyproject.org/singularity/pbjasmine:2.4.0--h9948957_1" \
    "${METHYLONG_IMAGE_DIR}/depot.galaxyproject.org-singularity-pbjasmine-2.4.0--h9948957_1.img"

_wget_image \
    "https://depot.galaxyproject.org/singularity/fibertools-rs:0.7.1--h3b373d1_0" \
    "${METHYLONG_IMAGE_DIR}/depot.galaxyproject.org-singularity-fibertools-rs-0.7.1--h3b373d1_0.img"

_wget_image \
    "https://depot.galaxyproject.org/singularity/pbmm2:1.14.99--h9ee0642_0" \
    "${METHYLONG_IMAGE_DIR}/depot.galaxyproject.org-singularity-pbmm2-1.14.99--h9ee0642_0.img"

_wget_image \
    "https://depot.galaxyproject.org/singularity/whatshap:2.6--py39h2de1943_0" \
    "${METHYLONG_IMAGE_DIR}/depot.galaxyproject.org-singularity-whatshap-2.6--py39h2de1943_0.img"

_wget_image \
    "https://depot.galaxyproject.org/singularity/bioconductor-dss:2.54.0--r44h3df3fcb_0" \
    "${METHYLONG_IMAGE_DIR}/depot.galaxyproject.org-singularity-bioconductor-dss-2.54.0--r44h3df3fcb_0.img"

_wget_image \
    "https://depot.galaxyproject.org/singularity/ubuntu%3A24.04" \
    "${METHYLONG_IMAGE_DIR}/depot.galaxyproject.org-singularity-ubuntu%3A24.04.img"

_docker_image \
    "docker://quay.io/pacbio/pb-cpg-tools:3.0.0_build1" \
    "${METHYLONG_IMAGE_DIR}/quay.io-pacbio-pb-cpg-tools-3.0.0_build1.img"

# ── Symlink shared images into methylong cache dir ────────────────────────────
# Rule: only symlink when the tool dir and methylong use the exact same image file.
#   dorado  → same build, symlinked
#   fastqc  → same build, symlinked
#   samtools → same version (v1.22.1), symlinked
#   modkit  → methylong uses _2 build (same as tool dir), symlinked
log_info "--- Symlinking tool images into workflow/methylong/ ---"

_symlink() {
    local src="$1" dst="$2"
    local dst_name; dst_name="$(basename "${dst}")"
    if [[ ! -f "${src}" ]]; then
        log_warn "Source not found, skipping symlink: ${src}"; return 0
    fi
    if [[ -L "${dst}" ]]; then
        log_info "Symlink already exists: ${dst_name}"; return 0
    elif [[ -f "${dst}" ]]; then
        log_warn "Real file already at symlink target — not replacing: ${dst_name}"; return 0
    fi
    ln -s "${src}" "${dst}"
    log_success "Symlinked: ${dst_name}"
}

_symlink \
    "${DORADO_IMAGE_DIR}/dorado.img" \
    "${METHYLONG_IMAGE_DIR}/docker.io-nanoporetech-dorado-shae423e761540b9d08b526a1eb32faf498f32e8f22.img"

_symlink \
    "${FASTQC_IMAGE_DIR}/fastqc.img" \
    "${METHYLONG_IMAGE_DIR}/depot.galaxyproject.org-singularity-fastqc-0.12.1--hdfd78af_0.img"

_symlink \
    "${SAMTOOLS_IMAGE_DIR}/samtools.img" \
    "${METHYLONG_IMAGE_DIR}/depot.galaxyproject.org-singularity-samtools-1.22.1--h96c455f_0.img"

_symlink \
    "${MODKIT_IMAGE_DIR}/modkit.img" \
    "${METHYLONG_IMAGE_DIR}/depot.galaxyproject.org-singularity-ont-modkit-0.5.0--hcdda2d0_2.img"

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

echo ""
echo -e "${_BLD}Images: total=${_total}  skipped=${_skipped}  ok=${_ok}  failed=${_failed}${_RST}"

if [[ ${_failed} -gt 0 ]]; then
    log_error "Failed images:"
    for f in "${_failed_list[@]}"; do echo "  - ${f}"; done
    exit 1
fi

log_done "Image pull complete"
