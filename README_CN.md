<div align="center">

<img src="static/icon/logo.svg" width="70%" alt="ModFlowAgent logo">

# ModFlowAgent

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://python.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2+-1C3C3C?logo=langchain&logoColor=white)](https://github.com/langchain-ai/langgraph)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.x-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io)
[![License](https://img.shields.io/badge/License-BSD--3--Clause--Clear-green)](LICENSE)

[English](README.md) | [中文](README_CN.md)

</div>

## 概述

ModFlowAgent 是一个面向长读长 DNA 和 RNA 修饰分析的领域专用对话智能体。它将自然语言需求转化为经过验证的工作流方案和可执行的流水线。

- ONT RNA 修饰分析（m6A、inosine 等）
- ONT DNA 甲基化分析（5mC、5hmC）
- 单工具操作（Dorado、modkit、samtools、FastQC）
- nf-core/methylong 多步骤工作流（ONT / PacBio）

## 核心功能

- 单工具调用：通过混合 RAG 检索文档，生成校验后的 shell 命令
- 工作流规划：支持 nf-core/methylong（Nextflow）和本地 ONT 工作流
- 前置校验：检查输入格式、参考文件、MM/ML 标签等
- 人工审核：展示方案和命令，用户确认后执行
- 问答：通过 RAG 回答工作流相关问题

## 快速开始
```bash
git clone https://github.com/Sheng-T/ModFlowAgent.git
cd ModFlowAgent
```

### Docker 部署
```bash
docker build -t modflowagent:cpu .
docker run --rm -it -p 8501:8501 -e LLM_API_KEY=your_key -e LLM_API_BASE_URL=your_url -e LLM_API_MODEL=your_model modflowagent:cpu
```

默认账号：demo / demo

### Conda 最小安装

```bash
conda create -n modflowagent python=3.11 -y
pip install --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt
cp api_keys.example.py api_keys.py
bash start.sh
```

### 完整部署

```bash
bash deploy.sh
bash deploy.sh --skip-llm
```

## 使用示例

```
你能做什么？
我实验室附近最好的餐厅是哪家？
ont_dna 和 methylong 有什么区别？
对我的 ONT RNA POD5 数据进行 DRACH-context m6A 分析。
分析 ONT DNA 数据的 CpG 甲基化情况。
对 ONT modBAM 数据进行 methylong 分析，并跳过 SNV 检测。
```

## 文档

- 架构与设计：docs/architecture.md
- 部署指南：docs/deployment.md
- 开发者指南：docs/developer_guide.md
- 基准测试与消融：docs/benchmark.md