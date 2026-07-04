def get_qa_hints(lang: str = "en_US") -> str:
    if lang == "en_US":
        return (
            "CRITICAL: ont_rna is NOT a standalone CLI tool. Do NOT generate any shell command like "
            "'ont_rna --input ...' — no such command exists. "
            "ont_rna is a multi-step workflow executed entirely by the agent. "
            "To run it, the user simply describes their data in the chat (e.g. 'I have ONT RNA POD5 data, detect m6A') "
            "and the agent handles everything automatically.\n"
            "Workflow steps (run automatically in sequence):\n"
            "  1. dorado download — downloads the RNA basecall model and modification model\n"
            "  2. dorado basecaller — basecalls POD5 and calls modifications (e.g. m6A)\n"
            "  3. samtools sort — coordinate-sorts the output BAM\n"
            "  4. samtools index — indexes the sorted BAM\n"
            "  5. modkit extract — extracts per-read modification calls (always runs)\n"
            "  6. modkit pileup — site-level bedMethyl output (only when reference is provided)\n"
            "Input must be POD5 or modBAM — FASTQ is not supported. "
            "A reference transcriptome/genome is optional; without it modkit pileup is skipped.\n"
            "Kit note: RNA004 chemistry is recommended for m6A detection. If the user mentions RNA002 or DNA kits, "
            "warn that modification accuracy may be lower."
        )
    return (
        "重要提示：ont_rna 不是独立的命令行工具，不要生成任何类似 'ont_rna --input ...' 的命令，该命令不存在。"
        "ont_rna 是由 Agent 自动执行的多步骤工作流，用户只需在对话框中描述数据（如'我有 ONT RNA POD5 数据，检测 m6A'），"
        "Agent 会自动完成所有步骤。\n"
        "工作流步骤（按序自动执行）：\n"
        "  1. dorado download — 下载 RNA basecall 模型和修饰模型\n"
        "  2. dorado basecaller — 对 POD5 进行 basecall 并调用修饰（如 m6A）\n"
        "  3. samtools sort — 对输出 BAM 按坐标排序\n"
        "  4. samtools index — 索引排序后的 BAM\n"
        "  5. modkit extract — 提取每条 read 的修饰调用（始终运行）\n"
        "  6. modkit pileup — 输出位点级 bedMethyl（仅在提供参考序列时运行）\n"
        "输入必须是 POD5 或 modBAM，不支持 FASTQ。参考转录本/基因组可选，无参考时跳过 modkit pileup。\n"
        "Kit 说明：m6A 检测建议使用 RNA004 化学试剂盒；若用户提到 RNA002 或 DNA 试剂盒，应提示修饰检测精度可能偏低。"
    )
