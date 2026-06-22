# Workflow Pipeline 选择指南

## 支持的 Pipeline

### methylong
ONT（Oxford Nanopore）或 PacBio HiFi 数据的长读长甲基化分析流水线。
- 适用场景：分析 BAM 格式的长读长测序数据中的 **DNA 甲基化修饰**（5mC、6mA 等）
- 输入文件：BAM 文件（已 basecall）+ 参考基因组 FASTA 文件
- 需要 samplesheet.csv（列：group, sample, path, ref, method）
- method 字段：pacbio 或 ont
- 示例行：group1,sample1,sample1.bam,ref.fasta,ont
