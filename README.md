<div align="center">

# 🧬 Bio-Agent

**面向 HPC 集群的生物信息学 AI 智能体**

基于 LangGraph 构建，支持自然语言驱动工具调用、Nextflow 流水线编排与 RAG 增强问答

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://python.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2+-1C3C3C?logo=langchain&logoColor=white)](https://github.com/langchain-ai/langgraph)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.x-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

[功能特性](#-功能特性) · [快速开始](#-快速开始) · [架构设计](#-架构设计) · [项目结构](#-项目结构)

</div>

---

## ✨ 功能特性

| 功能 | 说明 |
|---|---|
| 🤖 **意图路由** | 自动识别用户输入，分流至工具调用 / Workflow 流水线 / 知识问答 / 无关拒答 |
| 🔧 **工具链调用** | 支持 `dorado`（ONT basecall）、`samtools`、`modkit`、`fastqc`，LLM 自动生成参数，通过 Singularity 容器执行 |
| 🔬 **Workflow 编排** | 对接本地 Nextflow 流水线（`methylong`），自动生成 samplesheet，自然语言配置参数 |
| 🧠 **RAG 增强问答** | 混合检索（BM25 + ChromaDB）工具文档，结合实时网络搜索回答生信领域问题 |
| 👤 **Human-in-the-Loop** | 执行前自动暂停，展示完整命令（含前置文件写入），支持确认 / 修改 / 取消，二次确认防误触 |
| 💾 **持久化会话** | 多用户 + 多会话隔离，SQLite 存储对话历史与 LangGraph checkpoint，用户文件按 uid/session 独立存储 |
| 🌐 **多语言 UI** | 界面支持中文 / English 切换，语言偏好按用户持久化 |
| 📊 **结果分析** | 执行完成后自动分析输出文件（BAM flagstat/stats），生成 QC 图表并展示报告 |

---

## 🚀 快速开始

### 环境要求

- Python 3.10+
- Singularity / Apptainer（工具链容器运行时）
- Nextflow 23+（Workflow 模式）
- matplotlib（结果图表，`pip install matplotlib`）

### 安装

```bash
git clone https://github.com/yourname/bio-agent.git
cd bio-agent
pip install -r requirements.txt
```

### 配置

```bash
configs/
├── model_config.py      # LLM 模型路径 / API 设置
├── path_config.py       # 数据目录、镜像路径（image_store、user_data_root 等）
├── rag_config.py        # RAG 文档自动发现、向量库缓存目录
└── workflow_config.py   # 支持的 Nextflow pipeline 列表
```

主要路径配置（`configs/path_config.py`）：

```python
IMAGE_PATH = {
    'image_store': "~/singularity_image",   # Singularity 镜像目录，子目录按工具名组织
}
DATA_PATH = {
    "dorado": {'base_data_dir': "~/agent_data", 'dorado_models': "~/tools/dorado_model/"},
    "workflow": {"base_data_dir": "~/agent_data"},
}
```

### 启动 Web UI

```bash
streamlit run ui/app_ui.py --server.address 0.0.0.0 --server.port 8501
```

---

## 🏗️ 架构设计

Bio-Agent 以 **LangGraph** 为核心，将推理过程拆分为可观测节点图：

```
用户输入
   │
   ▼
[router] ── 意图分类 ─────────────────────────────┐
   │                                              │
   ▼ 工具 / 流水线                            ▼ 问答
[tools_selector]                           [llm_answer]
   │
   ▼
[rag] → [planner]
             │
      ┌──────┴──────────────┐
      ▼                     ▼
[param_generator]     [rag_pipeline]        ← Workflow 专用
                            │
                      [prereq_generator]    ← 自动生成 samplesheet
                            │
                      [param_generator]
                            │
                      [human_reviewer] ── ⏸️ interrupt_before ── 等待用户确认
                            │
                      [executor] → [summarizer]
```

### 关键设计

- **interrupt_before=["executor"]**：执行前强制暂停，用户审查命令（含 samplesheet 预览）后二次确认才放行
- **run_dir 隔离**：每次运行在 `session_dir/run_{id}_{timestamp}/` 下创建独立目录，前置文件、运行结果、分析图表均归档在此，不覆盖用户上传文件
- **pending_commands 复用**：review 节点构建命令时一次性确定所有路径（含时间戳），executor 直接复用，避免重复生成导致路径不一致
- **Singularity 封装**：工具链命令自动提取绑定路径，透明包裹进 `singularity exec`；Nextflow 流水线由宿主机直接执行，内部通过 `-profile singularity` 管理容器

---

## 📁 项目结构

```
bio-agent/
├── agent_graph/
│   ├── graph.py                  # LangGraph 图定义（节点 + 边 + 编译）
│   ├── state.py                  # AgentState 定义
│   ├── nodes/
│   │   ├── router/               # 意图分类、会话重置
│   │   ├── toolchain/            # 工具选择、RAG、Planner、参数生成
│   │   ├── workflows/            # Pipeline 选择、RAG、前置文件生成
│   │   └── execution/            # 命令审查、执行、结果总结
│   └── prompts/                  # LLM prompt 模板
├── tools/
│   ├── toolchain/
│   │   ├── dorado/               # dorado validator & command builder
│   │   ├── samtools/             # samtools validator
│   │   ├── modkit/               # modkit validator
│   │   └── fastqc/               # fastqc validator
│   ├── workflow/
│   │   └── methylong/            # methylong command builder
│   └── analyzers/                # 输出文件分析（BAM QC、甲基化等）
├── runtime/
│   ├── executor.py               # 命令执行（subprocess）
│   └── env_wrapper.py            # Singularity 封装 + 路径自动绑定
├── storage/
│   ├── checkpointer.py           # SqliteSaver 单例
│   ├── session_store.py          # 用户 / 会话 / 消息持久化
│   ├── file_manager.py           # 用户文件管理（配额、归档）
│   └── rag_retriever.py          # BM25 + ChromaDB 混合检索
├── configs/                      # 所有配置集中管理
├── static/
│   ├── dorado/                   # dorado 工具文档 + args schema
│   ├── samtools/                 # samtools 工具文档 + args schema
│   ├── modkit/                   # modkit 工具文档 + args schema
│   ├── fastqc/                   # fastqc 工具文档 + args schema
│   └── workflow/                 # workflow pipeline 文档 + prereqs 配置
├── utils/
│   ├── search_utils.py           # 网络搜索 + 网页爬取 + RAG 增强
│   ├── user_context.py           # 线程本地 session/run_dir 上下文
│   ├── i18n.py                   # 国际化 _() 函数
│   └── ui_logger.py              # 节点日志 → Streamlit 队列桥接
├── locales/                      # i18n 语言文件（zh_CN / en_US）
├── ui/
│   ├── app_ui.py                 # Streamlit 主入口
│   ├── chat.py                   # 聊天区域、审查面板、执行流程
│   ├── sidebar.py                # 会话管理、文件上传、工具能力一览
│   └── login.py                  # 用户登录
└── main.py                       # CLI 入口
```

---

## 🛠️ 技术栈

| 层 | 技术 |
|---|---|
| Agent 框架 | LangGraph + LangChain |
| LLM | 本地部署模型（Qwen3 等）/ 远程 API |
| 向量检索 | ChromaDB + HuggingFace Embeddings + BM25 混合 |
| Web UI | Streamlit |
| 持久化 | SQLite（会话历史 + LangGraph checkpoint） |
| 容器运行时 | Singularity / Apptainer |
| 流水线引擎 | Nextflow + 本地 pipeline |

---

## 📖 使用示例

**生信知识问答**
```
>>> ONT 测序的甲基化检测原理是什么？
```
Agent 触发 RAG 检索 + 网络搜索，综合回答。

**工具调用**
```
>>> 用 dorado basecaller 对我上传的 pod5 文件进行 basecall，模型用 sup
```
Agent 选择 dorado → RAG 检索参数文档 → 生成命令 → 展示审查 → 确认后在 Singularity 容器内执行 → 自动分析 BAM 输出并生成 QC 报告。

**Nextflow 流水线**
```
>>> 用 methylong 流水线分析我上传的 BAM 文件和参考基因组
```
Agent 选择 methylong pipeline → LLM 根据上传文件生成 samplesheet.csv → 展示 samplesheet 预览和完整命令 → 用户二次确认后写入 samplesheet 并执行 Nextflow。

---

## 🤝 贡献

欢迎提交 Issue 或 Pull Request。
