# runtime/executor.py
import subprocess

class ToolExecutor:
    @staticmethod
    def run(cmd: str):
        """物理执行命令并捕获所有输出"""
        print(f"[ToolExecutor] 执行指令: {cmd}")
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True
        )

        stdout = result.stdout or ""
        stderr = result.stderr or ""

        # ⭐ 核心：统一输出
        output = (stdout + "\n" + stderr).strip()

        return {
            "status": "success" if result.returncode == 0 else "error",
            "stdout": stdout,
            "stderr": stderr,
            "output": output,
            "exit_code": result.returncode
        }