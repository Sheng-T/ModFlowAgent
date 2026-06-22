def get_qa_hints(lang: str = "en_US") -> str:
    if lang == "en_US":
        return (
            "For ONT DNA modification workflow questions: this local workflow runs Dorado basecalling "
            "(if POD5 input), then modkit pileup (if reference provided) or modkit extract (read-level only). "
            "Input must be POD5 or modBAM — FASTQ is not supported. "
            "A reference genome is optional; without it only read-level modification calls are produced.\n"
            "For IGV visualization: load the aligned BAM + BAI, plus the bedMethyl (.bed.gz + .tbi) for site-level tracks."
        )
    return (
        "ONT DNA 修饰工作流说明：该本地流程支持 Dorado basecall（POD5 输入时自动触发），"
        "有参考基因组时运行 modkit pileup 输出位点级 bedMethyl，无参考时仅输出读段级 modkit extract 结果。"
        "输入必须是 POD5 或 modBAM，不支持 FASTQ。\n"
        "IGV 可视化：加载比对后的 BAM + BAI，加上 bedMethyl（.bed.gz + .tbi）作为甲基化轨道。"
    )
