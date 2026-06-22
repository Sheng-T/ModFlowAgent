# runtime/executor.py
import subprocess
import threading

from utils.ui_logger import ui_print


class ToolExecutor:
    @staticmethod
    def run(cmd: str):
        """物理执行命令，实时流式读取输出，避免长时间进程阻塞 Streamlit。"""
        ui_print(f"[ToolExecutor] running command: {cmd}")

        proc = subprocess.Popen(
            ['bash', '-c', cmd],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            start_new_session=True,  # isolate from Streamlit process group
        )

        stdout_lines = []
        stderr_lines = []

        def _read(pipe, buf):
            for line in pipe:
                line = line.rstrip("\n")
                buf.append(line)
                # 关键修复：过滤掉 Nextflow 的进程状态行，只打印有意义的内容
                if line.startswith("[- "):
                    # Nextflow 的进度行，只打印到终端，不推给 UI（避免刷屏）
                    print(line)
                else:
                    # 其他有意义的输出，才推给 UI
                    ui_print(line)  # 推送到 Streamlit 前端

        t_out = threading.Thread(target=_read, args=(proc.stdout, stdout_lines), daemon=True)
        t_err = threading.Thread(target=_read, args=(proc.stderr, stderr_lines), daemon=True)
        t_out.start()
        t_err.start()
        proc.wait()
        t_out.join()
        t_err.join()

        stdout = "\n".join(stdout_lines)
        stderr = "\n".join(stderr_lines)
        output = (stdout + "\n" + stderr).strip()

        return {
            "status": "success" if proc.returncode == 0 else "error",
            "stdout": stdout,
            "stderr": stderr,
            "output": output,
            "exit_code": proc.returncode,
        }