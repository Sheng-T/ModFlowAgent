<div align="center">

# ModFlowAgent

面向 HPC 集群的长读长表观基因组学分析 AI 智能体，基于 LangGraph + Streamlit 构建。用自然语言描述需求，系统自动决定调用哪个工具或流水线、生成参数、展示完整命令供审查，然后在 Singularity 容器内执行。

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://python.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2+-1C3C3C?logo=langchain&logoColor=white)](https://github.com/langchain-ai/langgraph)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.x-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

**[English](README.md) · [中文](README_CN.md)**

</div>

---

## 能做什么

**单工具调用** — `dorado`、`samtools`、`modkit`、`fastqc`。系统选择合适的子命令，通过混合 RAG（BM25 + ChromaDB）检索工具文档生成参数，在对应 Singularity 镜像中运行。

**流水线** — 两种模式：
- **nfcore**：Nextflow 流水线（`methylong`）。系统生成并校验 samplesheet，检查 BAM 输入的 MM/ML 修饰标签、DMR 分组数量，再交给 Nextflow 执行。
- **local**：多步骤 Singularity 串联（`ont_dna`、`ont_rna`）。各步骤在独立子目录中顺序执行；可选步骤（如没有 reference 时的 `modkit_pileup`）自动跳过。

**问答** — 生信问题通过混合 RAG 检索工具/流水线文档并结合可选网络搜索来回答。对于本地流水线，系统会查询 manifest 中声明的工具文档来支持相关问题。

有三处人工审查节点：流水线选择（意图不明确时）、前置参数表单（samplesheet 或参数表单）、命令确认。每处都可以修改，确认后才执行。

---

## 支持的流水线

| 名称 | 类型 | 分子 | 支持修饰类型 |
|---|---|---|---|
| `methylong` | nfcore (Nextflow) | DNA | 5mCpG / 5hmCpG |
| `ont_rna` | local (Singularity) | RNA | m6A / m6A_DRACH / inosine / pseU / m5C / 2OmeG / all |
| `ont_dna` | local (Singularity) | DNA | 5mCG / 5hmCG / 5mC / 5hmC / 6mA / 4mC / all |

新增流水线需要：(1) 在 `static/workflows/<name>/` 创建 `<name>_manifest.json`，(2) 在 `tools/workflow/registry.py` 注册 `WorkflowSpec`，(3) 在 `tools/workflow/local/<name>.py` 实现步骤构建器。不需要修改图定义。

---

## 快速开始

### 环境要求

- Python 3.10+
- Singularity / Apptainer
- Nextflow 23+（仅 nfcore 模式）
- `pod5` Python 包（可选，ont_rna 的 kit 自动检测）

### 安装

**一键部署（推荐用于 HPC 服务器）**

```bash
git clone https://github.com/Sheng-T/ModFlowAgent.git
cd ModFlowAgent
bash deploy.sh
```

向导自动检测 CUDA、GPU 和内存，仅需填写少量无法自动检测的参数（数据目录、LLM 模式、端口等）。Singularity 镜像、Dorado 模型和大语言模型权重均自动下载。

```bash
bash deploy.sh --skip-llm   # 跳过模型下载（使用 API 模式）
bash deploy.sh --step 3     # 单独重跑某一步
bash deploy.sh --from 5     # 从第 5 步续跑
```

**手动安装**

```bash
git clone https://github.com/Sheng-T/ModFlowAgent.git
cd ModFlowAgent
pip install -r requirements.txt
```

### 配置

所有配置在 `config.yaml` 中。服务器私有覆盖写在 `config.local.yaml`（已加入 .gitignore），同名键优先级更高。

```yaml
llm:
  model_name: qwen3_14B   # 本地模型，设置了 api_key 时忽略
  device: auto

tools:
  exec_env:
    type: conda
    env_name: sin         # 找不到 Singularity 镜像时的回退环境
  threads: 8
  searxng_url: ""         # 可选，自建 SearXNG 实例

data:
  agent_data: ~/agent_data
  dorado_models: ~/tools/dorado_model/
  singularity_image_dir: ~/singularity_image
  pipeline_dir: ~/agent_workflow/
  nextflow_offline: true
  user_quota_gb: 100

users:
  admin: "CHANGE_ME"      # 首次登录前请设置真实密码
```

