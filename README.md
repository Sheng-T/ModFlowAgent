<div align="center">

# ModFlowAgent

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://python.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2+-1C3C3C?logo=langchain&logoColor=white)](https://github.com/langchain-ai/langgraph)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.x-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

[English](README.md) | [??](README_CN.md)

</div>

A domain-specialized conversational agent for long-read DNA and RNA modification analysis. Converts natural-language requests into validated workflow plans and commands for ONT RNA, ONT DNA, single-tool operations, and nf-core/methylong-backed analysis.

---

## What it does

- **Single-tool calls** ? dorado, samtools, modkit, fastqc. Retrieves parameters via hybrid RAG (BM25 + ChromaDB) and generates validated shell commands.
- **Pipelines** ? Two modes: nfcore (Nextflow) for methylong with samplesheet validation, and local (Singularity) for ont_rna/ont_dna with conditional step skipping.
- **Q&A** ? Workflow-related questions answered via hybrid RAG with optional web search.

## Quick start

### Docker demo (lightweight, no HPC required)

```bash
docker build -t modflowagent:latest .
docker run --rm -it -p 8501:8501 \
  -e LLM_API_KEY="your_key" \
  -e LLM_API_BASE_URL="https://api.deepseek.com/v1" \
  -e LLM_API_MODEL="deepseek-chat" \
  modflowagent:latest
```

Then open http://localhost:8501

### API-based setup (pip + API key)

```bash
git clone https://github.com/Sheng-T/ModFlowAgent.git
cd ModFlowAgent
pip install -r requirements.txt
cp api_keys.example.py api_keys.py
# Edit api_keys.py, then:
streamlit run ui/app_ui.py --server.address 0.0.0.0 --server.port 8501
```

### Full HPC deployment

```bash
bash deploy.sh
bash deploy.sh --skip-llm  # API mode, no local LLM weights
```

## Usage examples

```
Run DRACH-context m6A analysis on my ONT RNA POD5 data.
Check if this BAM has MM/ML modification tags.
Run methylong with haplotype-level DMR analysis.
```

## Documentation

- Architecture & design: [docs/architecture.md](docs/architecture.md)
- Deployment: [docs/deployment.md](docs/deployment.md)
- Developer guide: [docs/developer_guide.md](docs/developer_guide.md)
- Benchmark & ablation: [docs/benchmark.md](docs/benchmark.md)

## License

BSD-3-Clause-Clear
