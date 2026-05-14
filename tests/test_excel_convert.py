"""excel_convert 模块的单元测试"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from pdfgj.excel_convert import _setup_excel, _convert_excel, excel_to_pdf, ExcelConverter


class TestSetupExcel:
    """_setup_excel 函数测试"""

    def test_setup_excel(self):
        """测试配置 Excel 应用"""
        mock_excel = MagicMock()
        _setup_excel(mock_excel)
        assert mock_excel.Visible is False
        assert mock_excel.DisplayAlerts is False
        assert mock_excel.ScreenUpdating is False
        assert mock_excel.AutomationSecurity == 3


class TestConvertExcel:
    """_convert_excel 函数测试"""

    @patch('pdfgj.excel_convert._check_overwrite', return_value=False)
    def test_convert_excel_no_overwrite(self, mock_check, tmp_path):
        """测试用户拒绝覆盖"""
        mock_excel = MagicMock()
        result = _convert_excel(mock_excel, tmp_path / "test.xlsx")
        assert result is False

    @patch('pdfgj.excel_convert._check_overwrite', return_value=True)
    @patch('pdfgj.excel_convert._precheck_file', return_value="文件不存在")
    def test_convert_excel_precheck_fail(self, mock_pre, mock_check, tmp_path):
        """测试预检失败"""
        mock_excel = MagicMock()
        result = _convert_excel(mock_excel, tmp_path / "test.xlsx")
        assert result is False

    @patch('pdfgj.excel_convert._check_overwrite', return_value=True)
    @patch('pdfgj.excel_convert._precheck_file', return_value=None)
    def test_convert_excel_success(self, mock_pre, mock_check, tmp_path):
        """测试成功转换"""
        mock_excel = MagicMock()
        mock_wb = MagicMock()
        mock_excel.Workbooks.Open.return_value = mock_wb

        result = _convert_excel(mock_excel, tmp_path / "test.xlsx")
        assert result is True
        mock_wb.ExportAsFixedFormat.assert_called_once()
        mock_wb.Close.assert_called_once()

    @patch('pdfgj.excel_convert._check_overwrite', return_value=True)
    @patch('pdfgj.excel_convert._precheck_file', return_value=None)
    def test_convert_excel_open_returns_none(self, mock_pre, mock_check, tmp_path):
        """测试打开文件返回 None"""
        mock_excel = MagicMock()
        mock_excel.Workbooks.Open.return_value = None

        result = _convert_excel(mock_excel, tmp_path / "test.xlsx")
        assert result is False

    @patch('pdfgj.excel_convert._check_overwrite', return_value=True)
    @patch('pdfgj.excel_convert._precheck_file', return_value=None)
    def test_convert_excel_error(self, mock_pre, mock_check, tmp_path):
        """测试转换错误"""
        mock_excel = MagicMock()
        mock_excel.Workbooks.Open.side_effect = Exception("Error 0x800a03ec")

        result = _convert_excel(mock_excel, tmp_path / "test.xlsx")
        assert result is False

    @patch('pdfgj.excel_convert._check_overwrite', return_value=True)
    @patch('pdfgj.excel_convert._precheck_file', return_value=None)
    def test_convert_excel_wb_close_error(self, mock_pre, mock_check, tmp_path):
        """测试工作簿关闭失败"""
        mock_excel = MagicMock()
        mock_wb = MagicMock()
        mock_wb.Close.side_effect = Exception("close error")
        mock_excel.Workbooks.Open.return_value = mock_wb

        result = _convert_excel(mock_excel, tmp_path / "test.xlsx")
        assert result is True


class TestExcelToPdf:
    """excel_to_pdf 函数测试"""

    @patch('pdfgj.excel_convert._has_win32', False)
    def test_excel_to_pdf_no_win32(self, tmp_path):
        """测试缺少 pywin32"""
        result = excel_to_pdf(tmp_path / "test.xlsx")
        assert result is False


class TestExcelConverter:
    """ExcelConverter 类测试"""

    def test_app_name(self):
        """测试应用名称"""
        with patch('pdfgj.com_core._has_win32', True), \
             patch('pdfgj.com_core.pythoncom'), \
             patch('pdfgj.com_core.DispatchEx'):
            converter = ExcelConverter()
            assert converter.app_name == 'Excel.Application'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
