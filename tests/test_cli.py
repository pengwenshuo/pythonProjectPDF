"""cli 模块的单元测试"""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from pdfgj.cli import parse_args, _print_summary


class TestParseArgs:
    """parse_args 函数的测试类"""

    def test_default_args(self):
        """测试默认参数"""
        with patch('sys.argv', ['pdfgj']):
            args = parse_args()
            assert args.merge is False
            assert args.image is False
            assert args.word is False
            assert args.excel is False
            assert args.ppt is False
            assert args.output == 'merged.pdf'
            assert args.recursive is False
            assert args.sortby == 'name'
            assert args.yes is False

    def test_merge_mode(self):
        """测试合并模式"""
        with patch('sys.argv', ['pdfgj', '-m']):
            args = parse_args()
            assert args.merge is True

    def test_image_mode(self):
        """测试图片模式"""
        with patch('sys.argv', ['pdfgj', '-i']):
            args = parse_args()
            assert args.image is True

    def test_word_mode(self):
        """测试Word模式"""
        with patch('sys.argv', ['pdfgj', '-w']):
            args = parse_args()
            assert args.word is True

    def test_excel_mode(self):
        """测试Excel模式"""
        with patch('sys.argv', ['pdfgj', '-e']):
            args = parse_args()
            assert args.excel is True

    def test_ppt_mode(self):
        """测试PPT模式"""
        with patch('sys.argv', ['pdfgj', '-p']):
            args = parse_args()
            assert args.ppt is True

    def test_recursive(self):
        """测试递归参数"""
        with patch('sys.argv', ['pdfgj', '-r']):
            args = parse_args()
            assert args.recursive is True

    def test_yes(self):
        """测试跳过确认参数"""
        with patch('sys.argv', ['pdfgj', '-y']):
            args = parse_args()
            assert args.yes is True

    def test_output(self):
        """测试输出文件名参数"""
        with patch('sys.argv', ['pdfgj', '-o', 'output.pdf']):
            args = parse_args()
            assert args.output == 'output.pdf'

    def test_sortby(self):
        """测试排序参数"""
        with patch('sys.argv', ['pdfgj', '--sortby', 'mtime']):
            args = parse_args()
            assert args.sortby == 'mtime'

    def test_slides(self):
        """测试PPT页码参数"""
        with patch('sys.argv', ['pdfgj', '-p', '--slides', '1,3,5-8']):
            args = parse_args()
            assert args.slides == '1,3,5-8'


class TestPrintSummary:
    """_print_summary 函数的测试类"""

    def test_all_success(self, capsys):
        """测试全部成功"""
        _print_summary(5, [])
        captured = capsys.readouterr()
        assert "成功 5/5" in captured.out

    def test_some_failed(self, capsys):
        """测试部分失败"""
        _print_summary(5, ["file1.pdf", "file2.pdf"])
        captured = capsys.readouterr()
        assert "成功 3/5" in captured.out
        assert "失败 (2)" in captured.out


