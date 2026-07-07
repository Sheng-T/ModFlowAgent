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

在浏览器中打开: http://localhost:8501

使用默认账号登录: 

```
Username: demo
Password: demo
```

> 部署时，请在 `config.local.yaml` 中覆盖默认帐户。

Docker 模式旨在轻量级演示 Web 界面、问答、工作流路由、RAG 资源可用时的 RAG 辅助规划、前提条件验证和命令预览。它不包含 Dorado、modkit、Nextflow、nf-core/methylong、Singularity/Apptainer 或本地 LLM 权重。完整的工作流执行需要相应的外部工具和运行时环境。

### Conda 最小安装

此模式启动 ModFlowAgent Web 界面，并使用与 OpenAI 兼容的 API 后端。它适用于工作流规划、RAG 辅助问答、验证和命令预览，无需下载本地 LLM 权重。

```bash
conda create -n modflowagent python=3.11 -y
pip install --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt

cp api_keys.example.py api_keys.py
# 编辑 api_keys.py 文件并添加您的 API 密钥

bash start.sh

# 要使用特定端口：
bash start.sh --server.port 8501
```

### 配置

ModFlowAgent 可以通过公共默认值、私有本地覆盖和环境变量进行配置。

- `config.yaml` 包含用于演示和轻量级使用的公共默认设置。
- `config.local.yaml` 用于私有或服务器特定的覆盖，例如真实用户帐户、本地模型路径和执行路径。此文件不应提交。
- `api_keys.py` 可用于基于本地 API 的设置。
- Docker 部署应通过环境变量传递 API 设置，例如 `LLM_API_KEY`、`LLM_API_BASE_URL` 和 `LLM_API_MODEL`。

建议的优先级为：

> 环境变量 > config.local.yaml > config.yaml > 内置默认值

### 可选的工作流执行设置

基于 Docker 和 API 的设置足以启动 Web 界面、进行工作流规划、验证、RAG 辅助问答以及命令预览。要实际执行长读取工作流，需要安装或构建外部工具和运行时环境，例如 Singularity/Apptainer、Nextflow、Dorado、modkit 和 nf-core/methylong。

ModFlowAgent 提供用于准备这些执行依赖项的部署脚本：

```bash
bash deploy.sh
bash deploy.sh --skip-llm
```
> **注意**：第 3 步会拉取用于执行流水线的 Singularity 镜像。如果因网络限制导致镜像拉取失败，脚本会报告失败的镜像并停止运行。您可以执行 `bash deploy.sh --from 4` 继续后续设置，稍后再手动拉取失败的镜像。Web 界面和基于 LLM 的规划功能无需这些镜像即可运行，但执行 Dorado、modkit 或 methylong 工作流则必须使用它们。

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

- 架构与设计: [docs/architecture.md](docs/architecture.md)
- 部署指南: [docs/deployment.md](docs/deployment.md)
- 开发者指南: [docs/developer_guide.md](docs/developer_guide.md)
- 基准测试与消融: [docs/benchmark.md](docs/benchmark.md)