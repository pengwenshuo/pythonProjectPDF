"""word_convert 模块的单元测试"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from pdfgj.word_convert import _setup_word, _convert_word, word_to_pdf, WordConverter


class TestSetupWord:
    """_setup_word 函数测试"""

    def test_setup_word(self):
        """测试配置 Word 应用"""
        mock_word = MagicMock()
        _setup_word(mock_word)
        assert mock_word.Visible is False
        assert mock_word.DisplayAlerts == 0
        assert mock_word.AutomationSecurity == 3


class TestConvertWord:
    """_convert_word 函数测试"""

    @patch('pdfgj.word_convert._check_overwrite', return_value=False)
    def test_convert_word_no_overwrite(self, mock_check, tmp_path):
        """测试用户拒绝覆盖"""
        mock_word = MagicMock()
        result = _convert_word(mock_word, tmp_path / "test.docx")
        assert result is False

    @patch('pdfgj.word_convert._check_overwrite', return_value=True)
    @patch('pdfgj.word_convert._precheck_file', return_value="文件不存在")
    def test_convert_word_precheck_fail(self, mock_pre, mock_check, tmp_path):
        """测试预检失败"""
        mock_word = MagicMock()
        result = _convert_word(mock_word, tmp_path / "test.docx")
        assert result is False

    @patch('pdfgj.word_convert._check_overwrite', return_value=True)
    @patch('pdfgj.word_convert._precheck_file', return_value=None)
    def test_convert_word_success(self, mock_pre, mock_check, tmp_path):
        """测试成功转换"""
        mock_word = MagicMock()
        mock_doc = MagicMock()
        mock_word.Documents.Open.return_value = mock_doc

        result = _convert_word(mock_word, tmp_path / "test.docx")
        assert result is True
        mock_doc.SaveAs.assert_called_once()
        mock_doc.Close.assert_called_once()

    @patch('pdfgj.word_convert._check_overwrite', return_value=True)
    @patch('pdfgj.word_convert._precheck_file', return_value=None)
    def test_convert_word_open_returns_none(self, mock_pre, mock_check, tmp_path):
        """测试打开文件返回 None"""
        mock_word = MagicMock()
        mock_word.Documents.Open.return_value = None

        result = _convert_word(mock_word, tmp_path / "test.docx")
        assert result is False

    @patch('pdfgj.word_convert._check_overwrite', return_value=True)
    @patch('pdfgj.word_convert._precheck_file', return_value=None)
    def test_convert_word_com_error(self, mock_pre, mock_check, tmp_path):
        """测试 COM 错误"""
        mock_word = MagicMock()
        mock_word.Documents.Open.side_effect = Exception("Error 0x800a03ec")

        result = _convert_word(mock_word, tmp_path / "test.docx")
        assert result is False

    @patch('pdfgj.word_convert._check_overwrite', return_value=True)
    @patch('pdfgj.word_convert._precheck_file', return_value=None)
    def test_convert_word_general_error(self, mock_pre, mock_check, tmp_path):
        """测试一般错误"""
        mock_word = MagicMock()
        mock_word.Documents.Open.side_effect = RuntimeError("test error")

        result = _convert_word(mock_word, tmp_path / "test.docx")
        assert result is False

    @patch('pdfgj.word_convert._check_overwrite', return_value=True)
    @patch('pdfgj.word_convert._precheck_file', return_value=None)
    def test_convert_word_doc_close_error(self, mock_pre, mock_check, tmp_path):
        """测试文档关闭失败"""
        mock_word = MagicMock()
        mock_doc = MagicMock()
        mock_doc.Close.side_effect = Exception("close error")
        mock_word.Documents.Open.return_value = mock_doc

        result = _convert_word(mock_word, tmp_path / "test.docx")
        assert result is True  # 转换成功，关闭失败只打印警告


class TestWordToPdf:
    """word_to_pdf 函数测试"""

    @patch('pdfgj.word_convert._has_win32', False)
    def test_word_to_pdf_no_win32(self, tmp_path):
        """测试缺少 pywin32"""
        result = word_to_pdf(tmp_path / "test.docx")
        assert result is False


class TestWordConverter:
    """WordConverter 类测试"""

    def test_app_name(self):
        """测试应用名称"""
        with patch('pdfgj.com_core._has_win32', True), \
             patch('pdfgj.com_core.pythoncom'), \
             patch('pdfgj.com_core.DispatchEx'):
            converter = WordConverter()
            assert converter.app_name == 'Word.Application'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
