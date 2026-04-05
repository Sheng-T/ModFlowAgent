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
| 🤖 **意图路由** | 自动识别用户输入，分流至工具调用 / 知识问答 / 无关拒答 |
| 🔧 **工具链调用** | 支持 `dorado`（ONT basecall）、`samtools` 等生信工具，LLM 自动生成参数 |
| 🔬 **Workflow 编排** | 对接 nf-core 流水线（`methylong` 等），自然语言配置 Nextflow 参数 |
| 🧠 **RAG 增强问答** | 检索工具文档 + 实时搜索（Baidu/DDG/Wikipedia），回答生信领域问题 |
| 👤 **Human-in-the-Loop** | 执行前自动暂停，展示待运行命令，支持确认 / 修改 / 取消 |
| 💾 **持久化会话** | 多用户 + 多会话，SQLite 存储对话历史与 LangGraph checkpoint |
| 🌐 **多语言 UI** | 界面支持中文 / English 切换，语言偏好按用户持久化 |
| ☁️ **SLURM 兼容** | 工具命令通过 Singularity 容器封装；Nextflow 流水线直接提交集群 |

---

## 🚀 快速开始

### 环境要求

- Python 3.10+
- （可选）Singularity / Apptainer（HPC 容器运行时）
- （可选）Nextflow 23+（Workflow 模式）

### 安装

```bash
git clone https://github.com/yourname/bio-agent.git
cd bio-agent
pip install -r requirements.txt
```

### 配置

编辑 `configs/` 下的配置文件：

```bash
configs/
├── model_config.py      # LLM 模型路径 / API 设置
├── path_config.py       # 数据目录、镜像路径
├── runtime_config.py    # 运行环境（local / slurm）
└── workflow_config.py   # Nextflow pipeline 注册
```

### 启动 Web UI

```bash
streamlit run ui/app_ui.py --server.address 0.0.0.0 --server.port 8501
```

### 命令行模式

```bash
python main.py
```

---

## 🏗️ 架构设计

Bio-Agent 以 **LangGraph** 为核心，将 Agent 的推理过程拆分为可观测的节点图：

```
用户输入
   │
   ▼
[router] ── 意图分类 ──────────────────────────┐
   │                                           │
   ▼ 工具/流水线                            ▼ 问答
[tools_selector]                         [llm_answer]
   │
   ▼
[rag] → [planner]
             │
      ┌──────┴──────┐
      ▼             ▼
[param_generator] [rag_pipeline]  ← Workflow 专用
      │
      ▼
[human_reviewer] ── ⏸️ interrupt_before ── 等待用户确认
      │
      ▼
[executor] → [summarizer]
```

### 关键设计

- **interrupt_before=["executor"]**：每次执行前强制暂停，用户可审查命令后再放行
- **MemorySaver / SqliteSaver**：开发用内存 checkpoint，生产用 SQLite 持久化
- **双模 command builder**：工具链走 `build_shell_args` + Singularity 封装；Workflow 走 `build_workflow_command` 直接生成 `nextflow run` 命令

---

## 📁 项目结构

```
bio-agent/
├── agent_graph/
│   ├── graph.py              # LangGraph 图定义（节点 + 边 + 编译）
│   ├── state.py              # AgentState 定义
│   ├── nodes/                # 各节点实现
│   │   ├── router/           # 意图分类、会话重置
│   │   ├── toolchain/        # 工具选择、RAG、参数生成
│   │   └── execution/        # 命令审查、执行、总结
│   └── prompts/              # LLM prompt 模板
├── tools/
│   ├── toolchain/            # dorado、samtools validator & command builder
│   └── workflow/             # Nextflow pipeline validator & command builder
├── runtime/
│   ├── executor.py           # 命令执行（subprocess）
│   └── env_wrapper.py        # Singularity / SLURM 封装
├── storage/
│   ├── checkpointer.py       # SqliteSaver 单例
│   ├── session_store.py      # 用户 / 会话 / 消息持久化
│   └── rag_retriever.py      # BM25 + Vector 混合检索
├── utils/
│   ├── search_utils.py       # 网络搜索 + 网页爬取 + RAG 增强
│   ├── i18n.py               # 国际化 _() 函数
│   └── ui_logger.py          # 节点日志 → Streamlit 队列桥接
├── configs/                  # 所有配置集中管理
├── locales/                  # i18n 语言文件（zh_CN / en_US）
├── ui/
│   └── app_ui.py             # Streamlit 前端
└── main.py                   # CLI 入口
```

---

## 🛠️ 技术栈

| 层 | 技术 |
|---|---|
| Agent 框架 | LangGraph + LangChain |
| LLM | Qwen3 系列（本地部署）/ Gemini（API） |
| 向量检索 | ChromaDB + HuggingFace Embeddings + BM25 混合 |
| Web UI | Streamlit |
| 持久化 | SQLite（会话 + LangGraph checkpoint） |
| 容器运行时 | Singularity / Apptainer |
| 流水线引擎 | Nextflow + nf-core |

---

## 📖 使用示例

**生信知识问答**
```
>>> 生物信息学是什么？
```
Agent 自动触发 RAG 搜索，综合百度百科 / Wikipedia 回答。

**工具调用**
```
>>> 用 dorado 对 /data/pod5 进行 basecall，模型用 sup
```
Agent 选择 dorado → 生成参数 → 展示命令 → 等待确认 → 在 Singularity 容器内执行。

**Nextflow 流水线**
```
>>> 运行 methylong 流水线，输入 samplesheet.csv，参考基因组 hg38.fa
```
Agent 自动生成完整的 `nextflow run nf-core/methylong ...` 命令并提交 SLURM。

---

## 🤝 贡献

欢迎提交 Issue 或 Pull Request。
