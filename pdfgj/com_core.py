"""COM 公共层：进程管理、错误分类、文件预检、批量转换"""

import subprocess
import time
import traceback
from pathlib import Path
from typing import Any

from . import utils
from .deps import _has_win32


# ============================================================
# COM 进程名映射
# ============================================================
# Word.Application → WINWORD.EXE, Excel.Application → EXCEL.EXE
_COM_PROCESS_NAMES: dict[str, str] = {
    'Word.Application': 'WINWORD.EXE',
    'Excel.Application': 'EXCEL.EXE',
}


# ============================================================
# PID 获取
# ============================================================
def _get_com_pid(app: Any, name: str = "") -> int | None:
    """尝试多条路径获取 COM Application 的进程 PID"""
    paths = ['PID', 'pid', 'Application.PID', 'Application.pid']
    for attr_path in paths:
        obj = app
        try:
            for part in attr_path.split('.'):
                obj = getattr(obj, part)
            pid = int(obj)
            if pid and pid > 0:
                return pid
        except Exception:
            continue
    return None


# ============================================================
# COM 进程安全退出
# ============================================================
def _com_quit(app: Any, name: str, max_retries: int = 3) -> None:
    """安全退出 COM 应用：Quit → PID 精确杀 → (可选)进程名杀"""
    if app is None:
        return

    proc_name = _COM_PROCESS_NAMES.get(name, '')

    # 第一步：正常退出
    try:
        app.Quit()
    except Exception:
        pass

    # 等待一下让进程有机会正常退出
    time.sleep(0.3)

    # 检查进程是否已退出
    if proc_name:
        try:
            result = subprocess.run(
                ['tasklist', '/FI', f'IMAGENAME eq {proc_name}', '/NH'],
                capture_output=True, text=True, timeout=5
            )
            if proc_name.lower() not in result.stdout.lower():
                return  # 已正常退出
        except Exception:
            pass

    # 第二步：获取 PID 并精确终止
    pid = _get_com_pid(app, name)
    if pid:
        for attempt in range(1, max_retries + 1):
            try:
                subprocess.run(
                    ['taskkill', '/F', '/PID', str(pid)],
                    capture_output=True, timeout=10
                )
                time.sleep(0.5 * attempt)
                # 验证是否已退出
                result = subprocess.run(
                    ['tasklist', '/FI', f'IMAGENAME eq {proc_name}', '/NH'],
                    capture_output=True, text=True, timeout=5
                )
                if proc_name.lower() not in result.stdout.lower():
                    print(f"  [信息] 已强制终止 {name} (PID={pid})")
                    return
            except Exception:
                pass
        print(f"  [警告] 无法终止 {name} 进程 (PID={pid})，请手动检查任务管理器")
        return

    # 第三步：PID 不可用时的处理
    if not utils._allow_kill_office:
        print(f"  [警告] {name} 进程可能未完全退出（无法获取 PID）。")
        print(f"        请手动检查任务管理器中的 {proc_name}，或下次使用 --kill-office 参数自动终止")
        return

    # 仅在用户显式授权时执行全量进程名终止
    print(f"  [警告] 即将终止所有 {proc_name} 进程，可能丢失未保存工作！")
    for attempt in range(1, max_retries + 1):
        try:
            subprocess.run(
                ['taskkill', '/F', '/IM', proc_name],
                capture_output=True, timeout=10
            )
            time.sleep(0.5 * attempt)
            result = subprocess.run(
                ['tasklist', '/FI', f'IMAGENAME eq {proc_name}', '/NH'],
                capture_output=True, text=True, timeout=5
            )
            if proc_name.lower() not in result.stdout.lower():
                print(f"  [信息] 已按进程名终止 {proc_name}")
                return
        except Exception:
            pass

    print(f"  [警告] 无法终止 {name} 进程，请手动检查任务管理器（{proc_name}）")


# ============================================================
# COM 错误分类
# ============================================================
def _is_com_error(err: Exception) -> bool:
    """判断异常是否为 COM 相关错误"""
    return (type(err).__qualname__ == 'com_error'
            or type(err).__module__ == 'pywintypes' and type(err).__qualname__ == 'error')


def _classify_com_error(err: Exception) -> str:
    """根据 COM 异常的 HRESULT 错误码返回人类可读的原因"""
    msg = str(err)
    # 常见 HRESULT 错误码映射（取低 16 位匹配）
    hresult_map = {
        '0x800a175d': '文档设置了修改密码，或启用了保护视图',
        '0x800a1391': '文件正在被其他程序使用（文件锁定）',
        '0x800a03ec': '文件不存在或路径无效',
        '0x800a136b': '文件格式不兼容或扩展名不匹配',
        '0x800a138f': '权限不足，无法访问文件',
        '0x800a1066': '文件可能已损坏或包含不可解析的内容',
        '0x80010105': 'COM 服务器忙或已崩溃，请重试',
        '0x800706ba': 'COM 服务无响应，可能 OLE 死锁',
        '0x80010001': 'RPC 调用被拒绝，Office 可能正在显示对话框',
    }
    for code, reason in hresult_map.items():
        if code.lower() in msg.lower():
            return reason
    # 未匹配到已知错误码时，返回原始错误信息
    return f"COM 错误（详情: {msg.strip() or '未知'}）"


# ============================================================
# 文件预检
# ============================================================
def _precheck_file(file_path: Path) -> str | None:
    """打开前预检文件状态，返回错误原因字符串或 None（表示正常）"""
    if not file_path.exists():
        return f"文件不存在: {file_path.name}"
    if not file_path.is_file():
        return f"路径不是文件: {file_path.name}"
    try:
        # 检查文件是否可读（是否被独占锁定）
        with open(file_path, 'rb') as f:
            f.read(1)
    except PermissionError:
        return f"文件被其他程序独占锁定，无法读取: {file_path.name}"
    except OSError as e:
        return f"文件访问异常: {file_path.name} ({e})"
    return None


# ============================================================
# 批量转换
# ============================================================
def _batch_convert(files: list[Path], converter_cls: type, label: str = "") -> list[str]:
    """批量转换：通过上下文管理器复用同一 COM Application，仅启停一次。
    返回失败文件的名称列表。"""
    if not _has_win32:
        print("  [跳过] 缺少 pywin32 库。请运行: pip install pywin32")
        return [f.name for f in files]
    total = len(files)
    t0 = time.time()
    try:
        with converter_cls() as ctx:
            failed: list[str] = []
            for i, f in enumerate(files, 1):
                if not ctx.convert(f):
                    failed.append(f.name)
                utils._progress_bar(i, total, t0, label)
            return failed
    except RuntimeError as e:
        print(f"\n  [失败] {e}")
        return [f.name for f in files]
    except Exception as e:
        print(f"\n  [失败] 批量转换异常: {e}")
        if _is_com_error(e):
            print("    提示：请确认已安装对应 Office 组件且未被占用")
        else:
            traceback.print_exc()
        return [f.name for f in files]
