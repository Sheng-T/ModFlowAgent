<div align="center">

# ModFlowAgent

A conversational agent for long-read epigenomics analysis on HPC clusters, built on LangGraph + Streamlit. You describe what you want in plain text; the agent figures out which tool or pipeline to run, generates the parameters, shows you the full command for review, and executes it inside Singularity containers.

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://python.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2+-1C3C3C?logo=langchain&logoColor=white)](https://github.com/langchain-ai/langgraph)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.x-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

**[English](README.md) · [中文](README_CN.md)**

</div>

---

## What it does

**Single tools** — `dorado`, `samtools`, `modkit`, `fastqc`. The agent picks the right subcommand, pulls parameters from the tool docs via hybrid RAG (BM25 + ChromaDB), and runs inside the appropriate Singularity image.

**Workflows** — two modes:
- **nfcore**: Nextflow pipelines (`methylong`). The agent generates and validates a samplesheet, checks MM/ML modification tags in BAM inputs, validates DMR group counts, then hands off to Nextflow.
- **local**: per-step Singularity chains (`ont_dna`, `ont_rna`). Steps run sequentially in isolated subdirectories. Optional steps (e.g. `modkit_pileup` when no reference is provided) are dropped automatically.

**Q&A** — bioinformatics questions answered with hybrid RAG over tool/workflow docs plus optional web search. For local workflows, the agent queries the relevant tool docs (declared in each workflow's manifest) to answer questions about them.

Human review happens at three points: workflow selection (when intent is ambiguous), prereq form (samplesheet or param form), and final command preview. You can edit at each step before anything runs.

---

## Supported workflows

| Name | Type | Molecule | Modifications |
|---|---|---|---|
| `methylong` | nfcore (Nextflow) | DNA | 5mCpG / 5hmCpG |
| `ont_rna` | local (Singularity) | RNA | m6A / m6A_DRACH / inosine / pseU / m5C / 2OmeG / all |
| `ont_dna` | local (Singularity) | DNA | 5mCG / 5hmCG / 5mC / 5hmC / 6mA / 4mC / all |

Adding a new workflow requires: (1) a `<name>_manifest.json` in `static/workflows/<name>/`, (2) a `WorkflowSpec` in `tools/workflow/registry.py`, and (3) step builders in `tools/workflow/local/<name>.py`. No graph changes needed.

---

## Quick start

### Requirements

- Python 3.10+
- Singularity / Apptainer
- Nextflow 23+ (nfcore workflows only)
- `pod5` Python package (optional — enables kit auto-detection for ont_rna)

### Installation

**One-click deployment (recommended for HPC servers)**

```bash
git clone https://github.com/yourname/bio-agent.git
cd bio-agent
bash deploy.sh
```

The wizard auto-detects CUDA, GPU, and RAM, then prompts for the few values it cannot detect (base directory, LLM mode, server port). All Singularity images, Dorado models, and LLM weights are downloaded automatically.

```bash
bash deploy.sh --skip-llm   # skip model download (API mode)
bash deploy.sh --step 3     # re-run a single step
bash deploy.sh --from 5     # resume from step 5
```

**Manual installation**

```bash
git clone https://github.com/yourname/bio-agent.git
cd bio-agent
pip install -r requirements.txt
```

### Configuration

All settings are in `config.yaml`. Server-specific overrides go in `config.local.yaml` (gitignored), which takes precedence.

```yaml
llm:
  model_name: qwen3_14B   # local model; ignored when api_key is set
  device: auto

tools:
  exec_env:
    type: conda
    env_name: sin         # fallback when no Singularity image is found
  threads: 8
  searxng_url: ""         # optional self-hosted SearXNG for web search

data:
  agent_data: ~/agent_data
  dorado_models: ~/tools/dorado_model/
  singularity_image_dir: ~/singularity_image
  pipeline_dir: ~/agent_workflow/
  nextflow_offline: true
  user_quota_gb: 100

users:
  admin: "CHANGE_ME"      # set a real password before first login
```

**LLM backend**

The system picks the backend based on whether an API key is configured:
- No key → local GPU model (`model_name` + `model_paths` in config.yaml)
- Key set → OpenAI-compatible API or Gemini (`api_keys.py`)

```bash
cp api_keys.example.py api_keys.py
```

```python
# api_keys.py
LLM_API_KEY      = "sk-xxxxxxxxxxxxxxxx"
LLM_API_BASE_URL = "https://api.deepseek.com/v1"
LLM_API_MODEL    = "deepseek-chat"
LLM_API_MAX_TOKENS = 4096
```

| Provider | `LLM_API_BASE_URL` | `LLM_API_MODEL` |
|---|---|---|
| DeepSeek | `https://api.deepseek.com/v1` | `deepseek-chat` |
| OpenAI | `https://api.openai.com/v1` | `gpt-4o` |
| SiliconFlow | `https://api.siliconflow.cn/v1` | `Qwen/Qwen3-235B-A22B` |
| Ollama (local) | `http://localhost:11434/v1` | `qwen3:14b` |
| Google Gemini | *(set `GEMINI_API_KEY` in `api_keys.py`)* | `gemini-2.5-flash` |



### Ablation modes

Three environment variables independently disable specific EpiAgent components for ablation analysis:

```bash
ABLATION_NO_CONTROLLER=1  bash start.sh   # bypass staged workflow controller
ABLATION_NO_VALIDATION=1 bash start.sh   # disable validation gates
ABLATION_NO_RAG=1         bash start.sh   # disable RAG grounding
```

Set multiple at once: `ABLATION_NO_CONTROLLER=1 ABLATION_NO_RAG=1 bash start.sh`


### Launch

```bash
streamlit run ui/app_ui.py --server.address 0.0.0.0 --server.port 8501
```

---

## Architecture

```
User Input
   │
   ▼
[router] ── intent classification ──────────────────────────────────────┐
   │                                                                    │
   ▼ tool / workflow                                       ▼ Q&A  ▼ off-topic
[tools_selector]                                     [llm_answer] [irrelevant]
   │
   ├── regular tool ──▶ [rag] ──▶ [planner] ──▶ [param_generator]
   │
   └── Workflow ──▶ [planner]
                       │
                       ├── workflow auto-resolved ──────────────────────────────┐
                       │                                                        │
                       └── intent ambiguous ──▶ [human_workflow_selector] ⏸    │
                                                  (user picks from list)        │
                                                           │                    │
                                          ┌────────────────┘                    │
                                          ▼                                     ▼
                                workflow_type == "nfcore"         workflow_type == "local"
                                          │                                     │
                                          ▼                                     ▼
                                   [rag_pipeline]               [local_prereq_generator]
                                          │                                     │
                                  [prereq_generator]      [human_local_prereq_reviewer] ⏸
                                  (samplesheet + validation)  (user confirms param form)
                                          │                                     │
                                          └──────────────┬──────────────────────┘
                                                         ▼
                                                [param_generator]
                                                         │
                                                [human_reviewer]  ← interrupt_after ⏸
                                             (full command preview)
                                                         │
                                                   [executor]
                                          ┌──────────────┴──────────────┐
                                          ▼                             ▼
                                    [summarizer] → END          [param_generator]
                                  (analyse + report)             (retry on failure)
```

### Interrupt nodes

| Node | Trigger | Interrupt mode |
|---|---|---|
| `human_workflow_selector` | LLM cannot confidently pick a workflow | `interrupt_before` |
| `human_prereq_reviewer` | nfcore samplesheet generated and validated | `interrupt_before` |
| `human_local_prereq_reviewer` | local workflow prereq params generated | `interrupt_before` |
| `human_reviewer` | all command params ready | `interrupt_after` |

`human_reviewer` uses `interrupt_after` so `pending_commands` is fully built before pausing. Resuming with `app.stream(None, config)` goes straight to `executor` without re-triggering the interrupt.

### Design notes

- **`workflow_type: str`** — `"nfcore"` / `"local"` / `""`. The only routing signal for the workflow branch.
- **Manifest-based auto-discovery** — `rag_config.py` scans `static/tools/` and `static/workflows/` at startup. Each workflow has a `<name>_manifest.json` declaring its type, description, input format, and which tools it uses. Adding a workflow or tool doc requires no code change.
- **`WorkflowSpec` registry** — `tools/workflow/registry.py` is the single source of truth for steps, display names, and recommended-for text. Sidebar and planner both read from here.
- **Deterministic step builders** — `tools/workflow/local/{name}.py` builds exact shell commands per step. modkit flags and thread counts are resolved here, not by the LLM.
- **`model_map.py`** — `(molecule, modification_type)` → dorado model pair + modkit flags. Adding a new modification type only requires editing this file.
- **Per-workflow prompt modules** — `agent_graph/prompts/workflows/{name}/` can provide `prereq_prompt.py`, `params_prompt.py`, and `qa_rules.py`. Missing modules fall back to generic prompts silently.
- **Domain-aware samplesheet validation** — path fixing → file existence check → BAM MM/ML tag check → DMR group validation. All issues are shown in the UI before anything runs.
- **`run_dir` isolation** — each run gets `session_dir/run_{id}_{timestamp}/`. Local workflow steps run in numbered subdirectories: `step01_dorado_download/`, `step02_dorado_basecaller/`, etc.
- **`pending_commands` reuse** — commands (with all paths and timestamps) are built once in the review node and reused by the executor. No path drift from regeneration.
- **Dynamic step trimming** — `local_prereq_generator` removes optional steps (e.g. `modkit_pileup`) from `tool_sequence` when required prereqs are absent (e.g. no `reference`).
- **Background file server** — `utils/file_server.py` serves large outputs over HTTP, bypassing the Streamlit WebSocket and avoiding MemoryError on multi-GB files.
- **App naming** — `configs/app_config.py` exports `APP_DISPLAY`, `APP_PASCAL`, `APP_SNAKE`. Renaming the app is a one-line change.

---

## Usage examples

**Q&A**
```
What is the difference between ont_dna and methylong?
What sequencing kits does modkit pileup support?
```

**Single tool**
```
Run dorado basecaller on my uploaded pod5 file using the sup model
```
→ selects dorado → RAG retrieves param docs → generates command → review panel → Singularity execution → BAM QC report

**nfcore workflow**
```
Run the methylong pipeline on my uploaded BAM file, do haplotype-level DMR analysis
```
→ identifies methylong → generates samplesheet.csv → path fixing + MM/ML tag check + DMR group validation → review panel → Nextflow → MultiQC report

**Local workflow (ont_rna)**
```
I have ONT direct-RNA pod5 data, detect m6A modifications
```
→ presents workflow candidates → user selects ont_rna → fills prereq form (data_file required, reference optional) → user confirms → executes in sequence:
1. `step01_dorado_download/` — downloads RNA basecall + inosine_m6A modification model
2. `step02_dorado_basecaller/` — basecall with `--modified-bases-models`
3. `step03_samtools_sort/` — coordinate-sort BAM
4. `step04_samtools_index/`
5. `step05_modkit_extract/` — per-read modification table
6. `step06_modkit_pileup/` — site-level bedMethyl (only when reference is provided)

→ generates modification frequency distributions, sequence context logos, 5-mer motif charts — all saved as PNG + PDF

---

## Developer guide

### Adding a new workflow

#### Local workflow (Singularity tool chain)

**1. Create the manifest** — `static/workflows/<name>/<name>_manifest.json`:

```json
{
  "type": "local",
  "short_description": "One-line description shown in Q&A context",
  "description": "Full description for the workflow selection dialog",
  "input": "POD5 or BAM (+ optional reference FASTA)",
  "tools": ["dorado", "modkit"],
  "qa_keywords": ["keyword1", "keyword2"]
}
```

`tools` lists which tool docs are pulled into Q&A for this workflow. `qa_keywords` are additional terms (beyond the workflow name) that trigger loading this workflow's context during Q&A.

**2. Register a WorkflowSpec** — `tools/workflow/registry.py`:

```python
register(WorkflowSpec(
    name            = "my_workflow",
    display_name    = "My Workflow",
    type            = "local",
    description     = "What it does",
    recommended_for = "When to use it",
    molecule        = "RNA",
    modification    = "m6A",
    input_formats   = ["pod5", "fast5"],
    steps           = ["dorado_download", "dorado_basecaller", "samtools_sort"],
    step_tools      = ["dorado", "dorado", "samtools"],
))
```

**3.** Add a prereq form entry in `static/workflows/workflow_prereqs.json`

**4.** Create `tools/workflow/local/my_workflow.py` with `build_step_command(step, prereq, data_path, step_dir, all_step_dirs)`

**5.** (Optional) Add `agent_graph/prompts/workflows/my_workflow/prereq_prompt.py`, `params_prompt.py`, `qa_rules.py` for custom prompts

**6.** (Optional) Add a result analyser in `tools/analyzers/workflow/local/` and register it in `tools/analyzers/workflow/registry.py`

#### nfcore workflow (Nextflow pipeline)

**1. Create the manifest** — `static/workflows/<name>/<name>_manifest.json`:

```json
{
  "type": "nfcore",
  "short_description": "One-line description",
  "description": "Full description for the workflow selection dialog",
  "input": "BAM or POD5 + reference FASTA",
  "tools": [],
  "qa_keywords": ["pipeline-specific", "tool-names", "method-terms"]
}
```

**2. Register a WorkflowSpec** — `tools/workflow/registry.py`:

```python
register(WorkflowSpec(
    name            = "my_nfcore",
    display_name    = "My nfcore Pipeline",
    type            = "nfcore",
    description     = "What it does",
    recommended_for = "When to use it",
    molecule        = "DNA",
    modification    = "5mCpG",
    input_formats   = ["bam", "pod5"],
    pipeline_id     = "my_nfcore",   # matches the nf-core pipeline name
))
```

**3.** Add a prereq entry in `static/workflows/workflow_prereqs.json` with `nfcore_pre_params` (pre-form questions) and `prereqs` (samplesheet column definitions)

**4.** Create `tools/workflow/nf/my_nfcore/validator.py` — implement `validate_nfcore_kwargs()`, `fix_paths()`, `validate_samplesheet()`, and the command builder function

**5.** (Optional) Add `agent_graph/prompts/workflows/my_nfcore/prereq_prompt.py` for a custom samplesheet generation prompt

**6.** (Optional) Add `static/workflows/my_nfcore/my_nfcore_doc.md` — automatically indexed for RAG Q&A

**7.** (Optional) Add a result analyser in `tools/analyzers/workflow/nf/` and register it in `tools/analyzers/workflow/registry.py`

### Adding a new modification type

Edit `tools/workflow/model_map.py` only:
1. Add the mod key → model name to `RNA_MOD_MODELS` or `DNA_MOD_MODELS`
2. Add the modkit flag logic to `get_modkit_flags()`
3. Add the user-facing option to `static/workflows/workflow_prereqs.json`

### Adding a new tool

1. Write the validator in `tools/toolchain/{tool}/validator.py`
2. Register in `tools/registry.py`: `TOOL_REGISTRY["tool_name"] = my_validator`
3. Add to `TOOL_LIST` in `configs/tool_config.py`
4. Add docs and args schema under `static/tools/{tool}/` (auto-discovered by RAG)

### Adding per-workflow QA hints

Create `agent_graph/prompts/workflows/{name}/qa_rules.py`:

```python
def get_qa_hints(lang: str = "en_US") -> str:
    if lang == "en_US":
        return "Rules injected into the Q&A prompt when this workflow is mentioned..."
    return "中文提示..."
```

The Q&A node discovers and injects this automatically.

---

## Tech stack

| Layer | Technology |
|---|---|
| Agent framework | LangGraph + LangChain |
| LLM | Local models (Qwen3) / any OpenAI-compatible API / Google Gemini |
| Vector retrieval | ChromaDB + HuggingFace Embeddings + BM25 hybrid |
| Web UI | Streamlit |
| Persistence | SQLite (session history + LangGraph checkpoints) |
| Container runtime | Singularity / Apptainer |
| Pipeline engine | Nextflow (nfcore) + direct Singularity (local) |
| File serving | Background HTTP server (streaming, avoids base64 overhead) |

---

## Contributing

Issues and pull requests are welcome.
