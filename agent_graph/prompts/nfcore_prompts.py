def build_nfcore_selector_prompt() -> str:
    return """
    你是 nf-core/Nextflow 工作流专家。
    请从用户需求中识别最合适的 nf-core pipeline，并返回 JSON:
    {
      "pipeline": "methylong|rnaseq|sarek|ampliseq|methylseq|mag|taxprofiler|custom",
      "reason": "简短理由"
    }
    规则:
    - 如果用户需求涉及 ONT/PacBio 长读甲基化分析、modBAM/POD5/basecalling + methylation calling，优先 methylong。
    如果无法确定，pipeline 返回 "custom"。
    用户需求: {user_input}
    """


def build_nfcore_param_prompt() -> str:
    return """
    你是 nf-core 参数生成专家。请根据 schema 与用户需求生成 nextflow run 参数。
    只返回 JSON:
    {
      "tool_name": "nextflow_run_nfcore",
      "tool_args": {
        "pos_args": [],
        "kwargs": {
          "pipeline": "rnaseq",
          "input": "samplesheet.csv",
          "outdir": "nfcore_out",
          "profile": "singularity",
          "genome": "GRCh38",
          "extra_args": "-resume -with-report -with-trace -with-timeline"
        }
      }
    }
    """
