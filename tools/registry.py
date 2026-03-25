from tools.toolchain.dorado.validator import dorado
from tools.toolchain.samtools.validator import samtools
from tools.workflow.methylong.validator import methylong
from tools.toolchain.command_builder import build_shell_args
from tools.workflow.command_builder import build_workflow_command


TOOL_REGISTRY = {
    "dorado": dorado,
    "samtools": samtools,
}

WORKFLOW_REGISTRY = {
    "methylong": methylong,  # 以后加 rnaseq、sarek 也在这里注册
}

# COMMAND_REGISTRY = {
#     "dorado": build_shell_args,
#     "samtools": build_shell_args,
#     "workflow": build_workflow_command,
# }

COMMAND_REGISTRY = {
    "workflow": build_workflow_command,
}