**切换 LLM 后端**

系统根据是否配置 API Key 自动切换：
- 未填 Key → 本地 GPU 模型（在 config.yaml 里设置 `model_name` 和 `model_paths`）
- 填了 Key → OpenAI-compatible API 或 Gemini（在 `api_keys.py` 配置）

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

| 服务商 | `LLM_API_BASE_URL` | `LLM_API_MODEL` |
|---|---|---|
| DeepSeek | `https://api.deepseek.com/v1` | `deepseek-chat` |
| OpenAI | `https://api.openai.com/v1` | `gpt-4o` |
| SiliconFlow | `https://api.siliconflow.cn/v1` | `Qwen/Qwen3-235B-A22B` |
| Ollama（本地） | `http://localhost:11434/v1` | `qwen3:14b` |
| Google Gemini | *(在 `api_keys.py` 设置 `GEMINI_API_KEY`)* | `gemini-2.5-flash` |

### 启动

```bash
streamlit run ui/app_ui.py --server.address 0.0.0.0 --server.port 8501
```

---

## 架构

```
用户输入
   │
   ▼
[router] ── 意图分类 ─────────────────────────────────────────────────────┐
   │                                                                      │
   ▼ 工具 / 流水线                                             ▼ 问答  ▼ 无关
[tools_selector]                                          [llm_answer]  [irrelevant]
   │
   ├── 普通工具 ──▶ [rag] ──▶ [planner] ──▶ [param_generator]
   │
   └── Workflow ──▶ [planner]
                       │
                       ├── 自动识别 ────────────────────────────────────────┐
                       │                                                    │
                       └── 意图模糊 ──▶ [human_workflow_selector] ⏸         │
                                           (用户从候选列表选择)               │
                                                    │                       │
                                   ┌────────────────┘                       │
                                   ▼                                        ▼
                         workflow_type == "nfcore"           workflow_type == "local"
                                   │                                        │
                                   ▼                                        ▼
                            [rag_pipeline]                  [local_prereq_generator]
                                   │                                        │
                           [prereq_generator]           [human_local_prereq_reviewer] ⏸
                         (samplesheet + 校验)              (用户确认/修改参数表单)
                                   │                                        │
                                   └──────────────┬─────────────────────────┘
                                                  ▼
                                         [param_generator]
                                                  │
                                         [human_reviewer]  ← interrupt_after ⏸
                                           (展示完整命令)
                                                  │
                                            [executor]
                                   ┌──────────────┴──────────────┐
                                   ▼                             ▼
                             [summarizer] → END          [param_generator]
                          (分析结果 + 生成报告)             (失败重试)
```

### 中断节点

| 节点 | 触发条件 | 中断方式 |
|---|---|---|
| `human_workflow_selector` | LLM 无法确定选哪个流水线 | `interrupt_before` |
| `human_prereq_reviewer` | nfcore samplesheet 已生成并校验 | `interrupt_before` |
| `human_local_prereq_reviewer` | 本地流水线前置参数已生成 | `interrupt_before` |
| `human_reviewer` | 所有命令参数就绪 | `interrupt_after` |

`human_reviewer` 用 `interrupt_after`：节点执行完（`pending_commands` 已生成）才暂停，用户确认后 `app.stream(None, config)` 直接进 `executor`，不会重复触发中断。

### 设计说明

