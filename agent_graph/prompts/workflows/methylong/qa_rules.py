"""
methylong-specific Q&A guidance hints.
Injected into the general QA prompt when methylong context is active.
"""


def get_qa_hints(lang: str = "en_US") -> str:
    if lang == "en_US":
        return (
            "For FASTQ input questions: explain that FASTQ files are NOT supported. "
            "methylong requires either a modBAM (BAM basecalled by Dorado with a modification model, "
            "containing MM/ML tags) or raw pod5 files. Standard FASTQ files lack the MM/ML modification "
            "tags needed for methylation calling.\n"
            "For PacBio + Dorado questions: explain that Dorado is an ONT-specific basecaller and cannot "
            "process PacBio data. PacBio methylation calling uses pb-CpG-tools (pileup), which methylong "
            "handles automatically when method=pacbio. The user should just provide their PacBio BAM "
            "without specifying Dorado.\n"
            "For jasmine vs ccsmeth questions: both are PacBio HiFi methylation callers used in the "
            "methylong PacBio mode. jasmine is the newer, more accurate model-based caller that runs "
            "directly on PacBio kinetics data and is generally preferred for CpG methylation. ccsmeth "
            "is an earlier deep-learning approach that also works on CCS reads; it may still be preferred "
            "for certain legacy datasets or when jasmine is unavailable. methylong selects between them "
            "automatically based on configuration.\n"
            "For IGV visualization questions: recommend loading the aligned BAM + BAI index, plus "
            "bedMethyl (.bed.gz + .tbi) or bedGraph files for methylation tracks. "
            "Do not suggest re-running the pipeline."
        )
    return (
        "如果用户提到 FASTQ 文件：说明 FASTQ 不被支持，methylong 需要 modBAM（由 Dorado + 修饰模型 basecall 的 BAM，"
        "含 MM/ML 标签）或 pod5 文件，普通 FASTQ 缺少甲基化标签。\n"
        "如果用户提到 PacBio + Dorado：说明 Dorado 是 ONT 专属 basecaller，不支持 PacBio 数据；"
        "PacBio 甲基化使用 pb-CpG-tools，methylong 在 method=pacbio 时自动调用，"
        "用户直接提供 PacBio BAM 即可，无需指定 Dorado。\n"
        "如果用户询问 jasmine 与 ccsmeth 的区别：两者都是用于 methylong PacBio 模式的 HiFi 甲基化调用工具。"
        "jasmine 是更新的基于模型的调用工具，直接利用 PacBio kinetics 数据，CpG 甲基化精度更高，通常优先推荐；"
        "ccsmeth 是早期的深度学习方法，同样适用于 CCS reads，在某些老数据集或 jasmine 不可用时仍可选用；"
        "methylong 会根据配置自动选择。\n"
        "IGV 可视化：推荐加载比对后的 BAM + BAI 索引，加上 bedMethyl（.bed.gz + .tbi）或 bedGraph 文件作为甲基化轨道，"
        "不要建议用户重新跑流水线。"
    )
