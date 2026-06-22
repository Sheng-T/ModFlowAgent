import re as _re

from agent_graph.state import AgentState, EMPTY_STATE
from utils.llm_utils import get_llm_instance
from utils.lang_utils import get_lang


_NOT_SUPPORTED_HINTS = {
    "fastq": (
        "NOT SUPPORTED on this platform: FASTQ input format. "
        "FASTQ files contain only base sequences — they lack the raw signal data and MM/ML base "
        "modification tags required for methylation/modification detection. "
        "Please provide POD5 or FAST5 (raw signal) for basecalling + modification calling, "
        "or a modBAM (BAM with MM/ML tags) if the data has already been basecalled."
    ),
    "pacbio_dorado": (
        "NOT SUPPORTED on this platform: PacBio data cannot be processed with Dorado. "
        "Dorado is an ONT-only basecaller and does not accept PacBio/HiFi input. "
        "For PacBio HiFi CpG methylation, use the methylong pipeline directly (HiFi BAM already contains kinetics — no basecalling step needed). "
        "For standalone PacBio 5mC calling outside this platform, tools such as jasmine (PacBio's native 5mC caller) "
        "or ccsmeth are commonly used."
    ),
    "pacbio_rna": (
        "NOT SUPPORTED on this platform: PacBio + RNA modification analysis. "
        "No pipeline here handles PacBio/HiFi RNA m6A or any RNA modification. "
        "For RNA modification analysis, ONT direct-RNA sequencing (RNA004 kit) is required — "
        "use the ont_rna workflow. "
        "methylong is for DNA methylation only (5mC/5hmC/Fiber-seq); it does NOT support RNA."
    ),
}


def reset_session_state_node(state: AgentState) -> AgentState:
    user_input = state["input"]
    print(f"\n[Router] Analyzing user input: '{user_input[:30]}...'")

    history = state.get("chat_history", [])
    # user_choice 必须保留，否则 classify_intent_route 和 select_tools_node 里的模式判断会失效
    user_choice = state.get("user_choice")
    # Preserve local_prereq_params tagged with workflow name so re-running the
    # same workflow skips the slow LLM inference step.  The planner clears them
    # if a different workflow is selected (see plan_tool_steps_node).
    # selected_workflow / workflow_type are intentionally NOT preserved so that
    # every new user message goes through planner Case B (LLM selection with
    # history context).  This prevents a prior methylong session from silently
    # hijacking unrelated requests like "run all workflows on my data".
    preserved_prereq = state.get("local_prereq_params") or {}

    # Detect unsupported combinations; attach a targeted hint for the answer node.
    lower = user_input.lower()
    _pacbio_kw = ["pacbio", "hifi", " pb ", "pb-"]
    router_hint = ""
    if any(k in lower for k in ["fastq", ".fq", "fq.gz", "fastq.gz"]):
        router_hint = _NOT_SUPPORTED_HINTS["fastq"]
    elif any(k in lower for k in _pacbio_kw) and "dorado" in lower:
        router_hint = _NOT_SUPPORTED_HINTS["pacbio_dorado"]
    elif any(k in lower for k in _pacbio_kw) and " rna " in f" {lower} ":
        router_hint = _NOT_SUPPORTED_HINTS["pacbio_rna"]

    # Detect DNA/RNA mismatch: user says "dna" but path or reference suggests RNA data.
    # Only warn — do not block, the user may know what they're doing.
    _data_warning = _detect_data_type_mismatch(lower)
    if _data_warning:
        history = list(history) + [{"role": "assistant", "content": _data_warning}]

    return {**EMPTY_STATE, "input": user_input, "chat_history": history,
            "user_choice": user_choice,
            "local_prereq_params": preserved_prereq,
            "router_hint": router_hint}


# ── RNA/DNA mismatch detection ────────────────────────────────────────────────

# ONT RNA kit identifiers and transcript reference patterns that strongly imply RNA data
_RNA_PATH_PATTERNS  = [r"rna00[0-9]", r"/rna[_\-/]", r"[_\-/]rna[_\-/]", r"directrna", r"direct.rna"]
_RNA_REF_PATTERNS   = [r"\.transcripts?\.", r"transcriptome", r"cdna"]

