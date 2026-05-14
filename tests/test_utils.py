"""utils 模块的单元测试"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# 添加项目根目录到 Python 路径
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from pdfgj.utils import parse_slide_range, natural_sort_key, _get_files, _check_overwrite, set_force_overwrite, _progress_bar


class TestParseSlideRange:
    """parse_slide_range 函数的测试类"""

    def test_basic_single_pages(self):
        """测试基本的单页解析"""
        result = parse_slide_range("1,3,5", 10)
        assert result == [1, 3, 5]

    def test_basic_range(self):
        """测试基本的范围解析"""
        result = parse_slide_range("2-5", 10)
        assert result == [2, 3, 4, 5]

    def test_mixed_format(self):
        """测试混合格式（单页和范围）"""
        result = parse_slide_range("1,3-5,8", 10)
        assert result == [1, 3, 4, 5, 8]

    def test_duplicate_removal(self):
        """测试去重功能"""
        result = parse_slide_range("1,2,3,2,1", 10)
        assert result == [1, 2, 3]

    def test_sorting(self):
        """测试排序功能"""
        result = parse_slide_range("5,3,1,4,2", 10)
        assert result == [1, 2, 3, 4, 5]

    def test_overflow_trimming(self):
        """测试超出范围裁剪"""
        result = parse_slide_range("1,5,10,15", 10)
        assert result == [1, 5, 10]

    def test_all_overflow(self):
        """测试所有页码超出范围"""
        with pytest.raises(ValueError, match="所有指定页码均超出范围"):
            parse_slide_range("11,12,13", 10)

    def test_empty_string(self):
        """测试空字符串"""
        with pytest.raises(ValueError, match="页码范围不能为空"):
            parse_slide_range("", 10)

    def test_whitespace_only(self):
        """测试仅空白字符"""
        with pytest.raises(ValueError, match="页码范围不能为空"):
            parse_slide_range("   ", 10)

    def test_invalid_format_missing_number(self):
        """测试无效格式：缺少数字"""
        with pytest.raises(ValueError, match="无效的页码范围格式"):
            parse_slide_range("1-,5", 10)

    def test_invalid_format_non_numeric(self):
        """测试无效格式：非数字"""
        with pytest.raises(ValueError, match="页码必须是数字"):
            parse_slide_range("1,abc,5", 10)

    def test_invalid_range_start_greater_than_end(self):
        """测试无效范围：起始页大于结束页"""
        with pytest.raises(ValueError, match="起始页不能大于结束页"):
            parse_slide_range("5-3", 10)

    def test_page_zero(self):
        """测试页码为 0"""
        with pytest.raises(ValueError, match="页码必须从 1 开始"):
            parse_slide_range("0,1,2", 10)

    def test_negative_page(self):
        """测试负数页码"""
        # "-1" 会被解析为范围格式，起始页为空
        with pytest.raises(ValueError):
            parse_slide_range("-1,1,2", 10)

    def test_total_slides_zero(self):
        """测试 total_slides 为 0"""
        with pytest.raises(ValueError, match="演示文稿没有幻灯片"):
            parse_slide_range("1,2,3", 0)

    def test_total_slides_negative(self):
        """测试 total_slides 为负数"""
        with pytest.raises(ValueError, match="演示文稿没有幻灯片"):
            parse_slide_range("1,2,3", -5)

    def test_single_page(self):
        """测试单页"""
        result = parse_slide_range("5", 10)
        assert result == [5]

    def test_range_at_boundary(self):
        """测试边界范围"""
        result = parse_slide_range("8-10", 10)
        assert result == [8, 9, 10]

    def test_complex_mixed_format(self):
        """测试复杂混合格式"""
        result = parse_slide_range("1,3-5,7,9-10", 10)
        assert result == [1, 3, 4, 5, 7, 9, 10]


class TestNaturalSortKey:
    """natural_sort_key 函数的测试类"""

    def test_basic_sorting(self):
        """测试基本排序"""
        paths = [Path("file10.txt"), Path("file2.txt"), Path("file1.txt")]
        sorted_paths = sorted(paths, key=natural_sort_key)
        assert sorted_paths == [Path("file1.txt"), Path("file2.txt"), Path("file10.txt")]

    def test_case_insensitive(self):
        """测试不区分大小写"""
        paths = [Path("File.txt"), Path("file.txt"), Path("FILE.txt")]
        sorted_paths = sorted(paths, key=natural_sort_key)
        # 所有应该被视为相同的键
        assert len(sorted_paths) == 3

    def test_mixed_numbers_and_text(self):
        """测试数字和文本混合"""
        paths = [Path("abc10.txt"), Path("abc2.txt"), Path("abc1.txt")]
        sorted_paths = sorted(paths, key=natural_sort_key)
        assert sorted_paths == [Path("abc1.txt"), Path("abc2.txt"), Path("abc10.txt")]

    def test_no_numbers(self):
        """测试没有数字的情况"""
        paths = [Path("banana.txt"), Path("apple.txt"), Path("cherry.txt")]
        sorted_paths = sorted(paths, key=natural_sort_key)
        assert sorted_paths == [Path("apple.txt"), Path("banana.txt"), Path("cherry.txt")]


class TestGetFiles:
    """_get_files 函数的测试类"""

    def test_get_files_basic(self, tmp_path):
        """测试基本文件获取"""
        # 创建测试文件
        (tmp_path / "file1.jpg").touch()
        (tmp_path / "file2.png").touch()
        (tmp_path / "file3.txt").touch()  # 不支持的格式

        result = _get_files(tmp_path, {'.jpg', '.png'})
        assert len(result) == 2
        assert any(f.name == "file1.jpg" for f in result)
        assert any(f.name == "file2.png" for f in result)

    def test_get_files_recursive(self, tmp_path):
        """测试递归获取文件"""
        # 创建子目录和文件
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (tmp_path / "file1.jpg").touch()
        (subdir / "file2.jpg").touch()

        result = _get_files(tmp_path, {'.jpg'}, recursive=True)
        assert len(result) == 2

    def test_get_files_no_recursive(self, tmp_path):
        """测试不递归获取文件"""
        # 创建子目录和文件
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (tmp_path / "file1.jpg").touch()
        (subdir / "file2.jpg").touch()

        result = _get_files(tmp_path, {'.jpg'}, recursive=False)
        assert len(result) == 1
        assert result[0].name == "file1.jpg"

    def test_get_files_empty_directory(self, tmp_path):
        """测试空目录"""
        result = _get_files(tmp_path, {'.jpg'})
        assert len(result) == 0

    def test_get_files_sorted(self, tmp_path):
        """测试文件排序"""
        (tmp_path / "file10.jpg").touch()
        (tmp_path / "file2.jpg").touch()
        (tmp_path / "file1.jpg").touch()

        result = _get_files(tmp_path, {'.jpg'})
        assert result[0].name == "file1.jpg"
        assert result[1].name == "file2.jpg"
        assert result[2].name == "file10.jpg"


class TestCheckOverwrite:
    """_check_overwrite 函数的测试类"""

    def test_file_not_exists(self, tmp_path):
        """测试文件不存在"""
        pdf_path = tmp_path / "nonexistent.pdf"
        result = _check_overwrite(pdf_path)
        assert result is True

    def test_file_exists_force_overwrite(self, tmp_path):
        """测试强制覆盖"""
        pdf_path = tmp_path / "existing.pdf"
        pdf_path.touch()

        set_force_overwrite(True)
        result = _check_overwrite(pdf_path)
        set_force_overwrite(False)
        assert result is True

    def test_file_exists_no_force(self, tmp_path):
        """测试文件存在但不强制覆盖"""
        pdf_path = tmp_path / "existing.pdf"
        pdf_path.touch()

        # 非交互模式，应该返回 False
        result = _check_overwrite(pdf_path, interactive=False)
        assert result is False

    def test_file_exists_interactive_yes(self, tmp_path):
        """测试交互模式用户确认覆盖"""
        pdf_path = tmp_path / "existing.pdf"
        pdf_path.touch()

        with patch('builtins.input', return_value='y'):
            result = _check_overwrite(pdf_path, interactive=True)
            assert result is True

    def test_file_exists_interactive_no(self, tmp_path):
        """测试交互模式用户拒绝覆盖"""
        pdf_path = tmp_path / "existing.pdf"
        pdf_path.touch()

        with patch('builtins.input', return_value='n'):
            result = _check_overwrite(pdf_path, interactive=True)
            assert result is False


class TestSetForceOverwrite:
    """set_force_overwrite 函数的测试类"""

    def test_set_true(self):
        """测试设置为 True"""
        set_force_overwrite(True)
        import pdfgj.utils
        assert pdfgj.utils._force_overwrite is True
        set_force_overwrite(False)

    def test_set_false(self):
        """测试设置为 False"""
        set_force_overwrite(False)
        import pdfgj.utils
        assert pdfgj.utils._force_overwrite is False


class TestProgressBar:
    """_progress_bar 函数的测试类"""

    def test_progress_bar_zero_total(self, capsys):
        """测试总数为0"""
        _progress_bar(0, 0, 0)
        captured = capsys.readouterr()
        # 总数为0时不应该输出任何内容
        assert captured.out == ""

    def test_progress_bar_complete(self, capsys):
        """测试完成状态"""
        import time
        _progress_bar(10, 10, time.time() - 10)
        captured = capsys.readouterr()
        # 完成时应该输出换行
        assert "\n" in captured.out

    def test_progress_bar_middle(self, capsys):
        """测试中间状态（非交互式环境不输出）"""
        import time
        _progress_bar(5, 10, time.time() - 5)
        captured = capsys.readouterr()
        # 非交互式环境下，中间状态不输出（只在完成时输出）
        assert captured.out == ""


class TestSetAllowKillOffice:
    """set_allow_kill_office 函数的测试类"""

    def test_set_true(self):
        """测试设置为 True"""
        from pdfgj.utils import set_allow_kill_office
        set_allow_kill_office(True)
        import pdfgj.utils
        assert pdfgj.utils._allow_kill_office is True
        set_allow_kill_office(False)

    def test_set_false(self):
        """测试设置为 False"""
        from pdfgj.utils import set_allow_kill_office
        set_allow_kill_office(False)
        import pdfgj.utils
        assert pdfgj.utils._allow_kill_office is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])