- **`workflow_type: str`** — 取值 `"nfcore"` / `"local"` / `""`，是 workflow 分支路由的唯一信号
- **Manifest 自动发现** — `rag_config.py` 启动时扫描 `static/tools/` 和 `static/workflows/`。每个流水线有 `<name>_manifest.json`，声明类型、描述、输入格式和使用的工具列表。新增流水线文档无需改代码
- **`WorkflowSpec` 注册表** — `tools/workflow/registry.py` 是步骤定义、显示名称、推荐理由的唯一来源，侧边栏和 planner 都从这里读
- **确定性步骤构建器** — `tools/workflow/local/{name}.py` 按步骤生成精确的 shell 命令，不依赖 LLM，保证可复现。modkit flags 和线程数在这里注入
- **`model_map.py`** — `(molecule, modification_type)` → dorado 模型对 + modkit flags 的完整映射，新增修饰类型只需编辑这一个文件
- **per-workflow 提示词模块** — `agent_graph/prompts/workflows/{name}/` 可以放 `prereq_prompt.py`、`params_prompt.py`、`qa_rules.py`，节点通过 `importlib` 动态发现，缺失时无声回退到通用模板
- **领域感知 samplesheet 校验** — LLM 生成后依次执行：路径修正 → 文件存在检查 → BAM MM/ML 标签检查 → DMR 分组校验，命令执行前把问题全部暴露出来
- **`run_dir` 隔离** — 每次运行在 `session_dir/run_{id}_{timestamp}/` 下创建独立目录；本地流水线每步在 `step01_xxx/`、`step02_xxx/` 等子目录中运行
- **`pending_commands` 复用** — review 节点一次性确定所有路径（含时间戳），executor 直接复用，不会因重新生成导致路径漂移
- **动态步骤裁剪** — `local_prereq_generator` 根据前置参数自动从 `tool_sequence` 中移除可选步骤（如无 `reference` 时去掉 `modkit_pileup`）
- **后台文件服务器** — `utils/file_server.py` 通过 HTTP 提供大文件下载，绕过 Streamlit WebSocket，彻底避免 GB 级文件的 MemoryError
- **应用统一命名** — `configs/app_config.py` 导出 `APP_DISPLAY`、`APP_PASCAL`、`APP_SNAKE`，改名只需改这一行

---

## 使用示例

**问答**
```
ont_dna 和 methylong 有什么区别？
modkit pileup 支持哪些测序 kit？
```

**单工具调用**
```
用 dorado basecaller 对我上传的 pod5 文件进行 basecall，模型用 sup
```
→ 选择 dorado → RAG 检索参数文档 → 生成命令 → 审查面板 → Singularity 执行 → BAM QC 报告

**nfcore 流水线**
```
用 methylong 分析我的 BAM 文件，做单倍型级别的 DMR 分析
```
→ 识别 methylong → 生成 samplesheet.csv → 路径修正 + MM/ML 标签检查 + DMR 分组校验 → 审查面板 → Nextflow → MultiQC 报告

**本地流水线（ont_rna）**
```
我有 ONT direct-RNA pod5 数据，帮我检测 m6A 修饰
```
→ 展示流水线候选 → 用户选择 ont_rna → 填写参数表单（data_file 必填，reference 可选）→ 用户确认 → 逐步执行：
1. `step01_dorado_download/` — 下载 RNA basecall 模型 + inosine_m6A 修饰模型
2. `step02_dorado_basecaller/` — basecall，自动附加 `--modified-bases-models`
3. `step03_samtools_sort/` — 坐标排序
4. `step04_samtools_index/`
5. `step05_modkit_extract/` — 逐读修饰表
6. `step06_modkit_pileup/` — site-level bedMethyl（仅有 reference 时执行）

→ 生成修饰频率分布图、序列上下文 Logo、5-mer motif 图表，全部保存为 PNG + PDF

---

## 开发指南

### 新增流水线

#### Local 流水线（Singularity 工具链）

**第 1 步：创建 manifest** — `static/workflows/<name>/<name>_manifest.json`：

```json
{
  "type": "local",
  "short_description": "一行简介，显示在问答上下文中",
  "description": "完整描述，显示在流水线选择弹窗中",
  "input": "POD5 或 BAM（+ 可选 reference FASTA）",
  "tools": ["dorado", "modkit"],
  "qa_keywords": ["关键词1", "关键词2"]
}
```

`tools` 列出该流水线使用的工具，用于问答时查询对应工具文档。`qa_keywords` 是触发加载该流水线上下文的额外关键词（工具名、方法名等），用户提问时无需说出流水线名称也能命中。

**第 2 步：注册 WorkflowSpec** — `tools/workflow/registry.py`：

```python
register(WorkflowSpec(
    name         = "my_workflow",
    display_name = "My Workflow",
    type         = "local",
    description  = "做什么",
    recommended_for = "什么情况下推荐",
    molecule     = "DNA",
    modification = "5mCG",
    input_formats= ["pod5", "bam"],
    steps        = ["dorado_basecaller", "samtools_sort", "modkit_pileup"],
    step_tools   = ["dorado", "samtools", "modkit"],
))
```

**第 3 步：** 在 `static/workflows/workflow_prereqs.json` 添加前置参数表单定义