class TestMain:
    """main 函数的测试类"""

    @patch('pdfgj.cli.parse_args')
    @patch('pdfgj.cli.set_force_overwrite')
    @patch('pdfgj.cli.set_allow_kill_office')
    def test_main_no_args(self, mock_set_kill, mock_set_force, mock_parse, capsys):
        """测试无参数调用"""
        from pdfgj.cli import main

        mock_parse.return_value = MagicMock(
            merge=False, image=False, word=False, excel=False, ppt=False,
            recursive=False, yes=False, kill_office=False,
            output='merged.pdf', sortby='name', slides=None
        )

        with patch('pdfgj.cli.merge_pdfs') as mock_merge:
            mock_merge.return_value = True
            main()
            mock_merge.assert_called_once()

    @patch('pdfgj.cli.parse_args')
    @patch('pdfgj.cli.set_force_overwrite')
    @patch('pdfgj.cli.set_allow_kill_office')
    def test_main_image_mode_no_files(self, mock_set_kill, mock_set_force, mock_parse, capsys):
        """测试图片模式无文件"""
        from pdfgj.cli import main

        mock_parse.return_value = MagicMock(
            merge=False, image=True, word=False, excel=False, ppt=False,
            recursive=False, yes=False, kill_office=False,
            output='merged.pdf', sortby='name', slides=None
        )

        with patch('pdfgj.cli._get_files') as mock_get_files:
            mock_get_files.return_value = []
            main()
            captured = capsys.readouterr()
            assert "未找到图片文件" in captured.out

    @patch('pdfgj.cli.parse_args')
    @patch('pdfgj.cli.set_force_overwrite')
    @patch('pdfgj.cli.set_allow_kill_office')
    def test_main_image_mode_with_files(self, mock_set_kill, mock_set_force, mock_parse, capsys):
        """测试图片模式有文件"""
        from pdfgj.cli import main

        mock_parse.return_value = MagicMock(
            merge=False, image=True, word=False, excel=False, ppt=False,
            recursive=False, yes=False, kill_office=False,
            output='merged.pdf', sortby='name', slides=None
        )

        with patch('pdfgj.cli._get_files') as mock_get_files, \
             patch('pdfgj.cli.image_to_pdf') as mock_convert, \
             patch('pdfgj.cli._progress_bar'):
            mock_get_files.return_value = [Path("test.jpg")]
            mock_convert.return_value = True
            main()
            captured = capsys.readouterr()
            assert "完成" in captured.out

    @patch('pdfgj.cli.parse_args')
    @patch('pdfgj.cli.set_force_overwrite')
    @patch('pdfgj.cli.set_allow_kill_office')
    def test_main_image_mode_convert_fail(self, mock_set_kill, mock_set_force, mock_parse, capsys):
        """测试图片模式转换失败"""
        from pdfgj.cli import main

        mock_parse.return_value = MagicMock(
            merge=False, image=True, word=False, excel=False, ppt=False,
            recursive=False, yes=False, kill_office=False,
            output='merged.pdf', sortby='name', slides=None
        )

        with patch('pdfgj.cli._get_files') as mock_get_files, \
             patch('pdfgj.cli.image_to_pdf') as mock_convert, \
             patch('pdfgj.cli._progress_bar'):
            mock_get_files.return_value = [Path("test.jpg")]
            mock_convert.return_value = False
            main()
            captured = capsys.readouterr()
            assert "失败" in captured.out

    @patch('pdfgj.cli.parse_args')
    @patch('pdfgj.cli.set_force_overwrite')
    @patch('pdfgj.cli.set_allow_kill_office')
    def test_main_word_mode_no_files(self, mock_set_kill, mock_set_force, mock_parse, capsys):
        """测试Word模式无文件"""
        from pdfgj.cli import main

        mock_parse.return_value = MagicMock(
            merge=False, image=False, word=True, excel=False, ppt=False,
            recursive=False, yes=False, kill_office=False,
            output='merged.pdf', sortby='name', slides=None
        )

        with patch('pdfgj.cli._get_files') as mock_get_files:
            mock_get_files.return_value = []
            main()
            captured = capsys.readouterr()
            assert "未找到 Word 文档" in captured.out

    @patch('pdfgj.cli.parse_args')
    @patch('pdfgj.cli.set_force_overwrite')
    @patch('pdfgj.cli.set_allow_kill_office')
    def test_main_word_mode_with_files(self, mock_set_kill, mock_set_force, mock_parse, capsys):
        """测试Word模式有文件"""
        from pdfgj.cli import main

        mock_parse.return_value = MagicMock(
            merge=False, image=False, word=True, excel=False, ppt=False,
            recursive=False, yes=False, kill_office=False,
            output='merged.pdf', sortby='name', slides=None
        )

        with patch('pdfgj.cli._get_files') as mock_get_files, \
             patch('pdfgj.cli._batch_convert') as mock_convert:
            mock_get_files.return_value = [Path("test.docx")]
            mock_convert.return_value = []
            main()
            captured = capsys.readouterr()
            assert "完成" in captured.out

    @patch('pdfgj.cli.parse_args')
    @patch('pdfgj.cli.set_force_overwrite')
    @patch('pdfgj.cli.set_allow_kill_office')
    def test_main_excel_mode_no_files(self, mock_set_kill, mock_set_force, mock_parse, capsys):
        """测试Excel模式无文件"""
        from pdfgj.cli import main

        mock_parse.return_value = MagicMock(
            merge=False, image=False, word=False, excel=True, ppt=False,
            recursive=False, yes=False, kill_office=False,
            output='merged.pdf', sortby='name', slides=None
        )

        with patch('pdfgj.cli._get_files') as mock_get_files:
            mock_get_files.return_value = []
            main()
            captured = capsys.readouterr()
            assert "未找到 Excel 表格" in captured.out

    @patch('pdfgj.cli.parse_args')
    @patch('pdfgj.cli.set_force_overwrite')
    @patch('pdfgj.cli.set_allow_kill_office')
    def test_main_excel_mode_with_files(self, mock_set_kill, mock_set_force, mock_parse, capsys):
        """测试Excel模式有文件"""
        from pdfgj.cli import main

        mock_parse.return_value = MagicMock(
            merge=False, image=False, word=False, excel=True, ppt=False,
            recursive=False, yes=False, kill_office=False,
            output='merged.pdf', sortby='name', slides=None
        )

        with patch('pdfgj.cli._get_files') as mock_get_files, \
             patch('pdfgj.cli._batch_convert') as mock_convert:
            mock_get_files.return_value = [Path("test.xlsx")]
            mock_convert.return_value = []
            main()
            captured = capsys.readouterr()
            assert "完成" in captured.out

    @patch('pdfgj.cli.parse_args')
    @patch('pdfgj.cli.set_force_overwrite')
    @patch('pdfgj.cli.set_allow_kill_office')
    def test_main_ppt_mode_no_files(self, mock_set_kill, mock_set_force, mock_parse, capsys):
        """测试PPT模式无文件"""
        from pdfgj.cli import main

        mock_parse.return_value = MagicMock(
            merge=False, image=False, word=False, excel=False, ppt=True,
            recursive=False, yes=False, kill_office=False,
            output='merged.pdf', sortby='name', slides=None
        )

        with patch('pdfgj.cli._get_files') as mock_get_files:
            mock_get_files.return_value = []
            main()
            captured = capsys.readouterr()
            assert "未找到 PowerPoint 演示文稿" in captured.out

    @patch('pdfgj.cli.parse_args')
    @patch('pdfgj.cli.set_force_overwrite')
    @patch('pdfgj.cli.set_allow_kill_office')
    def test_main_ppt_mode_with_files(self, mock_set_kill, mock_set_force, mock_parse, capsys):
        """测试PPT模式有文件"""
        from pdfgj.cli import main

        mock_parse.return_value = MagicMock(
            merge=False, image=False, word=False, excel=False, ppt=True,
            recursive=False, yes=False, kill_office=False,
            output='merged.pdf', sortby='name', slides=None
        )

        with patch('pdfgj.cli._get_files') as mock_get_files, \
             patch('pdfgj.cli._batch_convert') as mock_convert:
            mock_get_files.return_value = [Path("test.pptx")]
            mock_convert.return_value = []
            main()
            captured = capsys.readouterr()
            assert "完成" in captured.out

    @patch('pdfgj.cli.parse_args')
    @patch('pdfgj.cli.set_force_overwrite')
    @patch('pdfgj.cli.set_allow_kill_office')
    def test_main_merge_mode(self, mock_set_kill, mock_set_force, mock_parse, capsys):
        """测试显式合并模式"""
        from pdfgj.cli import main

        mock_parse.return_value = MagicMock(
            merge=True, image=False, word=False, excel=False, ppt=False,
            recursive=False, yes=False, kill_office=False,
            output='merged.pdf', sortby='name', slides=None
        )

        with patch('pdfgj.cli.merge_pdfs') as mock_merge:
            mock_merge.return_value = True
            main()
            mock_merge.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
