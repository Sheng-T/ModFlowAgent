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
- Production-scale methylong-based multi-step workflows (ONT / PacBio)

The system integrates **LLM + RAG + workflow validation + execution planning** into a unified agent framework.



---

## What it does

- **Single-tool calls:** Dorado, samtools, modkit, and FastQC. ModFlowAgent retrieves tool parameters via hybrid RAG and generates validated shell commands.
- **Workflow planning:** Supports a production-scale methylong workflow mode via Nextflow and local ONT RNA, ONT DNA, and PacBio DNA workflows via Singularity-based tool chains.
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

Docker mode is intended for lightweight demonstration of the web interface, Q&A, workflow routing, RAG-assisted planning when RAG resources are available, prerequisite validation, and command preview. It does not include Dorado, modkit, Nextflow, methylong, Singularity/Apptainer, or local LLM weights. Full workflow execution requires the corresponding external tools and runtime environment.

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
- `config.local.yaml` is used for private or server-specific overrides, such as real user accounts, local model paths, and execution paths. This file should not be committed.
- `api_keys.py` can be used for local API-based setup.
- Docker deployment should pass API settings through environment variables such as `LLM_API_KEY`, `LLM_API_BASE_URL`, and `LLM_API_MODEL`.

The recommended priority is:

> environment variables > config.local.yaml > config.yaml > built-in defaults

### Optional workflow execution setup

The Docker and API-based setups are sufficient for launching the web interface, workflow planning, validation, RAG-assisted Q&A, and command preview. To actually execute long-read workflows, external tools and runtime environments such as Singularity/Apptainer, Nextflow, Dorado, modkit, and methylong need to be installed or built.

ModFlowAgent provides deployment scripts for preparing these execution dependencies:

```bash
bash deploy.sh
bash deploy.sh --skip-llm  # API mode, skip downloading local LLM weights
bash deploy.sh --skip-images  # skip Singularity image pull (step 3)
```
> **Note**: Steps 3 and 5 require Singularity images and Dorado models for pipeline execution. If image pulling fails due to network restrictions, these steps produce warnings and skip instead of erroring. Run `bash deploy.sh --skip-images` or `bash deploy.sh --from 4` to continue setup without them. The web interface and LLM-based planning work without these images, but executing Dorado/modkit/methylong workflows requires them.

## Test dataset and reproducible demo

This repository includes a small ONT DNA 5mC demo dataset in [`demo/`](demo/):

- `demo/5mC_test_200.pod5`: POD5 input subset
- `demo/all_5mers.fa`: matching reference FASTA
- `demo/all_5mers_5mC_sites.bed`: expected 5mC sites from the validation reference
- `demo/test_200_ids.txt`: read IDs used to generate the subset

The demo subset was derived from the Oxford Nanopore modified-base validation data hosted in [ONT Open Datasets](https://registry.opendata.aws/ont-open-data/) under `s3://ont-open-data/modbase-validation_2024.10/`.

To run ModFlowAgent on the bundled test dataset:

```bash
# Prepare the full execution environment, including workflow images and Dorado models.
bash deploy.sh --skip-llm

# Start the web interface.
bash start.sh
```

Then open http://localhost:8501 and use one of the following prompts, replacing the paths with the downloaded test data and matching reference FASTA:

```text
Profile 5mC methylation from ONT DNA POD5 test data at /absolute/path/to/ModFlowAgent/demo/5mC_test_200.pod5 and use reference /absolute/path/to/ModFlowAgent/demo/all_5mers.fa.
```

For lightweight review without running external bioinformatics tools, the same prompts can be used in Docker or API mode to test workflow routing, prerequisite validation, and command generation.

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