**第 4 步：** 创建 `tools/workflow/local/my_workflow.py`，实现 `build_step_command(step, prereq, data_path, step_dir, all_step_dirs)`

**第 5 步：**（可选）在 `agent_graph/prompts/workflows/my_workflow/` 下添加 `prereq_prompt.py`、`params_prompt.py`、`qa_rules.py`

**第 6 步：**（可选）在 `tools/analyzers/workflow/local/` 添加结果分析器并注册到 `tools/analyzers/workflow/registry.py`

#### nfcore 流水线（Nextflow 流水线）

**第 1 步：创建 manifest** — `static/workflows/<name>/<name>_manifest.json`：

```json
{
  "type": "nfcore",
  "short_description": "一行简介",
  "description": "完整描述",
  "input": "BAM 或 POD5 + reference FASTA",
  "tools": [],
  "qa_keywords": ["流水线特有工具名", "方法名"]
}
```

**第 2 步：注册 WorkflowSpec** — `tools/workflow/registry.py`：

```python
register(WorkflowSpec(
    name         = "my_nfcore",
    display_name = "My nfcore Pipeline",
    type         = "nfcore",
    description  = "做什么",
    recommended_for = "什么情况下推荐",
    molecule     = "DNA",
    modification = "5mCpG",
    input_formats= ["bam", "pod5"],
    pipeline_id  = "my_nfcore",   # 与 nf-core 流水线名称一致
))
```

**第 3 步：** 在 `static/workflows/workflow_prereqs.json` 中添加条目，包含 `nfcore_pre_params`（预填表单问题）和 `prereqs`（samplesheet 列定义）

**第 4 步：** 创建 `tools/workflow/nf/my_nfcore/validator.py`，实现 `validate_nfcore_kwargs()`、`fix_paths()`、`validate_samplesheet()` 和命令构建函数

**第 5 步：**（可选）添加 `agent_graph/prompts/workflows/my_nfcore/prereq_prompt.py` 自定义 samplesheet 生成提示词

**第 6 步：**（可选）添加 `static/workflows/my_nfcore/my_nfcore_doc.md`，自动被 RAG 索引用于问答

**第 7 步：**（可选）在 `tools/analyzers/workflow/nf/` 添加结果分析器并注册到 `tools/analyzers/workflow/registry.py`

### 新增修饰类型

只需编辑 `tools/workflow/model_map.py`：
1. 在 `RNA_MOD_MODELS` 或 `DNA_MOD_MODELS` 中添加 mod_key → 模型名映射
2. 在 `get_modkit_flags()` 中添加对应 flag 逻辑
3. 在 `static/workflows/workflow_prereqs.json` 添加用户可选项

步骤构建器、图定义等文件均无需修改。

### 新增单工具

1. 在 `tools/toolchain/{tool}/validator.py` 写命令构建函数
2. 在 `tools/registry.py` 注册：`TOOL_REGISTRY["tool_name"] = my_validator`
3. 在 `configs/tool_config.py` 的 `TOOL_LIST` 中添加工具名
4. 在 `static/tools/{tool}/` 下放工具文档和 args schema（RAG 自动发现）

### 新增 per-workflow 问答提示

创建 `agent_graph/prompts/workflows/{name}/qa_rules.py`：

```python
def get_qa_hints(lang: str = "en_US") -> str:
    if lang == "en_US":
        return "Rules injected into Q&A prompt when this workflow is mentioned..."
    return "该流水线被提及时注入问答提示词的中文规则..."
```

问答节点自动发现并注入，无需改其他文件。

---

## 技术栈

| 层 | 技术 |
|---|---|
| Agent 框架 | LangGraph + LangChain |
| LLM | 本地模型（Qwen3）/ 任意 OpenAI-compatible API / Google Gemini |
| 向量检索 | ChromaDB + HuggingFace Embeddings + BM25 混合 |
| Web UI | Streamlit |
| 持久化 | SQLite（会话历史 + LangGraph checkpoint） |
| 容器运行时 | Singularity / Apptainer |
| 流水线引擎 | Nextflow（nfcore）+ 直接 Singularity 调用（local） |
| 文件下载 | 后台 HTTP 服务器（流式，无 base64 内存开销） |

---

## 贡献

欢迎提 Issue 或 Pull Request。
