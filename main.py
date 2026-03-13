# main.py
import os

# 导入上面的 app 和 AgentState
from agent_graph.graph import create_agent_graph # 实际运行需要模块导入
from agent_graph.state import AgentState


from utils.common_utils import other_path


def run_interactive_mode(app):
    print("\n" + "=" * 20 + " BioAgent 已启动 (输入 'exit' 退出) " + "=" * 20)

    while True:
        try:
            # 1. 获取控制台输入
            user_input = input("\n>>> 请输入你的指令: ").strip()

            # 2. 退出逻辑
            if user_input.lower() in ["exit", "quit", "退出"]:
                print("正在退出 BioAgent，再见！")
                break

            if not user_input:
                continue

            # 3. 运行 Agent 流
            print(f"\n[Agent] 正在处理: {user_input}...")

            # 注意：app.stream 可能会输出多步结果，我们只打印每一步的结果
            for event in app.stream({"input": user_input}):
                for node_name, node_output in event.items():
                    # 这里可以根据需要只打印特定节点或所有节点的信息
                    # print(f"  -> [{node_name}] 处理中...")
                    pass

            # 如果你的 Summarizer 节点在 state 中存了最终回复
            # 建议在 Graph 的最后一步确保 state 被完整输出

        except KeyboardInterrupt:
            print("\n检测到中断，正在退出...")
            break
        except Exception as e:
            print(f"\n[Error] 运行出错: {e}")


if __name__ == "__main__":
    # 你的图初始化
    app = create_agent_graph("BioAgent", is_save_graph_image=True, graph_image_filename=other_path['graph_image'])

    # 启动交互
    run_interactive_mode(app)