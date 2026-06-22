#!/bin/bash
# ================================================
# methylong Singularity 镜像批量下载脚本（增强版）
# 支持：断点续传、超时设置、重试机制
# 使用方式：
#   ./pull_methylong_images.sh [保存目录]
# 示例：
#   ./pull_methylong_images.sh /public/home/buguai/singularity_cache/methylong
# ================================================

set -euo pipefail

# ====================== 配置 ======================
if [ -n "${1:-}" ]; then
    CACHE_DIR="$1"
else
    CACHE_DIR="./methylong_images"
fi

USE_SIF=false                    # 你当前设置为 false（.img格式），改成 true 则下载 .sif
MAX_RETRIES=3                    # 每个镜像最大重试次数
TIMEOUT=1800                     # 单次下载超时时间（秒），30分钟

mkdir -p "$CACHE_DIR"
cd "$CACHE_DIR"

echo "========================================"
echo "methylong Singularity 镜像批量下载脚本（增强版）"
echo "保存目录: $CACHE_DIR"
echo "格式: $( [ "$USE_SIF" = true ] && echo ".sif" || echo ".img" )"
echo "超时设置: ${TIMEOUT}秒   重试次数: ${MAX_RETRIES}"
echo "========================================"

# ====================== 镜像列表 ======================
declare -A images

images["clair3"]="https://depot.galaxyproject.org/singularity/clair3:1.1.1--py310h779eee5_0"
images["fastqc"]="https://depot.galaxyproject.org/singularity/fastqc:0.12.1--hdfd78af_0"
images["gawk"]="https://depot.galaxyproject.org/singularity/gawk:5.3.0"
images["pigz"]="https://depot.galaxyproject.org/singularity/pigz:2.8"
images["samtools"]="https://depot.galaxyproject.org/singularity/samtools:1.22.1--h96c455f_0"
images["ccsmeth"]="https://depot.galaxyproject.org/singularity/ccsmeth:0.5.0--pyhdfd78af_0"
images["pbjasmine"]="https://depot.galaxyproject.org/singularity/pbjasmine:2.4.0--h9948957_1"
images["fibertools-rs"]="https://depot.galaxyproject.org/singularity/fibertools-rs:0.7.1--h3b373d1_0"
images["pbmm2"]="https://depot.galaxyproject.org/singularity/pbmm2:1.14.99--h9ee0642_0"
images["ont-modkit"]="https://depot.galaxyproject.org/singularity/ont-modkit:0.5.0--hcdda2d0_2"
images["whatshap"]="https://depot.galaxyproject.org/singularity/whatshap:2.6--py39h2de1943_0"
images["bioconductor-dss"]="https://depot.galaxyproject.org/singularity/bioconductor-dss:2.54.0--r44h3df3fcb_0"
images["ubuntu"]="https://depot.galaxyproject.org/singularity/ubuntu%3A24.04" 

images["pb-cpg-tools"]="https://quay.io/pacbio/pb-cpg-tools:3.0.0_build1"
images["dorado"]="https://depot.galaxyproject.org/singularity/dorado:0.9.0--h9ee0642_0" # 404

# ====================== 下载函数（带重试 + 断点续传） ======================
pull_image() {
    local name=$1
    local url=$2

    if [ "$USE_SIF" = true ]; then
        local filename="${name}.sif"
    else
        local filename="${name}.img"
    fi

    # 如果文件已存在且大小 > 10MB，则跳过（避免下载一半的文件）
    if [ -f "$filename" ] && [ "$(stat -c %s "$filename" 2>/dev/null || stat -f %z "$filename" 2>/dev/null)" -gt 10485760 ]; then
        echo "✅ 已存在且完整: $filename"
        return 0
    fi

    echo "🔄 正在下载: $name → $filename"

    local retry=0
    while [ $retry -lt $MAX_RETRIES ]; do
        if command -v singularity &> /dev/null; then
            timeout ${TIMEOUT}s singularity pull --name "$filename" "$url" && break
        elif command -v apptainer &> /dev/null; then
            timeout ${TIMEOUT}s apptainer pull --name "$filename" "$url" && break
        else
            echo "❌ 未找到 singularity 或 apptainer 命令！"
            exit 1
        fi

        retry=$((retry + 1))
        echo "⚠️ 下载失败，第 ${retry} 次重试... (共 ${MAX_RETRIES} 次)"
        sleep 10
    done

    if [ -f "$filename" ] && [ "$(stat -c %s "$filename" 2>/dev/null || stat -f %z "$filename" 2>/dev/null)" -gt 10485760 ]; then
        echo "✅ 下载完成: $filename"
    else
        echo "❌ 下载失败: $name （已重试 ${MAX_RETRIES} 次）"
        echo "   建议：使用 --singularity_pull_docker_container true 参数让 Nextflow 从 Docker Hub 下载"
    fi
    echo "----------------------------------------"
}

# ====================== 开始下载 ======================
echo "共 ${#images[@]} 个镜像需要处理..."

for name in "${!images[@]}"; do
    pull_image "$name" "${images[$name]}"
done

echo "========================================"
echo "批量下载任务执行完毕！"
echo "保存路径: $CACHE_DIR"
echo ""
ls -lh *.sif *.img 2>/dev/null || echo "没有找到镜像文件"

echo ""
echo "使用提示："
echo "export NXF_SINGULARITY_CACHEDIR=$CACHE_DIR"
echo "nextflow run nf-core/methylong -profile singularity ..."