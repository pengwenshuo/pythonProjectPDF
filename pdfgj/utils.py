"""工具函数：排序、文件获取、进度条、覆盖保护、全局标志"""

import re
import sys
import time
from pathlib import Path


# ============================================================
# 自然排序
# ============================================================
def natural_sort_key(path: Path) -> str:
    """自然排序：数字按数值排序（1,2,10,11 而非 1,10,11,2）"""
    return re.sub(r'(\d+)', lambda m: m.group(1).zfill(10), path.name.lower())


# ============================================================
# 文件获取
# ============================================================
def _get_files(directory: Path, formats: set[str], recursive: bool = False) -> list[Path]:
    """获取目录下指定格式的文件，按自然序排列"""
    if recursive:
        files = [f for f in directory.rglob('*') if f.is_file() and f.suffix.lower() in formats]
    else:
        files = [f for f in directory.iterdir() if f.is_file() and f.suffix.lower() in formats]
    files.sort(key=natural_sort_key)
    return files


# ============================================================
# 页码范围解析
# ============================================================
def parse_slide_range(spec: str, total_slides: int) -> list[int]:
    """解析页码范围字符串，返回去重排序后的页码列表。

    格式: "1,3,5-8,10"
    规则:
      - 页码从 1 开始
      - 支持单页 (3) 和范围 (5-8)
      - 超出 total_slides 的页码会被裁剪并警告
      - 空字符串或无效格式抛出 ValueError
    """
    if not spec or not spec.strip():
        raise ValueError("页码范围不能为空")
    if total_slides <= 0:
        raise ValueError(f"演示文稿没有幻灯片（总数: {total_slides}）")

    pages: set[int] = set()
    for part in spec.split(','):
        part = part.strip()
        if not part:
            continue
        if '-' in part:
            # 范围格式：5-8
            nums = part.split('-', 1)
            if len(nums) != 2 or not nums[0].strip() or not nums[1].strip():
                raise ValueError(f"无效的页码范围格式: '{part}'")
            try:
                start = int(nums[0].strip())
                end = int(nums[1].strip())
            except ValueError:
                raise ValueError(f"页码必须是数字: '{part}'")
            if start < 1 or end < 1:
                raise ValueError(f"页码必须从 1 开始: '{part}'")
            if start > end:
                raise ValueError(f"起始页不能大于结束页: '{part}'")
            pages.update(range(start, end + 1))
        else:
            # 单页格式：3
            try:
                num = int(part)
            except ValueError:
                raise ValueError(f"页码必须是数字: '{part}'")
            if num < 1:
                raise ValueError(f"页码必须从 1 开始: '{part}'")
            pages.add(num)

    # 裁剪超出范围的页码
    valid_pages = sorted(p for p in pages if p <= total_slides)
    overflow = sorted(p for p in pages if p > total_slides)
    if overflow:
        print(f"  [警告] 页码超出范围（共 {total_slides} 页），已忽略: {', '.join(map(str, overflow))}")
    if not valid_pages:
        raise ValueError(f"所有指定页码均超出范围（共 {total_slides} 页）")

    return valid_pages


# ============================================================
# 进度条
# ============================================================
def _progress_bar(current: int, total: int, start_time: float, label: str = "") -> None:
    """自实现轻量进度条：百分比 + 已用时间 + 预估剩余时间

    在交互式终端中显示完整进度条，在非交互式环境（如重定向到文件）中仅输出完成信息。
    """
    if total == 0:
        return

    # 非交互式环境：仅在完成时输出一行
    if not sys.stdout.isatty():
        if current >= total:
            elapsed = time.time() - start_time
            elapsed_str = f"{elapsed:.0f}s" if elapsed < 120 else f"{elapsed/60:.1f}min"
            prefix = f"{label}: " if label else ""
            print(f"  {prefix}完成 {current}/{total}，耗时 {elapsed_str}")
        return

    # 交互式环境：仅在完成时显示进度条汇总
    if current >= total:
        elapsed = time.time() - start_time
        elapsed_str = f"{elapsed:.0f}s" if elapsed < 120 else f"{elapsed/60:.1f}min"
        prefix = f"{label}: " if label else ""
        print(f"  {prefix}完成 {current}/{total}，耗时 {elapsed_str}")


# ============================================================
# 全局标志（由命令行参数设置）
# ============================================================
_force_overwrite: bool = False   # --yes：跳过所有覆盖确认
_allow_kill_office: bool = False  # --kill-office：允许按进程名终止 Office


def set_force_overwrite(value: bool) -> None:
    global _force_overwrite
    _force_overwrite = value


def set_allow_kill_office(value: bool) -> None:
    global _allow_kill_office
    _allow_kill_office = value


# ============================================================
# 覆盖保护
# ============================================================
def _check_overwrite(pdf_path: Path, interactive: bool = True) -> bool:
    """检测同名 PDF 是否已存在；若是，提示确认或自动拒绝"""
    if not pdf_path.exists():
        return True
    if _force_overwrite:
        return True
    if interactive:
        print()  # 换行清除进度条行，避免与 input 提示冲突
        answer = input(f"  [!] 已存在 {pdf_path.name}，覆盖? (y/N): ").strip().lower()
        return answer == 'y'
    else:
        print(f"  [跳过] 已存在同名 PDF: {pdf_path.name}")
        return False
