"""merge 模块的单元测试"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from pdfgj.merge import _get_all_pdfs, merge_pdfs


class TestGetAllPdfs:
    """_get_all_pdfs 函数的测试类"""

    def test_get_pdfs_basic(self, tmp_path):
        """测试基本PDF文件获取"""
        (tmp_path / "file1.pdf").touch()
        (tmp_path / "file2.pdf").touch()
        (tmp_path / "file3.txt").touch()  # 非PDF文件

        result = _get_all_pdfs(tmp_path)
        assert len(result) == 2
        assert any(f.name == "file1.pdf" for f in result)
        assert any(f.name == "file2.pdf" for f in result)

    def test_get_pdfs_exclude(self, tmp_path):
        """测试排除指定文件"""
        (tmp_path / "file1.pdf").touch()
        (tmp_path / "merged.pdf").touch()

        result = _get_all_pdfs(tmp_path, exclude={"merged.pdf"})
        assert len(result) == 1
        assert result[0].name == "file1.pdf"

    def test_get_pdfs_recursive(self, tmp_path):
        """测试递归获取PDF"""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (tmp_path / "file1.pdf").touch()
        (subdir / "file2.pdf").touch()

        result = _get_all_pdfs(tmp_path, recursive=True)
        assert len(result) == 2

    def test_get_pdfs_empty_directory(self, tmp_path):
        """测试空目录"""
        result = _get_all_pdfs(tmp_path)
        assert len(result) == 0

    def test_get_pdfs_no_recursive(self, tmp_path):
        """测试不递归获取PDF"""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (tmp_path / "file1.pdf").touch()
        (subdir / "file2.pdf").touch()

        result = _get_all_pdfs(tmp_path, recursive=False)
        assert len(result) == 1
        assert result[0].name == "file1.pdf"


class TestMergePdfs:
    """merge_pdfs 函数的测试类"""

    def test_merge_no_pypdf(self, monkeypatch):
        """测试缺少 pypdf"""
        from pdfgj import merge
        monkeypatch.setattr(merge, '_has_pypdf', False)

        result = merge_pdfs(Path("."))
        assert result is False

    def test_merge_no_files(self, tmp_path, monkeypatch):
        """测试没有PDF文件"""
        from pdfgj import merge
        monkeypatch.setattr(merge, '_has_pypdf', True)

        with patch('pdfgj.merge._get_all_pdfs') as mock_get:
            mock_get.return_value = []
            result = merge_pdfs(tmp_path)
            assert result is False

    def test_merge_success(self, tmp_path, monkeypatch):
        """测试成功合并"""
        from pdfgj import merge
        from pypdf import PdfWriter, PdfReader
        monkeypatch.setattr(merge, '_has_pypdf', True)

        # 创建真实的 PDF 文件
        for name in ["a.pdf", "b.pdf"]:
            writer = PdfWriter()
            writer.add_blank_page(width=595, height=842)
            with open(tmp_path / name, 'wb') as f:
                writer.write(f)

        # 用真实 PdfReader 读取页面
        reader = PdfReader(str(tmp_path / "a.pdf"))
        real_page = reader.pages[0]

        mock_processor = MagicMock()
        mock_processor.validate_file.return_value = (True, "")
        mock_processor.process_pdf.return_value = (True, [real_page], "")

        with patch('pdfgj.merge._check_overwrite', return_value=True), \
             patch('pdfgj.merge._progress_bar'), \
             patch('pdfgj.merge.PDFProcessor', return_value=mock_processor):
            result = merge_pdfs(tmp_path)
            assert result is True
            assert (tmp_path / "merged.pdf").exists()

    def test_merge_sortby_ctime(self, tmp_path, monkeypatch):
        """测试按创建时间排序"""
        from pdfgj import merge
        from pypdf import PdfWriter, PdfReader
        monkeypatch.setattr(merge, '_has_pypdf', True)

        for name in ["a.pdf", "b.pdf"]:
            writer = PdfWriter()
            writer.add_blank_page(width=595, height=842)
            with open(tmp_path / name, 'wb') as f:
                writer.write(f)

        reader = PdfReader(str(tmp_path / "a.pdf"))
        real_page = reader.pages[0]

        mock_processor = MagicMock()
        mock_processor.validate_file.return_value = (True, "")
        mock_processor.process_pdf.return_value = (True, [real_page], "")

        with patch('pdfgj.merge._check_overwrite', return_value=True), \
             patch('pdfgj.merge._progress_bar'), \
             patch('pdfgj.merge.PDFProcessor', return_value=mock_processor):
            result = merge_pdfs(tmp_path, sortby='ctime')
            assert result is True

    def test_merge_sortby_mtime(self, tmp_path, monkeypatch):
        """测试按修改时间排序"""
        from pdfgj import merge
        from pypdf import PdfWriter, PdfReader
        monkeypatch.setattr(merge, '_has_pypdf', True)

        for name in ["a.pdf", "b.pdf"]:
            writer = PdfWriter()
            writer.add_blank_page(width=595, height=842)
            with open(tmp_path / name, 'wb') as f:
                writer.write(f)

        reader = PdfReader(str(tmp_path / "a.pdf"))
        real_page = reader.pages[0]

        mock_processor = MagicMock()
        mock_processor.validate_file.return_value = (True, "")
        mock_processor.process_pdf.return_value = (True, [real_page], "")

        with patch('pdfgj.merge._check_overwrite', return_value=True), \
             patch('pdfgj.merge._progress_bar'), \
             patch('pdfgj.merge.PDFProcessor', return_value=mock_processor):
            result = merge_pdfs(tmp_path, sortby='mtime')
            assert result is True

    def test_merge_overwrite_rejected(self, tmp_path, monkeypatch):
        """测试用户拒绝覆盖"""
        from pdfgj import merge
        monkeypatch.setattr(merge, '_has_pypdf', True)

        with patch('pdfgj.merge._get_all_pdfs') as mock_get, \
             patch('pdfgj.merge._check_overwrite', return_value=False):
            mock_get.return_value = [tmp_path / "a.pdf"]
            result = merge_pdfs(tmp_path)
            assert result is False

    def test_merge_invalid_pdf(self, tmp_path, monkeypatch):
        """测试无效 PDF 被跳过"""
        from pdfgj import merge
        monkeypatch.setattr(merge, '_has_pypdf', True)

        (tmp_path / "bad.pdf").touch()

        mock_processor = MagicMock()
        mock_processor.validate_file.return_value = (False, "文件为空")

        with patch('pdfgj.merge._check_overwrite', return_value=True), \
             patch('pdfgj.merge._progress_bar'), \
             patch('pdfgj.merge.PDFProcessor', return_value=mock_processor):
            result = merge_pdfs(tmp_path)
            assert result is False

    def test_merge_write_error(self, tmp_path, monkeypatch):
        """测试写入失败"""
        from pdfgj import merge
        monkeypatch.setattr(merge, '_has_pypdf', True)

        from pypdf import PdfWriter
        writer = PdfWriter()
        writer.add_blank_page(width=595, height=842)
        with open(tmp_path / "a.pdf", 'wb') as f:
            writer.write(f)

        mock_processor = MagicMock()
        mock_page = MagicMock()
        mock_processor.validate_file.return_value = (True, "")
        mock_processor.process_pdf.return_value = (True, [mock_page], "")

        original_open = open

        def mock_open(*args, **kwargs):
            if args and str(args[0]).endswith('merged.pdf'):
                raise PermissionError("denied")
            return original_open(*args, **kwargs)

        with patch('pdfgj.merge._check_overwrite', return_value=True), \
             patch('pdfgj.merge._progress_bar'), \
             patch('pdfgj.merge.PDFProcessor', return_value=mock_processor), \
             patch('builtins.open', side_effect=mock_open):
            result = merge_pdfs(tmp_path)
            assert result is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
