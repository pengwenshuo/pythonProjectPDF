"""ppt_convert 模块的单元测试"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from pdfgj.ppt_convert import _setup_ppt, _convert_ppt, _export_slides, ppt_to_pdf, PptConverter


class TestSetupPpt:
    """_setup_ppt 函数测试"""

    def test_setup_ppt(self):
        """测试配置 PowerPoint 应用"""
        mock_ppt = MagicMock()
        _setup_ppt(mock_ppt)
        assert mock_ppt.DisplayAlerts is False
        assert mock_ppt.AutomationSecurity == 3


class TestConvertPpt:
    """_convert_ppt 函数测试"""

    @patch('pdfgj.ppt_convert._check_overwrite', return_value=False)
    def test_convert_ppt_no_overwrite(self, mock_check, tmp_path):
        """测试用户拒绝覆盖"""
        mock_ppt = MagicMock()
        result = _convert_ppt(mock_ppt, tmp_path / "test.pptx")
        assert result is False

    @patch('pdfgj.ppt_convert._check_overwrite', return_value=True)
    @patch('pdfgj.ppt_convert._precheck_file', return_value="文件不存在")
    def test_convert_ppt_precheck_fail(self, mock_pre, mock_check, tmp_path):
        """测试预检失败"""
        mock_ppt = MagicMock()
        result = _convert_ppt(mock_ppt, tmp_path / "test.pptx")
        assert result is False

    @patch('pdfgj.ppt_convert._check_overwrite', return_value=True)
    @patch('pdfgj.ppt_convert._precheck_file', return_value=None)
    def test_convert_ppt_full_export(self, mock_pre, mock_check, tmp_path):
        """测试全量导出"""
        mock_ppt = MagicMock()
        mock_pres = MagicMock()
        mock_ppt.Presentations.Open.return_value = mock_pres

        result = _convert_ppt(mock_ppt, tmp_path / "test.pptx")
        assert result is True
        mock_pres.SaveAs.assert_called_once()
        mock_pres.Close.assert_called_once()

    @patch('pdfgj.ppt_convert._check_overwrite', return_value=True)
    @patch('pdfgj.ppt_convert._precheck_file', return_value=None)
    def test_convert_ppt_with_slides(self, mock_pre, mock_check, tmp_path):
        """测试指定页码导出"""
        mock_ppt = MagicMock()
        mock_pres = MagicMock()
        mock_pres.Slides.Count = 10
        mock_ppt.Presentations.Open.return_value = mock_pres

        with patch('pdfgj.ppt_convert._export_slides') as mock_export:
            result = _convert_ppt(mock_ppt, tmp_path / "test.pptx", slides="1,3,5")
            assert result is True
            mock_export.assert_called_once()

    @patch('pdfgj.ppt_convert._check_overwrite', return_value=True)
    @patch('pdfgj.ppt_convert._precheck_file', return_value=None)
    def test_convert_ppt_open_returns_none(self, mock_pre, mock_check, tmp_path):
        """测试打开文件返回 None"""
        mock_ppt = MagicMock()
        mock_ppt.Presentations.Open.return_value = None

        result = _convert_ppt(mock_ppt, tmp_path / "test.pptx")
        assert result is False

    @patch('pdfgj.ppt_convert._check_overwrite', return_value=True)
    @patch('pdfgj.ppt_convert._precheck_file', return_value=None)
    def test_convert_ppt_error(self, mock_pre, mock_check, tmp_path):
        """测试转换错误"""
        mock_ppt = MagicMock()
        mock_ppt.Presentations.Open.side_effect = Exception("Error 0x800a03ec")

        result = _convert_ppt(mock_ppt, tmp_path / "test.pptx")
        assert result is False

    @patch('pdfgj.ppt_convert._check_overwrite', return_value=True)
    @patch('pdfgj.ppt_convert._precheck_file', return_value=None)
    def test_convert_ppt_pres_close_error(self, mock_pre, mock_check, tmp_path):
        """测试演示文稿关闭失败"""
        mock_ppt = MagicMock()
        mock_pres = MagicMock()
        mock_pres.Close.side_effect = Exception("close error")
        mock_ppt.Presentations.Open.return_value = mock_pres

        result = _convert_ppt(mock_ppt, tmp_path / "test.pptx")
        assert result is True


class TestExportSlides:
    """_export_slides 函数测试"""

    def test_export_slides_success(self, tmp_path):
        """测试导出指定幻灯片"""
        mock_ppt = MagicMock()
        mock_src = MagicMock()
        mock_temp = MagicMock()
        mock_temp.Slides.Count = 0
        mock_ppt.Presentations.Add.return_value = mock_temp

        _export_slides(mock_ppt, mock_src, [1, 3, 5], tmp_path / "out.pdf")
        mock_temp.SaveAs.assert_called_once()

    def test_export_slides_temp_close_error(self, tmp_path):
        """测试临时演示文稿关闭失败"""
        mock_ppt = MagicMock()
        mock_src = MagicMock()
        mock_temp = MagicMock()
        mock_temp.Slides.Count = 0
        mock_temp.Close.side_effect = Exception("close error")
        mock_ppt.Presentations.Add.return_value = mock_temp

        # 不应抛出异常
        _export_slides(mock_ppt, mock_src, [1], tmp_path / "out.pdf")


class TestPptToPdf:
    """ppt_to_pdf 函数测试"""

    @patch('pdfgj.ppt_convert._has_win32', False)
    def test_ppt_to_pdf_no_win32(self, tmp_path):
        """测试缺少 pywin32"""
        result = ppt_to_pdf(tmp_path / "test.pptx")
        assert result is False


class TestPptConverter:
    """PptConverter 类测试"""

    def test_app_name(self):
        """测试应用名称"""
        with patch('pdfgj.com_core._has_win32', True), \
             patch('pdfgj.com_core.pythoncom'), \
             patch('pdfgj.com_core.DispatchEx'):
            converter = PptConverter()
            assert converter.app_name == 'PowerPoint.Application'

    def test_init_with_slides(self):
        """测试带页码参数初始化"""
        with patch('pdfgj.com_core._has_win32', True), \
             patch('pdfgj.com_core.pythoncom'), \
             patch('pdfgj.com_core.DispatchEx'):
            converter = PptConverter(slides="1,3,5")
            assert converter._slides == "1,3,5"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
