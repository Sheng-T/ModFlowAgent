<div align="center">

# 🧬 Bio-Agent

**Bioinformatics AI Agent for HPC Clusters**

Built on LangGraph — natural-language-driven tool invocation, Nextflow pipeline orchestration, and RAG-enhanced Q&A

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://python.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2+-1C3C3C?logo=langchain&logoColor=white)](https://github.com/langchain-ai/langgraph)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.x-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

**[English](README.md) · [中文](README_CN.md)**

[Features](#-features) · [Quick Start](#-quick-start) · [Architecture](#-architecture) · [Project Structure](#-project-structure)

</div>

---

## ✨ Features

| Feature | Description |
|---|---|
| 🤖 **Intent Routing** | Automatically classifies user input and routes to tool invocation / workflow pipeline / knowledge Q&A / off-topic rejection |
| 🔧 **Tool Chain** | Supports `dorado` (ONT basecall), `samtools`, `modkit`, `fastqc` — LLM auto-generates parameters, executed inside Singularity containers |
| 🔬 **Workflow Orchestration** | Integrates local Nextflow pipelines (`methylong`), auto-generates samplesheets, configures parameters via natural language |
| 🧠 **RAG-Enhanced Q&A** | Hybrid retrieval (BM25 + ChromaDB) over tool docs, combined with real-time web search for bioinformatics questions |
| 👤 **Human-in-the-Loop** | Pauses before every execution — shows the full command (including pre-file writes), supports Confirm / Modify / Cancel with a second confirmation to prevent accidents |
| 💾 **Persistent Sessions** | Multi-user + multi-session isolation; SQLite stores conversation history and LangGraph checkpoints; user files are stored under `uid/session` |
| 🌐 **Bilingual UI** | Interface supports English / 中文 switching; language preference is persisted per user |
| 📊 **Result Analysis** | After execution, automatically analyses output files (BAM flagstat/stats), generates QC charts and displays a summary report |

---

## 🚀 Quick Start

### Requirements

- Python 3.10+
- Singularity / Apptainer (container runtime for tool chain)
- Nextflow 23+ (Workflow mode)
- matplotlib (`pip install matplotlib`)

### Installation

```bash
git clone https://github.com/yourname/bio-agent.git
cd bio-agent
pip install -r requirements.txt
```

### Configuration

```bash
configs/
├── model_config.py      # LLM model path / API settings
├── path_config.py       # Data directories, image paths (image_store, user_data_root, etc.)
├── rag_config.py        # RAG document discovery, vector cache directory
└── workflow_config.py   # Supported Nextflow pipeline list
```

Key path settings (`configs/path_config.py`):

```python
IMAGE_PATH = {
    'image_store': "~/singularity_image",   # Singularity image dir, sub-dirs named by tool
}
DATA_PATH = {
    "dorado": {'base_data_dir': "~/agent_data", 'dorado_models': "~/tools/dorado_model/"},
    "workflow": {"base_data_dir": "~/agent_data"},
}
```

### Launch Web UI

```bash
streamlit run ui/app_ui.py --server.address 0.0.0.0 --server.port 8501
```

---

## 🏗️ Architecture

Bio-Agent uses **LangGraph** as its core, splitting the reasoning process into an observable node graph:

```
User Input
   │
   ▼
[router] ── intent classification ───────────────────────────┐
   │                                                         │
   ▼ tool / pipeline                            ▼ Q&A   ▼ off-topic
[tools_selector]                          [llm_answer] [irrelevant]
   │
   ▼
[rag]
   │
   ▼
[planner] ── tool_sequence empty ────────────────────── [summarizer] → END
   │
   ├── regular tool ───────────────────────────────────▶ [param_generator]
   │                                                           │
   └── Workflow ──▶ [rag_pipeline]                             │
                          │                                    │
                          ├── has prereqs ──▶ [prereq_generator] ──▶ [param_generator]
                          │                                    │
                          └── no prereqs ────────────────────▶ [param_generator]
                                                               │
                                                       [human_reviewer] ── ⏸️ interrupt_before
                                                               │
                                              ┌────────────────┼──────────────────────┐
                                              ▼                ▼                      ▼
                                        "executor"      "param_generator"         "end_node"
                                       (confirm run)    (modify & regenerate)      (cancel)
                                              │
                                         [executor]
                                              │
                                   ┌──────────┴───────────┐
                                   ▼                      ▼
                             [summarizer] → END     [param_generator]  (retry on failure)
```

### Key Design Decisions

- **`interrupt_before=["executor"]`** — Forces a pause before execution; the user reviews the full command (including samplesheet preview) and confirms before the agent proceeds.
- **`run_dir` isolation** — Each run creates an independent directory at `session_dir/run_{id}_{timestamp}/`; pre-files, outputs, and QC charts are all archived there without overwriting uploaded files.
- **`pending_commands` reuse** — Commands (including all paths and timestamps) are built once in the review node and reused by the executor, preventing path inconsistencies from regeneration.
- **Singularity wrapping** — Tool commands automatically extract bind paths and are transparently wrapped in `singularity exec`; Nextflow pipelines run on the host and manage containers internally via `-profile singularity`.

---

## 📁 Project Structure

```
bio-agent/
├── agent_graph/
│   ├── graph.py                  # LangGraph graph definition (nodes + edges + compile)
│   ├── state.py                  # AgentState definition
│   ├── nodes/
│   │   ├── router/               # Intent classification, session reset
│   │   ├── toolchain/            # Tool selection, RAG, Planner, parameter generation
│   │   ├── workflows/            # Pipeline selection, RAG, prereq file generation
│   │   └── execution/            # Command review, execution, result summarisation
│   └── prompts/                  # LLM prompt templates (bilingual)
├── tools/
│   ├── toolchain/
│   │   ├── dorado/               # dorado validator & command builder
│   │   ├── samtools/             # samtools validator
│   │   ├── modkit/               # modkit validator
│   │   └── fastqc/               # fastqc validator
│   ├── workflow/
│   │   └── methylong/            # methylong command builder
│   └── analyzers/                # Output file analysis (BAM QC, methylation, etc.)
├── runtime/
│   ├── executor.py               # Command execution (subprocess)
│   └── env_wrapper.py            # Singularity wrapping + automatic path binding
├── storage/
│   ├── checkpointer.py           # SqliteSaver singleton
│   ├── session_store.py          # User / session / message persistence
│   ├── file_manager.py           # User file management (quota, archiving)
│   └── rag_retriever.py          # BM25 + ChromaDB hybrid retrieval
├── configs/                      # Centralised configuration
├── static/
│   ├── dorado/                   # dorado tool docs + args schema
│   ├── samtools/                 # samtools tool docs + args schema
│   ├── modkit/                   # modkit tool docs + args schema
│   ├── fastqc/                   # fastqc tool docs + args schema
│   └── workflow/                 # workflow pipeline docs + prereqs config
├── utils/
│   ├── search_utils.py           # Web search + scraping + RAG augmentation
│   ├── user_context.py           # Thread-local session/run_dir context
│   ├── lang_utils.py             # get_lang() helper
│   ├── i18n.py                   # Internationalisation _() function
│   └── ui_logger.py              # Node logs → Streamlit queue bridge
├── ui/
│   ├── app_ui.py                 # Streamlit main entry point
│   ├── chat.py                   # Chat area, review panel, execution flow
│   ├── sidebar.py                # Session management, file upload, tool capability list
│   └── login.py                  # User login
└── main.py                       # CLI entry point
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Agent Framework | LangGraph + LangChain |
| LLM | Locally deployed models (Qwen3, etc.) / Remote API |
| Vector Retrieval | ChromaDB + HuggingFace Embeddings + BM25 hybrid |
| Web UI | Streamlit |
| Persistence | SQLite (session history + LangGraph checkpoints) |
| Container Runtime | Singularity / Apptainer |
| Pipeline Engine | Nextflow + local pipelines |

---

## 📖 Usage Examples

**Bioinformatics Q&A**
```
>>> What is the principle of methylation detection in ONT sequencing?
```
Agent triggers RAG retrieval + web search and synthesises an answer.

**Tool Invocation**
```
>>> Run dorado basecaller on my uploaded pod5 file using the sup model
```
Agent selects dorado → RAG retrieves parameter docs → generates command → shows review panel → after confirmation, executes inside Singularity → automatically analyses BAM output and generates a QC report.

**Nextflow Pipeline**
```
>>> Run the methylong pipeline on my uploaded BAM file and reference genome
```
Agent selects methylong pipeline → LLM generates samplesheet.csv from uploaded files → displays samplesheet preview and full command → after user confirmation, writes the samplesheet and launches Nextflow.

---

## 🤝 Contributing

Issues and pull requests are welcome.
