"""
Central registry of all supported workflows — both nf-core and local.

Adding a new workflow:
  1. Call register(WorkflowSpec(...)) at the bottom of this file.
  2. For nfcore: ensure the pipeline is listed in configs/workflow_config.py SUPPORTED_PIPELINES.
  3. For local:  add per-tool Singularity images to the appropriate image directory.
  4. (Optional) add a prereq form to static/workflow/workflow_prereqs.json.
  5. (Optional) add a deterministic step builder to tools/workflow/steps/{name}.py.
  6. (Optional) add a result analyzer to tools/analyzers/workflow/{name}.py and register it.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

WorkflowType = Literal["nfcore", "local"]


@dataclass
class WorkflowSpec:
    name: str
    display_name: str
    type: WorkflowType
    description: str
    recommended_for: str
    molecule: str = ""
    modification: str = ""
    input_formats: list[str] = field(default_factory=list)
    # nfcore only
    pipeline_id: str = ""
    # local only
    steps: list[str] = field(default_factory=list)
    step_tools: list[str] = field(default_factory=list)


_REGISTRY: dict[str, WorkflowSpec] = {}


def register(spec: WorkflowSpec) -> None:
    _REGISTRY[spec.name] = spec


def get(name: str) -> WorkflowSpec | None:
    return _REGISTRY.get(name)


def all_specs() -> list[WorkflowSpec]:
    return list(_REGISTRY.values())


def all_names() -> set[str]:
    return set(_REGISTRY.keys())


def nfcore_names() -> list[str]:
    return [s.name for s in _REGISTRY.values() if s.type == "nfcore"]


def local_names() -> list[str]:
    return [s.name for s in _REGISTRY.values() if s.type == "local"]


# ── nf-core workflows ──────────────────────────────────────────────────────────

register(WorkflowSpec(
    name="methylong",
    display_name="methylong (nf-core)",
    type="nfcore",
    pipeline_id="methylong",
    description=(
        "Complete ONT/PacBio HiFi DNA methylation & Fiber-seq pipeline: "
        "basecalling → alignment → modification calling (5mC/5hmC/m6A) → "
        "SNV calling → haplotype phasing → DMR calling → HTML QC reports. "
        "Supports Fiber-seq (6mA accessibility, nucleosome/MSP annotation) "
        "for both ONT and PacBio platforms."
    ),
    recommended_for=(
        "DNA methylation analysis (5mC, 5hmC, CpG) from ONT or PacBio HiFi long reads. "
        "Also the recommended pipeline for Fiber-seq (6mA accessibility, nucleosome positioning, "
        "MSP analysis) — use --fiberseq flag. "
        "Production-grade: multi-sample, full provenance, reproducible QC reports."
    ),
    molecule="DNA",
    modification="5mCpG / 5hmCpG / 6mA (Fiber-seq)",
    input_formats=["pod5", "bam"],
))

# ── local workflows ────────────────────────────────────────────────────────────
# Each local workflow resolves models at runtime via tools/workflow/model_map.py,
# so adding a new modification type only requires editing model_map.py.

register(WorkflowSpec(
    name="ont_rna",
    display_name="ONT RNA Modification (local)",
    type="local",
    description=(
        "Generic ONT direct-RNA modification detection via per-tool Singularity images. "
        "Supports m6A, pseU, inosine, and all RNA004-compatible modifications. "
        "Steps: dorado download → basecall → samtools sort/index "
        "→ modkit extract [→ modkit pileup if reference provided]."
    ),
    recommended_for=(
        "ONT direct-RNA sequencing data (RNA004 kit) — detects any RNA base modification "
        "at single-read and site level. Modification type is selectable (default: m6A)."
    ),
    molecule="RNA",
    modification="m6A / pseU / inosine / all",
    input_formats=["pod5", "fast5"],
    steps=["dorado_download", "dorado_basecaller", "samtools_sort",
           "samtools_index", "samtools_faidx", "modkit_pileup", "modkit_extract"],
    step_tools=["dorado", "dorado", "samtools", "samtools", "samtools", "modkit", "modkit"],
))

register(WorkflowSpec(
    name="ont_dna",
    display_name="ONT DNA Modification (local)",
    type="local",
    description=(
        "Generic ONT DNA modification detection via per-tool Singularity images. "
        "Supports 5mCG, 5hmCG, 6mA, and other DNA modifications from ONT pod5/BAM input. "
        "Steps: dorado basecall → samtools sort/index → modkit pileup + extract."
    ),
    recommended_for=(
        "Quick single-sample ONT DNA modification analysis without nf-core overhead. "
        "Modification type is selectable (default: 5mCG). "
        "ONT platform ONLY — does NOT support PacBio HiFi input. "
        "Does NOT support Fiber-seq (use methylong for Fiber-seq or PacBio analysis). "
        "Use methylong for multi-sample or production workflows."
    ),
    molecule="DNA",
    modification="5mCpG / 5hmCpG / 6mA / all",
    input_formats=["pod5", "bam"],
    steps=["dorado_download", "dorado_basecaller", "samtools_sort", "samtools_index",
           "samtools_faidx", "modkit_pileup", "modkit_extract"],
    step_tools=["dorado", "dorado", "samtools", "samtools", "samtools", "modkit", "modkit"],
))
