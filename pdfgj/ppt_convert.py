"""PowerPoint 转 PDF（需要安装 PowerPoint 和 pywin32）"""

import traceback
from pathlib import Path
from typing import Any

from .constants import PP_SAVE_AS_PDF, MSO_AUTOMATION_SECURITY_FORCE_DISABLE
from .deps import DispatchEx, pythoncom, _has_win32
from .utils import _check_overwrite, parse_slide_range
from .com_core import _com_quit, _is_com_error, _classify_com_error, _precheck_file


def _setup_ppt(ppt: Any) -> None:
    """配置 PowerPoint 应用：禁用弹窗、宏"""
    ppt.Visible = False
    ppt.DisplayAlerts = False
    ppt.AutomationSecurity = MSO_AUTOMATION_SECURITY_FORCE_DISABLE
    try:
        print(f"  [信息] PowerPoint 版本: {ppt.Version}")
    except Exception:
        pass


def _convert_ppt(ppt: Any, ppt_path: Path, slides: str | None = None) -> bool:
    """使用已启动的 PowerPoint 实例转换单个演示文稿"""
    pdf_path = ppt_path.with_suffix('.pdf')
    if not _check_overwrite(pdf_path):
        return False

    # 文件状态预检
    pre_err = _precheck_file(ppt_path)
    if pre_err:
        print(f"  [失败] {pre_err}")
        return False

    presentation = None
    try:
        presentation = ppt.Presentations.Open(str(ppt_path.absolute()), ReadOnly=True)
        if presentation is None:
            print(f"  [失败] {ppt_path.name}: 文件无法打开（可能已损坏或设置了打开密码）")
            return False

        if slides:
            # 指定范围：复制幻灯片到临时演示文稿后导出
            page_list = parse_slide_range(slides, presentation.Slides.Count)
            _export_slides(ppt, presentation, page_list, pdf_path)
        else:
            # 全量导出
            presentation.SaveAs(str(pdf_path.absolute()), FileFormat=PP_SAVE_AS_PDF)

        print(f"  [OK] {ppt_path.name} → {pdf_path.name}")
        return True
    except Exception as err:
        if _is_com_error(err):
            reason = _classify_com_error(err)
            print(f"  [失败] {ppt_path.name}: {reason}")
        else:
            print(f"  [失败] {ppt_path.name}: {err}")
            traceback.print_exc()
        return False
    finally:
        if presentation is not None:
            try:
                presentation.Close()
            except Exception as e:
                print(f"  [警告] 演示文稿关闭失败: {ppt_path.name}: {e}")


def _export_slides(ppt: Any, src_presentation: Any, page_list: list[int], pdf_path: Path) -> None:
    """将指定页码的幻灯片复制到临时演示文稿并导出为 PDF"""
    temp_pres = None
    try:
        # 创建空的临时演示文稿
        temp_pres = ppt.Presentations.Add()
        # 删除默认的空白幻灯片
        while temp_pres.Slides.Count > 0:
            temp_pres.Slides(1).Delete()

        # 复制指定幻灯片到临时演示文稿
        for page_num in page_list:
            src_slide = src_presentation.Slides(page_num)
            src_slide.Copy()
            # 粘贴到临时演示文稿末尾
            temp_pres.Slides.Paste(temp_pres.Slides.Count + 1)

        # 导出为 PDF
        temp_pres.SaveAs(str(pdf_path.absolute()), FileFormat=PP_SAVE_AS_PDF)
    finally:
        if temp_pres is not None:
            try:
                temp_pres.Close()
            except Exception:
                pass


def ppt_to_pdf(ppt_path: Path, slides: str | None = None) -> bool:
    """单文件模式：启动 PowerPoint → 转换 → 退出（兼容独立调用）"""
    if not _has_win32:
        print("  [跳过] 缺少 pywin32 库，无法转换 PowerPoint。请运行: pip install pywin32")
        return False
    ppt = None
    try:
        ppt = DispatchEx('PowerPoint.Application')
        _setup_ppt(ppt)
        return _convert_ppt(ppt, ppt_path, slides)
    finally:
        _com_quit(ppt, 'PowerPoint.Application')


class PptConverter:
    """
    PowerPoint 转 PDF 上下文管理器，复用同一 Application 实例批量转换。

    用法:
        with PptConverter(slides="1,3,5-8") as pc:
            pc.convert('a.pptx')
            pc.convert('b.pptx')
    """
    def __init__(self, slides: str | None = None) -> None:
        if not _has_win32:
            raise RuntimeError("缺少 pywin32 库。请运行: pip install pywin32")
        self._slides = slides
        self._app = None
        self._com_uninit_needed: bool = False

    def __enter__(self) -> 'PptConverter':
        hr = pythoncom.CoInitialize()  # type: ignore[union-attr]
        self._com_uninit_needed = (hr == 0)
        self._app = DispatchEx('PowerPoint.Application')
        _setup_ppt(self._app)
        return self

    def __exit__(self, *args) -> None:
        if self._app is not None:
            _com_quit(self._app, 'PowerPoint.Application')
        self._app = None
        if self._com_uninit_needed:
            try:
                pythoncom.CoUninitialize()  # type: ignore[union-attr]
            except Exception:
                pass

    def convert(self, path: Path | str) -> bool:
        """转换单个 PowerPoint 演示文稿为 PDF（复用当前 Application 实例）"""
        return _convert_ppt(self._app, Path(path), self._slides)
