"""utils 模块的单元测试"""

import pytest
from pathlib import Path

# 添加项目根目录到 Python 路径
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from pdfgj.utils import parse_slide_range, natural_sort_key


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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])