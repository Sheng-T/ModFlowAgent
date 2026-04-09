# modkit 使用文档

## 简介
modkit 是 Oxford Nanopore Technologies 开发的工具，用于处理和分析 BAM 文件中的碱基修饰（base modification）信息，特别适用于 m6A、5mC 等表观遗传修饰的检测与汇总。

## 主要子命令

### pileup
将每条 read 上的碱基修饰调用汇总为 bedMethyl 格式的 pileup 文件。

**必需参数：**
- `bam`：输入 BAM 文件（必须已排序并建立索引）
- `output`：输出 bedMethyl 文件路径
- `--ref`：参考基因组 FASTA 文件

**常用可选参数：**
- `--threads`：线程数（默认 4）
- `--cpg`：仅输出 CpG 位点
- `--combine-strands`：合并正负链的修饰信息
- `--mod-thresholds`：设置修饰概率阈值，如 `m:0.8`

**示例：**
```bash
modkit pileup --ref reference.fa --cpg --combine-strands \
  --threads 4 input.bam output.bed
```

### extract
从 BAM 文件中提取每条 read 的碱基修饰数据。

**示例：**
```bash
modkit extract --threads 4 input.bam output.tsv
```

### summary
统计 BAM 中碱基修饰调用的概况。

**示例：**
```bash
modkit summary input.bam
```

### adjust-mods
调整 BAM 文件中碱基修饰的概率值（如忽略某种修饰或做类型转换）。

**示例：**
```bash
modkit adjust-mods --ignore h input.bam output.bam
```

## 输出格式
- `pileup` 输出标准 bedMethyl 格式（10 列），可直接用于下游甲基化分析
- `extract` 输出 TSV 格式，每行为一条 read 的修饰记录

## 注意事项
- 输入 BAM 需包含 MM/ML 标签（由 dorado 等工具生成）
- 使用 `pileup` 时 BAM 必须有索引（`.bai` 文件）
