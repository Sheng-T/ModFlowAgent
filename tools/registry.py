from dataclasses import dataclass
from typing import Callable, Optional, Dict

from tools.toolchain.dorado.validator   import dorado
from tools.toolchain.samtools.validator import samtools
from tools.toolchain.modkit.validator   import modkit
from tools.toolchain.fastqc.validator   import fastqc
from tools.workflow.nf.methylong.validator import methylong
from tools.toolchain.command_builder    import build_shell_args
from tools.workflow.command_builder     import build_workflow_command


@dataclass
class ToolSpec:
    name: str
    validator: Optional[Callable] = None
    command_builder: Optional[Callable] = None
    description: str = ""


TOOL_REGISTRY = {
    "dorado":   dorado,
    "samtools": samtools,
    "modkit":   modkit,
    "fastqc":   fastqc,
}


# 新增元数据驱动的工具规格表（向后兼容）
TOOL_SPECS: Dict[str, ToolSpec] = {
    "dorado":   ToolSpec(name="dorado",   validator=dorado,   command_builder=build_shell_args, description="dorado basecaller"),
    "samtools": ToolSpec(name="samtools", validator=samtools, command_builder=build_shell_args, description="samtools suite"),
    "modkit":   ToolSpec(name="modkit",   validator=modkit,   command_builder=build_shell_args, description="modkit base modification analysis"),
    "fastqc":   ToolSpec(name="fastqc",   validator=fastqc,   command_builder=build_shell_args, description="FastQC quality control"),
    "workflow": ToolSpec(name="workflow", validator=None,     command_builder=build_workflow_command, description="pipeline/workflow runner"),
}


WORKFLOW_REGISTRY = {
    "methylong": methylong,  #
}


COMMAND_REGISTRY = {
    "workflow": build_workflow_command,
}


__all__ = ["TOOL_REGISTRY", "TOOL_SPECS", "WORKFLOW_REGISTRY", "COMMAND_REGISTRY", "ToolSpec"]
