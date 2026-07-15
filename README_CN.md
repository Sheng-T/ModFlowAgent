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

ModFlowAgent 是一个面向长读长 DNA 和 RNA 修饰分析的领域专用对话式智能体。  
它可以将自然语言请求转换为经过校验的工作流计划、工具命令和可执行分析流程，当前支持：

- ONT RNA 修饰分析（如 m6A、inosine）
- ONT DNA 甲基化分析（如 5mC、5hmC）
- PacBio DNA 修饰分析
- 单工具操作（Dorado、modkit、samtools、FastQC）
- 基于 methylong 的生产级多步骤工作流（ONT / PacBio）

系统将 **LLM + RAG + 工作流校验 + 执行规划** 集成到统一的智能体框架中。

---

## 核心功能

- **单工具调用：** 支持 Dorado、samtools、modkit 和 FastQC。ModFlowAgent 通过混合 RAG 检索工具参数，并生成经过校验的 shell 命令。
- **工作流规划：** 支持基于 Nextflow 的 methylong 工作流模式，以及本地 ONT RNA、ONT DNA、PacBio DNA 工作流。
- **前提条件校验：** 在执行前检查输入格式、参考文件、样本元数据、MM/ML 标签以及工作流特定约束。
- **人工审核：** 在执行前展示工作流计划、参数和最终命令，供用户确认。
- **问答：** 基于工具文档和工作流文档，通过混合 RAG 回答相关问题。

## 快速开始

```bash
git clone https://github.com/Sheng-T/ModFlowAgent.git
cd ModFlowAgent
```

### Docker 部署

```bash
# 构建轻量级 CPU 镜像
docker build -t modflowagent:cpu .

# 使用 OpenAI 兼容 API 作为后端运行
docker run --rm -it -p 8501:8501 \
  -e LLM_API_KEY="your_key" \
  -e LLM_API_BASE_URL="your_api_base_url" \
  -e LLM_API_MODEL="your_model_name" \
  modflowagent:cpu
```

然后在浏览器中打开：http://localhost:8501

默认演示账号：

```
Username: demo
Password: demo
```

> 正式部署时，请在 `config.local.yaml` 中覆盖默认账号。

Docker 模式主要用于轻量级演示 Web 界面、问答、工作流路由、RAG 辅助规划、前提条件校验和命令预览。它不包含 Dorado、modkit、Nextflow、methylong、Singularity/Apptainer 或本地 LLM 权重。完整执行工作流仍需要相应的外部工具和运行时环境。

### 基于 Conda 的 API 模式

该模式启动 ModFlowAgent Web 界面，并使用 OpenAI 兼容 API 作为后端。适合在不下载本地 LLM 权重的情况下进行工作流规划、RAG 辅助问答、校验和命令预览。

```bash
conda create -n modflowagent python=3.11 -y
conda activate modflowagent

pip install --upgrade pip setuptools wheel
pip install --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt

cp api_keys.example.py api_keys.py
# 编辑 api_keys.py 并添加你的 API key

bash start.sh

# 指定端口
bash start.sh --server.port 8501
```

### 配置

ModFlowAgent 可以通过公开默认配置、私有本地覆盖配置和环境变量进行配置。

- `config.yaml` 包含用于演示和轻量级使用的公开默认配置。
- `config.local.yaml` 用于私有或服务器特定覆盖，例如真实用户账号、本地模型路径和执行路径。该文件不应提交到仓库。
- `api_keys.py` 可用于本地 API 模式配置。
- Docker 部署建议通过环境变量传入 API 设置，例如 `LLM_API_KEY`、`LLM_API_BASE_URL` 和 `LLM_API_MODEL`。

推荐优先级：

> 环境变量 > config.local.yaml > config.yaml > 内置默认值

### 可选的工作流执行环境准备

Docker 模式和 API 模式足以启动 Web 界面、执行工作流规划、校验、RAG 辅助问答和命令预览。若要真正执行长读长工作流，还需要安装或构建外部工具和运行时环境，例如 Singularity/Apptainer、Nextflow、Dorado、modkit 和 methylong。

ModFlowAgent 提供了准备这些执行依赖项的部署脚本：

```bash
bash deploy.sh
bash deploy.sh --skip-llm  # API 模式，跳过本地 LLM 权重下载
bash deploy.sh --skip-images  # 跳过 Singularity 镜像拉取（第 3 步）
```

> **注意**：第 3 步和第 5 步需要 Singularity 镜像和 Dorado 模型才能执行流水线。如果因为网络限制导致镜像拉取失败，这些步骤会给出警告并跳过，而不会直接报错。可以使用 `bash deploy.sh --skip-images` 或 `bash deploy.sh --from 4` 继续完成其余安装。Web 界面和基于 LLM 的规划功能无需这些镜像即可运行，但执行 Dorado、modkit 或 methylong 工作流仍然需要它们。

## 使用示例

```
你能做什么？
我实验室附近最好的餐馆是哪家？
ont_dna 和 methylong 有什么区别？
对我的 ONT RNA POD5 数据进行 DRACH-context m6A 分析。
分析 ONT DNA 数据中的 CpG 甲基化情况。
对 ONT modBAM 数据运行 methylong，并跳过 SNV 检测。
```

## 文档

- 架构与设计：[docs/architecture.md](docs/architecture.md)
- 部署指南：[docs/deployment.md](docs/deployment.md)
- 开发者指南：[docs/developer_guide.md](docs/developer_guide.md)
- 基准测试与消融实验：[docs/benchmark.md](docs/benchmark.md)
