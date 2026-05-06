"""Excel 转 PDF（需要安装 Excel 和 pywin32）"""

import traceback
from pathlib import Path
from typing import Any

from .constants import XL_TYPE_PDF, XL_CALC_AUTOMATIC, MSO_AUTOMATION_SECURITY_FORCE_DISABLE
from .deps import DispatchEx, _has_win32
from .utils import _check_overwrite
from .com_core import _com_quit, _is_com_error, _classify_com_error, _precheck_file, COMConverter


def _setup_excel(excel: Any) -> None:
    """配置 Excel 应用：禁用弹窗、宏、外部链接、屏幕刷新"""
    excel.Visible = False
    excel.DisplayAlerts = False
    excel.ScreenUpdating = False
    excel.AutomationSecurity = MSO_AUTOMATION_SECURITY_FORCE_DISABLE
    try:
        print(f"  [信息] Excel 版本: {excel.Version} (COM 常量 xlTypePDF={XL_TYPE_PDF})")
    except Exception:
        pass


def _convert_excel(excel: Any, excel_path: Path) -> bool:
    """使用已启动的 Excel 实例转换单个工作簿（嵌套 try-finally 确保文档关闭）"""
    pdf_path = excel_path.with_suffix('.pdf')
    if not _check_overwrite(pdf_path):
        return False

    # 文件状态预检
    pre_err = _precheck_file(excel_path)
    if pre_err:
        print(f"  [失败] {pre_err}")
        return False

    wb = None
    try:
        wb = excel.Workbooks.Open(str(excel_path.absolute()), UpdateLinks=0, ReadOnly=True)
        if wb is None:
            print(f"  [失败] {excel_path.name}: 文件无法打开（可能已损坏或设置了打开密码）")
            return False
        # 打开工作簿后设置 Calculation，确保公式结果最新（某些版本在无工作簿时无法设置此属性）
        try:
            excel.Calculation = XL_CALC_AUTOMATIC
        except Exception:
            pass
        wb.ExportAsFixedFormat(XL_TYPE_PDF, str(pdf_path.absolute()))
        print(f"  [OK] {excel_path.name} → {pdf_path.name}")
        return True
    except Exception as err:
        if _is_com_error(err):
            reason = _classify_com_error(err)
            print(f"  [失败] {excel_path.name}: {reason}")
        else:
            print(f"  [失败] {excel_path.name}: {err}")
            traceback.print_exc()
        return False
    finally:
        if wb is not None:
            try:
                wb.Close(SaveChanges=False)
            except Exception as e:
                print(f"  [警告] 工作簿关闭失败: {excel_path.name}: {e}")


def excel_to_pdf(excel_path: Path) -> bool:
    """单文件模式：启动 Excel → 转换 → 退出（兼容独立调用）"""
    if not _has_win32:
        print("  [跳过] 缺少 pywin32 库，无法转换 Excel。请运行: pip install pywin32")
        return False
    excel = None
    try:
        excel = DispatchEx('Excel.Application')
        _setup_excel(excel)
        return _convert_excel(excel, excel_path)
    finally:
        _com_quit(excel, 'Excel.Application')


class ExcelConverter(COMConverter):
    """
    Excel 转 PDF 上下文管理器，复用同一 Application 实例批量转换。

    用法:
        with ExcelConverter() as ec:
            ec.convert('a.xlsx')
            ec.convert('b.xlsx')
    """

    @property
    def app_name(self) -> str:
        return 'Excel.Application'

    def setup(self, app: Any) -> None:
        _setup_excel(app)

    def convert(self, path: Path | str) -> bool:
        """转换单个 Excel 工作簿为 PDF（复用当前 Application 实例）"""
        return _convert_excel(self._app, Path(path))
