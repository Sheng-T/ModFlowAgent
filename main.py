# main.py
import os

from agent_graph.graph import create_agent_graph

import os

from configs import OTHER_PATH
from configs.app_config import APP_PASCAL

os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

def run_interactive_mode(app):
    print("\n" + "=" * 20 + f" {APP_PASCAL} 已启动 (输入 'exit' 退出) " + "=" * 20)

    while True:
        try:
            user_input = input("\n>>> 请输入你的指令: ").strip()

            if user_input.lower() in ["exit", "quit", "退出"]:
                print(f"正在退出 {APP_PASCAL}，再见！")
                break

            if not user_input:
                continue

            print(f"\n[Agent] 正在处理: {user_input}...")

            for event in app.stream({"input": user_input}):
                for node_name, node_output in event.items():
                    # print(f"  -> [{node_name}] 处理中...")
                    pass


        except KeyboardInterrupt:
            print("\n检测到中断，正在退出...")
            break
        except Exception as e:
            print(f"\n[Error] 运行出错: {e}")


if __name__ == "__main__":
    _ablation = os.environ.get("ABLATION_NO_CONTROLLER", "0") == "1"
    app = create_agent_graph(APP_PASCAL, is_save_graph_image=True, graph_image_filename=OTHER_PATH['graph_image'], ablation_no_controller=_ablation)

    run_interactive_mode(app)