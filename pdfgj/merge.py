"""PDF 合并"""

import os
import time
from pathlib import Path

from .deps import _has_pypdf, PdfMerger, PdfReader, PdfWriter
from .utils import _get_files, natural_sort_key, _check_overwrite, _progress_bar
from .pdf_processor import PDFProcessor


def _get_all_pdfs(directory: Path, recursive: bool = False, exclude: set[str] | None = None) -> list[Path]:
    """获取目录下所有 PDF 文件，排除指定文件名"""
    ex = exclude or set()
    return [f for f in _get_files(directory, {'.pdf'}, recursive) if f.name not in ex]


def merge_pdfs(directory: Path, output_name: str = "merged.pdf", recursive: bool = False,
               sortby: str = 'name') -> bool:
    """流式合并目录下 PDF 文件为单一 PDF，逐文件读取避免大目录内存耗尽"""
    if not _has_pypdf:
        print("缺少 pypdf 库，无法合并 PDF。请运行: pip install pypdf")
        return False
    assert PdfMerger is not None  # 静态分析护栏：_has_pypdf 为 True 时 PdfMerger 必定已导入
    pdf_files = _get_all_pdfs(directory, recursive, exclude={output_name})
    if sortby == 'ctime':
        pdf_files.sort(key=lambda f: f.stat().st_ctime)
    elif sortby == 'mtime':
        pdf_files.sort(key=lambda f: f.stat().st_mtime)
    else:
        pdf_files.sort(key=natural_sort_key)
    if not pdf_files:
        print("未找到可合并的 PDF 文件（尝试加 -r 递归查找子目录）")
        return False

    out_path = Path(output_name) if os.path.isabs(output_name) else (directory / output_name)
    if not _check_overwrite(out_path):
        return False

    # 创建PDF处理器
    processor = PDFProcessor()

    # 流式合并：使用 PdfWriter 逐文件追加，PdfReader 读完即释放
    writer = PdfWriter()  # type: ignore[misc]
    failed: list[Path] = []
    total = len(pdf_files)
    t0 = time.time()

    for i, pdf in enumerate(pdf_files, 1):
        _progress_bar(i, total, t0, "合并中")

        # 验证文件
        is_valid, error_msg = processor.validate_file(pdf)
        if not is_valid:
            print(f"\r  [跳过] {pdf.name}: {error_msg}")
            failed.append(pdf)
            continue

        # 处理PDF
        try:
            success, pages, error_msg = processor.process_pdf(pdf)
            if not success:
                print(f"\r  [跳过] {pdf.name}: {error_msg}")
                failed.append(pdf)
                continue

            # 添加页面到writer
            for page in pages:
                writer.add_page(page)
        except Exception as err:
            print(f"\r  [跳过] {pdf.name}: {err}")
            failed.append(pdf)

    # 进度条收尾换行
    _progress_bar(total, total, t0, "合并中")

    if not writer.pages:
        print("所有 PDF 文件均无法合并")
        writer.close()
        return False

    try:
        with open(str(out_path), 'wb') as f:
            writer.write(f)
    except Exception as err:
        print(f"合并写入失败: {err}")
        return False
    finally:
        writer.close()

    success_count = total - len(failed)
    print(f"合并完成！{success_count} 个 PDF → {out_path}")
    if failed:
        print(f"跳过: {[f.name for f in failed]}")
    return True