def _detect_data_type_mismatch(lower: str) -> str:
    """
    Return a warning message if the user says 'dna' but the input text contains
    path or reference patterns strongly associated with RNA data, or vice versa.
    Returns empty string when no mismatch is detected.
    """
    lang = get_lang()
    user_says_dna = _re.search(r"\b(dna|ont[_\- ]dna|ont_dna)\b", lower) is not None

    if not user_says_dna:
        return ""  # No declared type or already RNA — nothing to check

    rna_path_hit  = any(_re.search(p, lower) for p in _RNA_PATH_PATTERNS)
    rna_ref_hit   = any(_re.search(p, lower) for p in _RNA_REF_PATTERNS)

    if not (rna_path_hit or rna_ref_hit):
        return ""

    reasons = []
    if rna_path_hit:
        reasons.append(
            "the data path appears to reference an ONT RNA kit (e.g. RNA004)"
            if lang == "en_US" else
            "数据路径中包含 ONT RNA 测序试剂盒标识（如 RNA004）"
        )
    if rna_ref_hit:
        reasons.append(
            "the reference file looks like a transcript/transcriptome FASTA (used for RNA analysis)"
            if lang == "en_US" else
            "参考序列文件名含有转录组特征（如 .transcripts.、transcriptome），通常用于 RNA 分析"
        )

    reason_str = " and ".join(reasons) if lang == "en_US" else "；".join(reasons)

    if lang == "en_US":
        return (
            f"**⚠ Possible DNA/RNA mismatch detected:** You requested a DNA analysis, but {reason_str}. "
            "If your data is from ONT direct RNA sequencing, please use the **ont_rna** workflow instead. "
            "If this is intentional (e.g. your folder happens to be named RNA004 but contains DNA data), "
            "you can safely ignore this message and proceed."
        )
    return (
        f"**⚠ 检测到可能的 DNA/RNA 数据类型不匹配：**您请求了 DNA 分析，但{reason_str}。"
        "如果您的数据来自 ONT 直接 RNA 测序，请改用 **ont_rna** 工作流。"
        "如果这是预期行为（例如文件夹名称恰好含有 RNA 字样，但实际是 DNA 数据），请忽略此提示继续操作。"
    )


def classify_intent_route(state: AgentState) -> str:
    user_input = state["input"].lower()

    # Intercept inputs that should go directly to answer regardless of user_choice
    _fastq_kw = ["fastq", ".fq", "fq.gz", "fastq.gz"]
    if any(kw in user_input for kw in _fastq_kw):
        print("[Router] FASTQ input detected — routing to answer (not supported)")
        return "route_to_answer"

    _pacbio_kw = ["pacbio", "hifi", " pb ", "pb-"]
    _dorado_kw = ["dorado"]
    if any(k in user_input for k in _pacbio_kw) and any(k in user_input for k in _dorado_kw):
        print("[Router] PacBio + Dorado detected — routing to answer")
        return "route_to_answer"

    # PacBio + RNA: no supported pipeline exists for this combination.
    # Intercept early to avoid an infinite workflow-selection loop.
    _rna_word = " rna " in f" {user_input} "   # word-boundary match for "rna"
    if any(k in user_input for k in _pacbio_kw) and _rna_word:
        print("[Router] PacBio + RNA detected — not supported, routing to answer")
        return "route_to_answer"

    # 检查是否有来自UI的显式路由选择
    if "user_choice" in state and state["user_choice"]:
        choice = state["user_choice"]
        print(f"[Router] User selected mode: {choice}")
        if choice == "answer":
            return "route_to_answer"
        elif choice == "tools":
            return "route_to_tools"
        elif choice == "workflow":
            return "route_to_tools"   # workflow 也走 tools 路由，planner 负责解析具体类型
        # auto: 继续走下方 LLM 判断

    # 1) Direct keyword routing for deterministic behavior
    _workflow_kw = ["nextflow", "nf-core", "workflow", "pipeline", "流水线", "流程",
                    "methylong", "rnaseq", "methylseq", "sarek", "ampliseq", "mag", "taxprofiler",
                    "fiber-seq", "fiberseq", "fiber seq", "nucleosome", "核小体"]
    if any(k in user_input for k in _workflow_kw):
        return "route_to_tools"  # workflow 也走 tools 路由
    if any(k in user_input for k in ["dorado", "samtools", "basecall", "sort", "index"]):
        return "route_to_tools"

    # 2) 如果没有显式选择，使用LLM判断
    print("[Router] Calling LLM for intent classification...")
    llm = get_llm_instance(is_planner=True, temperature=0.2)

    classification = llm.invoke(
        f"You are a bioinformatics assistant. Classify the user's intent into one of three categories:\n"
        f"- 'tools': user wants to run an analysis, execute a tool or pipeline, or process sequencing data.\n"
        f"- 'answer': user is asking about a biological concept, bioinformatics method, or technical principle.\n"
        f"- 'irrelevant': user is chatting, off-topic, or saying something completely unrelated to science.\n"
        f"Reply with exactly one word (no punctuation): tools / answer / irrelevant\n"
        f"User input: {user_input}"
    )

    import re
    raw = classification if isinstance(classification, str) else classification.content
    clean_intent = re.sub(r"[^a-z]", "", raw.strip().lower())

    mapping = {
        "tools": "tools",
        "tool": "tools",
        "workflow": "tools",  # workflow也走tools
        "llmanswer": "answer",
        "answer": "answer",
        "irrelevant": "irrelevant",
    }
    final_intent = mapping.get(clean_intent, "answer")
    return f"route_to_{final_intent}"


