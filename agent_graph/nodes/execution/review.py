from agent_graph.prompts.review_prompts import build_human_review_feedback_prompt
from agent_graph.state import AgentState
from configs.path_config import DATA_PATH
from tools.registry import TOOL_REGISTRY, COMMAND_REGISTRY
from tools.toolchain.command_builder import build_shell_args
from utils.llm_utils import get_llm_instance


def validate_tool_calls_node(state: AgentState) -> AgentState:
    tool_calls = state.get("tool_calls", [])
    user_input = state.get("input", "").lower()
    if not tool_calls:
        return state

    for _, call in enumerate(tool_calls):
        tool_name = call.get("tool_name", "")
        tool_args = call.get("tool_args", {})
        kwargs = tool_args.get("kwargs", {})
        pos_args = tool_args.get("pos_args", [])

        if "basecall" in tool_name:
            current_model = pos_args[0] if len(pos_args) > 0 else ""
            if current_model in ["hac", "sup", "fast", ""] or len(current_model) < 10:
                if "dna" in user_input:
                    pos_args[0] = "dna_r10.4.1_e8.2_400bps_sup@v5.1.0"
                elif "rna002" in user_input:
                    pos_args[0] = "rna002_70bps_hac@v3.0.0"
                else:
                    pos_args[0] = "rna004_130bps_sup@v5.2.0"
                print(f"[Validator] 修正 model -> {pos_args[0]}")

            mod = kwargs.get("modified-bases")
            if mod and mod == "m6A_DRACH":
                kwargs["modified-bases-models"] = f"{pos_args[0]}_m6A_DRACH@v1"

        elif "samtools_sort" in tool_name:
            if "sort" in tool_name and not kwargs.get("o"):
                kwargs["o"] = "sorted_output.bam"
                print("[Validator] 专家校验：自动补全 Samtools 排序输出文件名")

        tool_args["kwargs"] = kwargs
        tool_args["pos_args"] = pos_args
        call["tool_args"] = tool_args

    state["tool_calls"] = tool_calls
    return state


def review_execution_plan_node(state: AgentState) -> dict:
    tool_calls = state.get("tool_calls", [])
    history = state.get("chat_history", [])

    print("\n" + "=" * 30 + " 待执行任务确认 " + "=" * 30)
    for i, call in enumerate(tool_calls):
        tool_name = call["tool_name"]
        tool_args = call["tool_args"]

        tool_name_array = tool_name.split("_")
        base_name = tool_name_array[0]
        last_sub_command = tool_name_array[-1]
        sub_cmd_str = " ".join(tool_name_array[1:])

        print(f"\n步骤 {i + 1}: {tool_name}")
        print(f"\n结构化参数: {tool_args}")

        # verify_func = getattr(tools_verify, base_name, None)
        verify_func = TOOL_REGISTRY.get(base_name)
        cmd_builder = COMMAND_REGISTRY.get(base_name)
        if verify_func:
            raw_cmd = verify_func(last_sub_command, sub_cmd_str, tool_args, DATA_PATH[base_name])
        elif cmd_builder:
            raw_cmd = cmd_builder(sub_cmd_str, tool_args, DATA_PATH[base_name])
        else:
            binary_name = f"{base_name} {sub_cmd_str}".strip()
            arg_str = build_shell_args(tool_args)
            raw_cmd = f"{binary_name} {arg_str}"

        print("实际执行命令：")
        print(f"  {raw_cmd}")

    print("\n" + "=" * 76)
    user_input = input("\n[确认确认] 是否执行上述命令？(y/n) 或输入修改意见: ").strip()

    if user_input.lower() == "y":
        history.append({"role": "user", "content": "确认执行，无需修改。"})
        return {
            "next_node": "executor",
            "user_approval": True,
            "user_feedback": "",
            "chat_history": history,
        }

    if user_input.lower() == "exit":
        history.append({"role": "user", "content": "退出当前任务。"})
        return {"next_node": "end_node", "chat_history": history}

    history.append({"role": "user", "content": f"用户修改意见：{user_input}"})
    identified_tools = state.get("identified_tools", [])

    llm = get_llm_instance(is_planner=True)
    prompt = build_human_review_feedback_prompt(user_input, tool_calls, identified_tools)
    raw_decision = llm.invoke(prompt)
    decision_text = raw_decision.content if hasattr(raw_decision, "content") else str(raw_decision)
    decision = decision_text.replace("'", "").replace('"', "").replace(".", "").strip().upper()
    if "nextflow" in identified_tools:
        mapping = {
            "SELECTOR": "tools_selector",
            "REPLAN": "nfcore_rag",
            "REPARAM": "nfcore_param_generator",
        }
    else:
        mapping = {"SELECTOR": "tools_selector", "REPLAN": "rag", "REPARAM": "param_generator"}

    return {
        "next_node": mapping.get(decision, "param_generator"),
        "user_feedback": user_input,
        "chat_history": history,
    }
