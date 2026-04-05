from dataclasses import dataclass
from typing import Callable, Optional, Dict

from tools.toolchain.dorado.validator import dorado
from tools.toolchain.samtools.validator import samtools
from tools.workflow.methylong.validator import methylong
from tools.toolchain.command_builder import build_shell_args
from tools.workflow.command_builder import build_workflow_command


@dataclass
class ToolSpec:
    name: str
    validator: Optional[Callable] = None
    command_builder: Optional[Callable] = None
    description: str = ""


# 兼容旧接口：保留 TOOL_REGISTRY（validator 映射）
TOOL_REGISTRY = {
    "dorado": dorado,
    "samtools": samtools,
}


# 新增元数据驱动的工具规格表（向后兼容）
TOOL_SPECS: Dict[str, ToolSpec] = {
    "dorado": ToolSpec(name="dorado", validator=dorado, command_builder=build_shell_args, description="dorado basecaller"),
    "samtools": ToolSpec(name="samtools", validator=samtools, command_builder=build_shell_args, description="samtools suite"),
    "workflow": ToolSpec(name="workflow", validator=None, command_builder=build_workflow_command, description="pipeline/workflow runner"),
}


WORKFLOW_REGISTRY = {
    "methylong": methylong,  # 以后加 rnaseq、sarek 也在这里注册
}


# 保留 COMMAND_REGISTRY 以兼容现有调用
COMMAND_REGISTRY = {
    "workflow": build_workflow_command,
}


__all__ = ["TOOL_REGISTRY", "TOOL_SPECS", "WORKFLOW_REGISTRY", "COMMAND_REGISTRY", "ToolSpec"]
