<div align="center">

# ModFlowAgent

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://python.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2+-1C3C3C?logo=langchain&logoColor=white)](https://github.com/langchain-ai/langgraph)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.x-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

[English](README.md) | [中文](README_CN.md)

</div>

面向 HPC 集群的长读长表观基因组学分析 AI 智能体。用自然语言描述需求，系统自动完成工具和流水线的选择、参数生成、命令校验和容器化执行。

---

## 核心功能

- **单工具调用** - Dorado、samtools、modkit、fastqc。通过混合 RAG 检索参数文档，生成校验后的 shell 命令。
- **流水线** - 两种模式：nfcore（Nextflow）运行 methylong，自动生成 samplesheet 并校验；local（Singularity）运行 ont_rna 和 ont_dna，支持条件步骤跳过。
- **问答** - 通过混合 RAG 和可选的网络搜索回答工作流相关问题。

## 快速开始

### Docker 演示（轻量级，无需 HPC）

docker build -t modflowagent:latest .
docker run --rm -it -p 8501:8501 -e LLM_API_KEY=your_key -e LLM_API_BASE_URL=https://api.deepseek.com/v1 -e LLM_API_MODEL=deepseek-chat modflowagent:latest

打开 http://localhost:8501

### API 模式（pip + API Key）

git clone https://github.com/Sheng-T/ModFlowAgent.git
cd ModFlowAgent
pip install -r requirements.txt
cp api_keys.example.py api_keys.py
# 编辑 api_keys.py 填入 API Key，然后：
streamlit run ui/app_ui.py --server.address 0.0.0.0 --server.port 8501

### HPC 完整部署

bash deploy.sh
bash deploy.sh --skip-llm  # API 模式，不下载本地模型

## 使用示例

  对 ONT RNA POD5 数据进行 DRACH 基序的 m6A 分析。
  检查这个 BAM 文件是否包含 MM/ML 修饰标签。
  用 methylong 对 PacBio BAM 进行 Fiber-seq 分析。

## 文档

- 架构与设计：docs/architecture.md
- 部署指南：docs/deployment.md
- 开发者指南：docs/developer_guide.md
- 基准测试与销融：docs/benchmark.md

## 许可证

BSD-3-Clause-Clear
