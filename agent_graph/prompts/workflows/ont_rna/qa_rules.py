def get_qa_hints(lang: str = "en_US") -> str:
    if lang == "en_US":
        return (
            "For ONT RNA modification workflow questions: this local workflow detects RNA base modifications "
            "(e.g. m6A) from ONT direct-RNA or cDNA POD5/modBAM data using Dorado + modkit. "
            "Input must be POD5 or modBAM — FASTQ is not supported. "
            "A reference transcriptome or genome is optional; without it only read-level calls are produced.\n"
            "Kit note: RNA004 chemistry is recommended for m6A detection. If the user mentions RNA002 or DNA kits, "
            "warn that modification accuracy may be lower."
        )
    return (
        "ONT RNA 修饰工作流说明：该本地流程检测 RNA 碱基修饰（如 m6A），"
        "使用 Dorado + modkit 处理直接 RNA 或 cDNA 的 POD5/modBAM 数据。"
        "输入必须是 POD5 或 modBAM，不支持 FASTQ。"
        "有参考转录本或基因组时运行 modkit pileup，否则仅输出读段级结果。\n"
        "Kit 说明：m6A 检测建议使用 RNA004 化学试剂盒；若用户提到 RNA002 或 DNA 试剂盒，"
        "应提示修饰检测精度可能偏低。"
    )
