"""命令行参数解析与主流程"""

import argparse
import sys
import time
from pathlib import Path

from .constants import IMG_FORMATS, WORD_FORMATS, EXCEL_FORMATS, PPT_FORMATS
from .utils import _get_files, _progress_bar, set_force_overwrite, set_allow_kill_office
from .com_core import _batch_convert
from .image_convert import image_to_pdf
from .word_convert import WordConverter
from .excel_convert import ExcelConverter
from .ppt_convert import PptConverter
from .merge import merge_pdfs


def parse_args() -> argparse.Namespace:
    """解析命令行参数并校验"""
    p = argparse.ArgumentParser(
        description='图片 / Word / Excel 转 PDF 与 PDF 合并工具',
        epilog='''
快捷方式（任意终端直接输入）:
  PDF                          合并PDF(默认)
  PDF -i                       图片→PDF
  PDF -w                       Word→PDF
  PDF -e                       Excel→PDF
  PDF -p                       PPT→PDF
  PDF -ro 合集.pdf             合并+递归+指定输出

完整命令:
  python -m pdfgj              合并PDF(默认)       python -m pdfgj -i          图片→PDF
  python -m pdfgj -ir          图片→PDF(递归)      python -m pdfgj -w          Word→PDF
  python -m pdfgj -wr          Word→PDF(递归)      python -m pdfgj -e          Excel→PDF
  python -m pdfgj -er          Excel→PDF(递归)     python -m pdfgj -p          PPT→PDF
  python -m pdfgj -pr          PPT→PDF(递归)       python -m pdfgj -p --slides 1,3,5-8  PPT→PDF(指定页码)
  python -m pdfgj -ro out      合并+递归+指定输出
        ''',
        formatter_class=argparse.RawTextHelpFormatter
    )
    # 工作模式
    mode = p.add_mutually_exclusive_group()
    mode.add_argument('-m', '--merge', action='store_true', help='合并模式：合并目录下所有 PDF')
    mode.add_argument('-i', '--image', action='store_true', help='图片模式：图片转 PDF')
    mode.add_argument('-w', '--word', action='store_true', help='Word 模式：Word 文档转 PDF')
    mode.add_argument('-e', '--excel', action='store_true', help='Excel 模式：Excel 表格转 PDF')
    mode.add_argument('-p', '--ppt', action='store_true', help='PPT 模式：PowerPoint 演示文稿转 PDF')
    p.add_argument('-o', '--output', type=str, default='merged.pdf', help='合并模式：指定输出文件名')
    p.add_argument('--slides', type=str, default=None,
                   help='PPT 模式：指定导出页码，如 "1,3,5-8"')
    p.add_argument('-r', '--recursive', action='store_true', help='递归查找子目录（适用于所有模式）')
    p.add_argument('--sortby', type=str, choices=['name', 'ctime', 'mtime'], default='name',
                   help='合并模式：排序依据（name/ctime/mtime）')
    p.add_argument('-y', '--yes', action='store_true',
                   help='跳过所有覆盖确认（批量自动化）')
    p.add_argument('--kill-office', action='store_true',
                   help='允许按进程名终止 Office 进程（可能丢失其他文档未保存工作）')
    args = p.parse_args()

    # 参数校验：用 sys.argv 判断用户是否显式传了 -o/--output/--sortby
    def _argv_has(flag: tuple[str, ...] | str) -> bool:
        flags = flag if isinstance(flag, tuple) else (flag,)
        return any(a in sys.argv for a in flags)

    has_output = _argv_has(('-o', '--output'))
    has_sortby = _argv_has('--sortby')
    # 默认模式和 -m 都是合并，都允许使用 -o / --sortby
    is_merge = args.merge or (not args.image and not args.word and not args.excel and not args.ppt)
    if (has_output or has_sortby) and not is_merge:
        p.error('-o / --sortby 只能在合并模式下使用')

    has_slides = _argv_has('--slides')
    if has_slides and not args.ppt:
        p.error('--slides 只能在 PPT 模式 (-p) 下使用')

    return args


def _print_summary(total: int, failed: list[str]) -> None:
    """输出批量转换的成功/失败统计"""
    success = total - len(failed)
    print(f"\n完成！成功 {success}/{total}")
    if failed:
        print(f"失败 ({len(failed)}): {', '.join(failed)}")


def main():
    set_force_overwrite(False)
    set_allow_kill_office(False)
    args = parse_args()
    set_force_overwrite(args.yes)
    set_allow_kill_office(args.kill_office)
    cwd = Path.cwd()
    print(f"工作目录: {cwd}\n")

    # --- Word 转 PDF（批量：仅启停一次 Word） ---
    if args.word:
        files = _get_files(cwd, WORD_FORMATS, recursive=args.recursive)
        if not files:
            print("当前目录未找到 Word 文档 (.docx / .doc)")
            return
        print(f"找到 {len(files)} 个 Word 文档")
        failed = _batch_convert(files, WordConverter, "Word→PDF")
        _print_summary(len(files), failed)
        return

    # --- Excel 转 PDF（批量：仅启停一次 Excel） ---
    if args.excel:
        files = _get_files(cwd, EXCEL_FORMATS, recursive=args.recursive)
        if not files:
            print("当前目录未找到 Excel 表格 (.xlsx / .xls)")
            return
        print(f"找到 {len(files)} 个 Excel 表格")
        failed = _batch_convert(files, ExcelConverter, "Excel→PDF")
        _print_summary(len(files), failed)
        return

    # --- PPT 转 PDF（批量：仅启停一次 PowerPoint） ---
    if args.ppt:
        files = _get_files(cwd, PPT_FORMATS, recursive=args.recursive)
        if not files:
            print("当前目录未找到 PowerPoint 演示文稿 (.pptx / .ppt)")
            return
        print(f"找到 {len(files)} 个演示文稿")
        failed = _batch_convert(files, lambda: PptConverter(slides=args.slides), "PPT→PDF")
        _print_summary(len(files), failed)
        return

    # --- 图片转 PDF（-i 模式）---
    if args.image:
        images = _get_files(cwd, IMG_FORMATS, recursive=args.recursive)
        if not images:
            print("当前目录未找到图片文件")
            print(f"支持格式: {', '.join(sorted(IMG_FORMATS))}")
            return
        print(f"找到 {len(images)} 张图片\n")
        total = len(images)
        t0 = time.time()
        failed: list[str] = []
        for i, img in enumerate(images, 1):
            if not image_to_pdf(img):
                failed.append(img.name)
            _progress_bar(i, total, t0, "图片→PDF")
        _print_summary(len(images), failed)
        return

    # --- 合并 PDF（默认模式，包括 -m 显式指定）---
    merge_pdfs(cwd, output_name=args.output, recursive=args.recursive, sortby=args.sortby)
