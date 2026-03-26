#!/usr/bin/env python3
"""检查并安装搜索功能所需的依赖"""
import subprocess
import sys

REQUIRED_PACKAGES = {
    'ddgs': 'ddgs',
    'html2text': 'html2text',
    'bs4': 'beautifulsoup4',
    'requests': 'requests'
}

DEPRECATED_PACKAGES = {
    'duckduckgo_search': '旧库已废弃，请卸载: pip uninstall duckduckgo_search -y'
}

def uninstall_deprecated():
    """卸载已废弃的包"""
    print("检查已废弃的包...")
    for module, instruction in DEPRECATED_PACKAGES.items():
        try:
            __import__(module)
            print(f"⚠ {module} 已安装（已废弃）")
            print(f"  {instruction}")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "uninstall", module, "-y"])
                print(f"✓ {module} 已卸载")
            except:
                pass
        except ImportError:
            pass

def check_and_install():
    """检查依赖并安装缺失的包"""
    # 先卸载废弃的包
    uninstall_deprecated()
    
    missing = []
    
    print("\n检查必要依赖...")
    for module, package in REQUIRED_PACKAGES.items():
        try:
            __import__(module)
            print(f"✓ {package}")
        except ImportError:
            print(f"✗ {package} 未安装")
            missing.append(package)
    
    if missing:
        print(f"\n安装缺失的包: {', '.join(missing)}")
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install"
            ] + missing)
            print("\n✓ 依赖安装完成")
        except Exception as e:
            print(f"\n✗ 安装失败: {e}")
            return False
    else:
        print("\n✓ 所有依赖已安装")
    
    return True

if __name__ == "__main__":
    success = check_and_install()
    sys.exit(0 if success else 1)
