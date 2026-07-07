<div align="center">

<img src="static/icon/logo.svg" width="70%" alt="ModFlowAgent logo">

# ModFlowAgent

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://python.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2+-1C3C3C?logo=langchain&logoColor=white)](https://github.com/langchain-ai/langgraph)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.x-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io)
[![License](https://img.shields.io/badge/License-BSD--3--Clause--Clear-green)](LICENSE)

[English](README.md) | [中文](README_CN.md)

</div>

## Overview

ModFlowAgent is a domain-specialized conversational agent for long-read DNA and RNA modification analysis.  
It converts natural-language requests into validated workflow plans, tool commands, and executable pipelines for:

- ONT RNA modification analysis (e.g., m6A, inosine)
- ONT DNA methylation analysis (e.g., 5mC, 5hmC)
- Single-tool operations (Dorado, modkit, samtools, FastQC)
- nf-core/methylong-based multi-step workflows (ONT / PacBio)

The system integrates **LLM + RAG + workflow validation + execution planning** into a unified agent framework.



---

## What it does

- **Single-tool calls:** Dorado, samtools, modkit, and FastQC. ModFlowAgent retrieves tool parameters via hybrid RAG and generates validated shell commands.
- **Workflow planning:** Supports nf-core/methylong via Nextflow and local ONT RNA/DNA workflows via Singularity-based tool chains.
- **Prerequisite validation:** Checks input formats, reference files, sample metadata, MM/ML tags, and workflow-specific constraints before execution.
- **Human-in-the-loop review:** Shows workflow plans, parameters, and final commands for user confirmation.
- **Q&A:** Answers workflow-related questions using hybrid RAG over tool and workflow documentation.

## Quick start

```bash
git clone https://github.com/Sheng-T/ModFlowAgent.git
cd ModFlowAgent
```

### Docker deployment

```bash
# Build the lightweight CPU image:
docker build -t modflowagent:cpu .

# Run ModFlowAgent with an OpenAI-compatible API backend:
docker run --rm -it -p 8501:8501 \
  -e LLM_API_KEY="your_key" \
  -e LLM_API_BASE_URL="your_api_base_url" \
  -e LLM_API_MODEL="your_model_name" \
  modflowagent:cpu
```

Then open: http://localhost:8501

Default demo login: 

```
Username: demo
Password: demo
```

> For deployment, please override the default account in `config.local.yaml`.

Docker mode is intended for lightweight demonstration of the web interface, Q&A, workflow routing, RAG-assisted planning when RAG resources are available, prerequisite validation, and command preview. It does not include Dorado, modkit, Nextflow, nf-core/methylong, Singularity/Apptainer, or local LLM weights. Full workflow execution requires the corresponding external tools and runtime environment.

### API-based setup with Conda

This mode starts the ModFlowAgent web interface and uses an OpenAI-compatible API backend. It is suitable for workflow planning, RAG-assisted Q&A, validation, and command preview without downloading local LLM weights.

```bash
conda create -n modflowagent python=3.11 -y
conda activate modflowagent

pip install --upgrade pip setuptools wheel
pip install --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt

cp api_keys.example.py api_keys.py
# Edit api_keys.py and add your API key(s)

bash start.sh

# To use a specific port:
bash start.sh --server.port 8501

```

### Configuration

ModFlowAgent can be configured through public defaults, private local overrides, and environment variables.

- `config.yaml` contains public default settings for demo and lightweight use.
- `config.local.yaml` is used for private or server-specific overrides, such as real user accounts, - local model paths, and execution paths. This file should not be committed.
- `api_keys.py` can be used for local API-based setup.
- Docker deployment should pass API settings through environment variables such as `LLM_API_KEY`, - `LLM_API_BASE_URL`, and `LLM_API_MODEL`.

The recommended priority is:

> environment variables > config.local.yaml > config.yaml > built-in defaults

### Optional workflow execution setup

The Docker and API-based setups are sufficient for launching the web interface, workflow planning, validation, RAG-assisted Q&A, and command preview. To actually execute long-read workflows, external tools and runtime environments such as Singularity/Apptainer, Nextflow, Dorado, modkit, and nf-core/methylong need to be installed or built.

ModFlowAgent provides deployment scripts for preparing these execution dependencies:

```bash
bash deploy.sh
bash deploy.sh --skip-llm  # API mode, skip downloading local LLM weights
```
> **Note**: Step 3 pulls Singularity images for pipeline execution. If image pulling fails due to network restrictions, the script reports the failed images and stops. You can continue the remaining setup with `bash deploy.sh --from 4`, then manually pull the failed images later. The web interface and LLM-based planning can run without these images, but executing Dorado/modkit/methylong workflows requires them.

## Usage examples

```
What can you do?
What is the best restaurant near my lab?
What is the difference between ont_dna and methylong?
Run DRACH-context m6A analysis on my ONT RNA POD5 data.
Profile CpG methylation from ONT DNA data.
Run methylong on ONT modBAM and skip SNV calling.
```

## Documentation

- Architecture & design: [docs/architecture.md](docs/architecture.md)
- Deployment: [docs/deployment.md](docs/deployment.md)
- Developer guide: [docs/developer_guide.md](docs/developer_guide.md)
- Benchmark & ablation: [docs/benchmark.md](docs/benchmark.md)