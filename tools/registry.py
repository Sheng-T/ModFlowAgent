from tools.toolchain.dorado.validator import dorado
from tools.toolchain.samtools.validator import samtools
from tools.workflow.validator import nextflow
from tools.toolchain.command_builder import build_shell_args
from tools.workflow.command_builder import build_nfcore_command


TOOL_REGISTRY = {
    "dorado": dorado,
    "samtools": samtools,
    "nextflow": nextflow,
}

COMMAND_REGISTRY = {
    "dorado": build_shell_args,
    "samtools": build_shell_args,
    "nextflow": build_nfcore_command,
}
